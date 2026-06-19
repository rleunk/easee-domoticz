# -*- coding: utf-8 -*-

import time

import domoticz_runtime
from easee_constants import BASE_URL, DEVICE_STATE_URL, LOGIN_URL, REFRESH_URL
import easee_logging


def _parse_retry_after(header_val):
    if header_val is None or header_val == 'onbekend':
        return 90
    try:
        return max(30, int(header_val))
    except (TypeError, ValueError):
        return 90


def _rate_limit_category(path):
    path = str(path or '')
    if '/chargers/' in path or '/sessions/' in path:
        return 'charger'
    if path.startswith('/state/') or '/equalizers/' in path:
        return 'equalizer'
    return 'general'


def _category_until_attr(category):
    if category == 'charger':
        return 'charger_rate_limited_until'
    if category == 'equalizer':
        return 'equalizer_rate_limited_until'
    return 'general_rate_limited_until'


def _category_until(plugin, category):
    return getattr(plugin, _category_until_attr(category), 0)


def _set_category_until(plugin, category, until):
    attr = _category_until_attr(category)
    prev = getattr(plugin, attr, 0)
    setattr(plugin, attr, max(prev, until))


def mark_rate_limited(plugin, retry_after_header=None):
    path = str(getattr(plugin, '_last_api_path', ''))
    secs = _parse_retry_after(retry_after_header)
    until = time.time() + secs
    category = _rate_limit_category(path)
    _set_category_until(plugin, category, until)
    if category == 'charger' and '/sessions/ongoing' in path:
        plugin.ongoing_skip_until = max(getattr(plugin, 'ongoing_skip_until', 0), until)
    easee_logging.debug(
        'easee_api',
        f'Rate limit ({category}) tot +{secs}s na GET {path}',
        'api',
    )


def is_charger_rate_limited(plugin):
    return time.time() < _category_until(plugin, 'charger')


def is_equalizer_rate_limited(plugin):
    return time.time() < _category_until(plugin, 'equalizer')


def is_general_rate_limited(plugin):
    return time.time() < _category_until(plugin, 'general')


def is_rate_limited(plugin):
    """True when any API category is rate-limited (legacy helper)."""
    return (
        is_charger_rate_limited(plugin)
        or is_equalizer_rate_limited(plugin)
        or is_general_rate_limited(plugin)
    )


def should_skip_ongoing(plugin):
    return is_charger_rate_limited(plugin) or time.time() < getattr(plugin, 'ongoing_skip_until', 0)


def _is_priority_path(path):
    return '/equalizers/' in path and path.endswith('/state')


def _is_expected_optional_failure(path, status):
    """HTTP 403/405 on optional probes that are often account-restricted — DEBUG only."""
    if status is None:
        return False
    path = str(path or '')
    try:
        code = int(status)
    except (TypeError, ValueError):
        return False
    if code == 403:
        if path == '/equalizers' or path.rstrip('/') == '/equalizers':
            return True
        if path.startswith('/equalizers/'):
            return True
        if '/cloud-loadbalancing/' in path or 'loadbalancing' in path:
            return True
    if code == 405 and '/sites/' in path and '/circuits' in path:
        return True
    return False


def _log_optional_api_issue(path, status, message):
    if status == 429 or not _is_expected_optional_failure(path, status):
        easee_logging.warning('easee_api', message, 'api')
    else:
        easee_logging.debug('easee_api', message, 'api')


def _is_rate_limited_for_path(plugin, path):
    if _is_priority_path(path):
        return False
    category = _rate_limit_category(path)
    return time.time() < _category_until(plugin, category)


def _request_base_url(path):
    """Route observations to https://api.easee.com/state/… (not /api/state/…)."""
    if path.startswith('/state/'):
        return DEVICE_STATE_URL
    return BASE_URL


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
    r = plugin.session.get(
        _request_base_url(path) + path,
        headers={'Authorization': f'Bearer {plugin.access_token}'},
        timeout=20,
    )
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
            f'GET {path} rate limit (429, {_rate_limit_category(path)}), Retry-After={retry_after} — overslaan tot volgende poll',
            'api',
        )
        return None
    r.raise_for_status()
    return r.json() if r.text else None

def api_get_optional(plugin, path, skip_if_rate_limited=True):
    if skip_if_rate_limited and _is_rate_limited_for_path(plugin, path):
        category = _rate_limit_category(path)
        remaining = int(_category_until(plugin, category) - time.time())
        easee_logging.debug(
            'easee_api',
            f'GET {path} overgeslagen ({category} rate limit actief, nog ~{max(0, remaining)}s)',
            'api',
        )
        return None
    try:
        data = api_get(plugin, path)
        status = getattr(plugin, '_last_http_status', None)
        if data is None:
            if status == 429:
                _log_optional_api_issue(
                    path,
                    status,
                    f'GET {path} optioneel: rate limit (429, {_rate_limit_category(path)}) — geen data',
                )
            elif status:
                _log_optional_api_issue(path, status, f'GET {path} optioneel: HTTP {status} — geen data')
            else:
                easee_logging.warning('easee_api', f'GET {path} optioneel: geen response', 'api')
        return data
    except Exception as e:
        status = getattr(plugin, '_last_http_status', None)
        if status:
            _log_optional_api_issue(path, status, f'GET {path} optioneel mislukt (HTTP {status}): {e}')
        else:
            easee_logging.warning('easee_api', f'GET {path} optioneel mislukt: {e}', 'api')
        return None

def last_request_was_rate_limited(plugin):
    return getattr(plugin, '_last_http_status', None) == 429

def last_request_status(plugin):
    return getattr(plugin, '_last_http_status', None)
