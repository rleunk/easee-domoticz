# -*- coding: utf-8 -*-

API_HOST = 'https://api.easee.com'
BASE_URL = API_HOST + '/api'
# Observations live at /state/{id}/observations (no /api prefix) — see Easee Get Observations API
DEVICE_STATE_URL = API_HOST
LOGIN_URL = BASE_URL + '/accounts/login'
REFRESH_URL = BASE_URL + '/accounts/refresh_token'
TIBBER_GQL = 'https://api.tibber.com/v1-beta/gql'
STATE_FILE = 'easee_state.json'
LEGACY_STATE_FILE = 'easee_v9_0_state.json'
PLUGIN_VERSION = '10.9.28'
PLUGIN_KEY = 'EaseeCloudAutoDiscoveryV1000'
ULTRA_DEBUG = False

OP_MODE_LABELS = {
    0: 'Offline',
    1: 'Geen auto',
    2: 'Wacht op start',
    3: 'Laden',
    4: 'Voltooid',
    5: 'Fout',
    6: 'Klaar om te laden',
    7: 'Wacht op autorisatie',
    8: 'Bezig met afmelden',
}

DEVICE_TYPES = {
    'Text':      {'Type': 243, 'Subtype': 19},
    'Switch':    {'Type': 244, 'Subtype': 73, 'Switchtype': 0},
    'Energy':    {'Type': 243, 'Subtype': 29},
    'CustomkWh': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;kWh'}},
    'CustomEUR': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;â‚¬'}},
}

CORE_DEVICE_IDS = {
    'Status': 'EASEE_CORE_STATUS',
    'Totaal Laden': 'EASEE_CORE_ENERGY',
    'Totaal kWh': 'EASEE_CORE_KWH',
    'LoadBal': 'EASEE_CORE_LOADBAL',
    'Kosten & Samenvatting': 'EASEE_CORE_COSTS',
    'Beste laden': 'EASEE_CORE_BEST',
}