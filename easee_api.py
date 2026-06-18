# -*- coding: utf-8 -*-

import time

import domoticz_runtime
from easee_constants import BASE_URL, LOGIN_URL, REFRESH_URL
import easee_logging


def _parse_retry_after(header_val):
    if header_val is None or header_val == 'onbekend':
        return 90
    try:
        return max(30, int(header_val))
    except (TypeError, ValueError):
        return 90


def mark_rate_limited(plugin, retry_after_header=None):
    secs = _parse_retry_after(retry_after_header)
    until = time.time() + secs
    prev = getattr(plugin, 'rate_limited_until', 0)
    plugin.rate_limited_until = max(prev, until)
    if '/sessions/ongoing' in str(getattr(plugin, '_last_api_path', '')):
        plugin.ongoing_skip_until = max(getattr(plugin, 'ongoing_skip_until', 0), until)


def is_rate_limited(plugin):
    return time.time() < getattr(plugin, 'rate_limited_until', 0)


def should_skip_ongoing(plugin):
    return is_rate_limited(plugin) or time.time() < getattr(plugin, 'ongoing_skip_until', 0)


def _is_priority_path(path):
    return '/equalizers/' in path and path.endswith('/state')


def login(plugin):
    try:
        r = plugin.session.post(LOGIN_URL, json={'userName': domoticz_runtime.Parameters.get('Username',''), 'password': domoticz_runtime.Parameters.get('Password','')}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            plugin.access_token = data.get('accessToken','')
            plugin.refresh_token = data.get('refreshToken','')
            if plugin.access_token:
                easee_logging.info('easee_api', 'Login geslaagd', 'login')
                return True
            easee_logging.error('easee_api', 'Login mislukt: geen access token in response', 'login')
            return False
        easee_logging.error('easee_api', f'Login mislukt, HTTP {r.status_code}: {r.text[:300]}', 'login')
    except Exception as e:
        easee_logging.error('easee_api', f'Login exception: {e}', 'login')
    return False

def refresh(plugin):
    if not plugin.access_token or not plugin.refresh_token:
        return login(plugin)
    try:
        r = plugin.session.post(REFRESH_URL, json={'accessToken': plugin.access_token, 'refreshToken': plugin.refresh_token}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            plugin.access_token = data.get('accessToken','')
            plugin.refresh_token = data.get('refreshToken','')
            if plugin.access_token:
                easee_logging.debug('easee_api', 'Token refresh geslaagd', 'login')
                return True
    except Exception as e:
        easee_logging.debug('easee_api', f'Token refresh mislukt, opnieuw inloggen: {e}', 'login')
    return login(plugin)

def api_get(plugin, path, retry=True):
    plugin._last_api_path = path
    plugin._last_http_status = None
    started = time.time()
    r = plugin.session.get(BASE_URL + path, headers={'Authorization': f'Bearer {plugin.access_token}'}, timeout=20)
    plugin._last_http_status = r.status_code
    elapsed = time.time() - started
    if elapsed > 5:
        easee_logging.warning('easee_api', f'GET {path} duurde {elapsed:.1f}s', 'api')
    if r.status_code == 401 and retry:
        if refresh(plugin):
            return api_get(plugin, path, False)
    if r.status_code == 429:
        retry_after = r.headers.get('Retry-After', 'onbekend')
        mark_rate_limited(plugin, retry_after)
        easee_logging.warning(
            'easee_api',
            f'GET {path} rate limit (429), Retry-After={retry_after} — overslaan tot volgende poll',
            'api',
        )
        return None
    r.raise_for_status()
    return r.json() if r.text else None

def api_get_optional(plugin, path, skip_if_rate_limited=True):
    if skip_if_rate_limited and is_rate_limited(plugin) and not _is_priority_path(path):
        easee_logging.debug(
            'easee_api',
            f'GET {path} overgeslagen (rate limit actief tot {int(plugin.rate_limited_until - time.time())}s)',
            'api',
        )
        return None
    try:
        data = api_get(plugin, path)
        status = getattr(plugin, '_last_http_status', None)
        if data is None:
            if status == 429:
                easee_logging.warning(
                    'easee_api',
                    f'GET {path} optioneel: rate limit (429) — geen data',
                    'api',
                )
            elif status:
                easee_logging.warning(
                    'easee_api',
                    f'GET {path} optioneel: HTTP {status} — geen data',
                    'api',
                )
            else:
                easee_logging.warning(
                    'easee_api',
                    f'GET {path} optioneel: geen response',
                    'api',
                )
        return data
    except Exception as e:
        status = getattr(plugin, '_last_http_status', None)
        if status:
            easee_logging.warning('easee_api', f'GET {path} optioneel mislukt (HTTP {status}): {e}', 'api')
        else:
            easee_logging.warning('easee_api', f'GET {path} optioneel mislukt: {e}', 'api')
        return None

def last_request_was_rate_limited(plugin):
    return getattr(plugin, '_last_http_status', None) == 429
