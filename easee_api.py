# -*- coding: utf-8 -*-

import time

import domoticz_runtime
from easee_constants import BASE_URL, LOGIN_URL, REFRESH_URL
import easee_logging

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
    started = time.time()
    r = plugin.session.get(BASE_URL + path, headers={'Authorization': f'Bearer {plugin.access_token}'}, timeout=20)
    elapsed = time.time() - started
    if elapsed > 5:
        easee_logging.warning('easee_api', f'GET {path} duurde {elapsed:.1f}s', 'api')
    if r.status_code == 401 and retry:
        if refresh(plugin):
            return api_get(plugin, path, False)
    r.raise_for_status()
    return r.json() if r.text else None

def api_get_optional(plugin, path):
    try:
        return api_get(plugin, path)
    except Exception as e:
        easee_logging.debug('easee_api', f'GET {path} optioneel mislukt: {e}', 'api')
        return None
