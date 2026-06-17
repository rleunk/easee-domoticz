# -*- coding: utf-8 -*-

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
        return plugin.login()
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
    return plugin.login()

def api_get(plugin, path, retry=True):
    r = plugin.session.get(BASE_URL + path, headers={'Authorization': f'Bearer {plugin.access_token}'}, timeout=20)
    if r.status_code == 401 and retry:
        if plugin.refresh():
            return plugin.api_get(path, False)
    r.raise_for_status()
    return r.json() if r.text else None

def api_get_optional(plugin, path):
    try:
        return plugin.api_get(path)
    except Exception as e:
        easee_logging.debug('easee_api', f'GET {path} optioneel mislukt: {e}', 'api')
        return None
