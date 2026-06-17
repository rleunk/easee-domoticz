# -*- coding: utf-8 -*-

import Domoticz
from easee_constants import BASE_URL, LOGIN_URL, REFRESH_URL

def login(plugin):
    try:
        r = plugin.session.post(LOGIN_URL, json={'userName': Parameters.get('Username',''), 'password': Parameters.get('Password','')}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            plugin.access_token = data.get('accessToken','')
            plugin.refresh_token = data.get('refreshToken','')
            return bool(plugin.access_token)
        plugin.error(f'Login mislukt, HTTP {r.status_code}: {r.text[:300]}')
    except Exception as e:
        plugin.error(f'Login exception: {e}')
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
            return bool(plugin.access_token)
    except Exception:
        pass
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
        plugin.debug(f'GET {path} optioneel mislukt: {e}')
        return None
