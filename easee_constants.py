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
PLUGIN_VERSION = '0.6.1'
MANUAL_RATE_DEFAULT = 0.25
MANUAL_DAL_RATE_DEFAULT = 0.22
MANUAL_NORMAL_RATE_DEFAULT = 0.28
MANUAL_PIEK_RATE_DEFAULT = 0.35
MANUAL_DAL_START_HOUR_DEFAULT = 23
MANUAL_DAL_END_HOUR_DEFAULT = 7
MANUAL_PIEK_START_HOUR_DEFAULT = 17
MANUAL_PIEK_END_HOUR_DEFAULT = 21
MANUAL_TARIFF_STATE_KEY = 'manual_tariff_backup'
API_TIMEOUT = 30
TIBBER_TOKEN_STATE_KEY = 'tibber_token_backup'
ENTSOE_TOKEN_STATE_KEY = 'entsoe_token_backup'
ENTSOE_API_URL = 'https://web-api.tp.entsoe.eu/api'
ENTSOE_NL_DOMAIN = '10YNL----------L'
ENTSOE_DOC_TYPE = 'A44'
ENTSOE_OPSLAG_DEFAULT = 0.0
ENTSOE_ENERGIEBELASTING_DEFAULT = 0.0
ENTSOE_BTW_PCT_DEFAULT = 21.0
ENERGYZERO_API_URL = 'https://api.energyzero.nl/v1/energyprices'
BESTE_LADEN_HOURS_STATE_KEY = 'beste_laden_hours'
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
    'Dag overzicht': 'EASEE_CORE_DAG_OVERZ',
    'Kosten & Samenvatting': 'EASEE_CORE_COSTS',
    'Beste laden': 'EASEE_CORE_BEST',
    'Dagrapport': 'EASEE_CORE_DAG',
}

# Tiles merged in v10.11 — no longer created or updated (marked Used=0 if present).
DEPRECATED_CORE_LABELS = ('Kosten & Samenvatting', 'Dagrapport')
DEPRECATED_CHARGER_LABELS = ('Totaal & Sessie', 'Kosten (Sessie/Dag)')