# -*- coding: utf-8 -*-
"""Centralized Easee / Tibber API field names and observation IDs."""

# ---- Fuse & eMobility (single source of truth) ----

FUSE_KEYS = {
    'limit': (
        'fuse', 'mainFuseLimit', 'fuseLimit', 'mainFuseCurrentLimit',
        'mainFuseLimitCurrent', 'maxFuse', 'maxFuseCurrent', 'fuseCurrent',
        'mainFuseLimitAmps', 'mainFuseCurrentLimitAmps',
        'mainCurrentLimit', 'currentLimit', 'importLimit', 'mainImportLimit',
        'householdCurrentLimit', 'gridCurrentLimit', 'maxImportCurrent',
        'maxMainCurrent', 'panelCurrentLimit', 'siteCurrentLimit',
    ),
    'main': ('ratedCurrent', 'mainFuseSize', 'mainFuse'),
    'emobility': ('maxAllocatedCurrent', 'maxCurrent', 'eMobilityLimit', 'emobilityLimit'),
    'emobility_fallback': ('maxCurrent', 'eMobilityLimit', 'emobilityLimit'),
    'emobility_primary': 'maxAllocatedCurrent',
    'allocated': ('allocatedCurrent',),
    'offline_circuit': (
        'offlineMaxCircuitCurrentP1', 'offlineMaxCircuitCurrentP2', 'offlineMaxCircuitCurrentP3',
    ),
    'fuse_raw': ('fuse',),
}

_FUSE_LIMIT_EXACT = {k.lower() for k in FUSE_KEYS['limit']}
_FUSE_EXCLUDED = {
    'ratedcurrent', 'mainfuse', 'mainfusesize', 'fusegroup', 'fuseid',
    'maxallocatedcurrent', 'allocatedcurrent', 'maxcurrent', 'emobilitylimit',
    'offlinemaxcircuitcurrentp1', 'offlinemaxcircuitcurrentp2', 'offlinemaxcircuitcurrentp3',
}
_EMOBILITY_EXACT = {k.lower() for k in FUSE_KEYS['emobility']} | {'emobilitycurrent'}

# ---- Site structure ----

SITE_STRUCTURE_KEYS = {
    'root': 'siteStructure',
    'max_continuous_current': 'maxContinuousCurrent',
    'rated_current': 'ratedCurrent',
    'circuits': 'circuits',
    'panels': 'panels',
    'source_max_continuous': 'siteStructure.maxContinuousCurrent',
    'nested_roots': ('site', 'panel', 'root', 'mainPanel', 'main', 'limits', 'loadBalancing', 'energy'),
    'nested_emobility': ('site', 'panel', 'limits', 'loadBalancing', 'energy'),
}

SITE_STRUCTURE_PATHS = {
    'max_continuous_current': SITE_STRUCTURE_KEYS['source_max_continuous'],
    'fuse': 'siteStructure.fuse',
}

# ---- Equalizer state & observations ----

EQUALIZER_KEYS = {
    'power': ('currentPower', 'power', 'activePowerImport', 'activePower'),
    'power_fallback': ('currentPower', 'power', 'activePower'),
    'load_balancing': ('loadBalancingActive', 'loadBalancing', 'isLoadBalancingEnabled'),
    'max_power_import': ('maxPowerImport',),
    'phase_current': ('currentL1', 'currentL2', 'currentL3'),
    'cumulative_import': ('cumulativeActivePowerImport',),
    'cumulative_export': ('cumulativeActivePowerExport',),
    'online': ('isOnline',),
    'site_id': ('siteId',),
    'allocated_current': ('allocatedCurrent',),
}

OBSERVATION_KEYS = {
    'container': ('observations', 'data'),
    'query_ids': '20,31,32,33,40,41,44,45,46',
}

OBSERVATION_ID_TO_FIELD = {
    20: SITE_STRUCTURE_KEYS['root'],
    31: 'currentL1',
    32: 'currentL2',
    33: 'currentL3',
    40: 'activePowerImport',
    41: 'activePowerExport',
    44: 'maxPowerImport',
    45: 'cumulativeActivePowerImport',
    46: 'cumulativeActivePowerExport',
}

# ---- Charger state & session ----

CHARGER_KEYS = {
    'id': ('id', 'chargerId', 'serialNumber'),
    'name': ('name', 'serialNumber', 'id'),
    'site': ('siteName', 'locationName', 'siteId'),
    'session_energy': ('sessionEnergy',),
    'power': ('totalPower',),
    'lifetime_energy': ('lifetimeEnergy',),
    'online': ('isOnline',),
    'op_mode': ('chargerOpMode',),
    'session_status': ('status', 'state'),
}

# ---- Site / state API paths (emobility source labels) ----

SITE_STATE_PATHS = {
    'site_state_mac': 'site.state.maxAllocatedCurrent',
    'site_state_emobility': 'site.state.emobility',
    'circuit_states_mac': 'circuitStates.maxAllocatedCurrent',
    'site_structure_mac': 'siteStructure.maxAllocatedCurrent',
    'site_detailed_mac': 'site.detailed.maxAllocatedCurrent',
    'site_detailed_emobility': 'site.detailed.emobility',
}

# ---- Tibber GraphQL response fields ----

TIBBER_KEYS = {
    'price': ('total', 'energy', 'tax'),
    'price_current': ('total', 'energy', 'tax', 'currency', 'startsAt'),
    'buckets': ('today', 'tomorrow'),
    'bucket_current': 'current',
    'starts_at': 'startsAt',
    'currency': 'currency',
}


def fuse_limit_key_tuple():
    return FUSE_KEYS['limit']


def emobility_key_tuple():
    return FUSE_KEYS['emobility']


def emobility_fallback_key_tuple():
    return FUSE_KEYS['emobility_fallback']


def main_fuse_key_tuple():
    return FUSE_KEYS['main']


def offline_circuit_key_tuple():
    return FUSE_KEYS['offline_circuit']


def is_fuse_limit_key_name(key):
    if not isinstance(key, str):
        return False
    kl = key.lower()
    if kl in _FUSE_EXCLUDED:
        return False
    if kl in _FUSE_LIMIT_EXACT:
        return True
    if 'fuselimit' in kl or 'fusecurrentlimit' in kl or 'mainfuselimit' in kl:
        return True
    if kl.endswith('fuse') or (kl.startswith('fuse') and 'rating' not in kl):
        return True
    if kl.endswith('limit') and any(x in kl for x in ('fuse', 'main', 'grid', 'import', 'household', 'panel', 'site')):
        return True
    return False


def is_emobility_key_name(key):
    if not isinstance(key, str):
        return False
    return key.lower() in _EMOBILITY_EXACT


def is_offline_circuit_current_key_name(key):
    if not isinstance(key, str):
        return False
    return key.lower() in {k.lower() for k in FUSE_KEYS['offline_circuit']}


# Backward-compatible flat aliases (for imports / iteration)
FUSE_LIMIT_KEYS = FUSE_KEYS['limit']
EMOBILITY_KEYS = FUSE_KEYS['emobility']
MAIN_FUSE_KEYS = FUSE_KEYS['main']
OFFLINE_CIRCUIT_CURRENT_KEYS = FUSE_KEYS['offline_circuit']


def first_dict_value(data, keys):
    """Return the first non-None value for any key in *keys*."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        if data.get(key) is not None:
            return data.get(key)
    return None


def first_power_value(values):
    """First non-empty equalizer power reading from *values*."""
    if not isinstance(values, dict):
        return None
    for key in EQUALIZER_KEYS['power']:
        val = values.get(key)
        if val is not None and val != '':
            return val
    return None
