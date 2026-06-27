# -*- coding: utf-8 -*-
"""Read optional P1 / solar / Sessy Domoticz devices for context hints (no control)."""

import domoticz_runtime
import easee_helpers
import easee_logging
from easee_constants import DEVICE_TYPES

P1_DEFAULT_NAME = 'Power'
SOLAR_DEFAULT_NAME = 'Zonnepanelen'
SESSY_DEFAULT_NAME = 'Sessy'
EXPORT_THRESHOLD_W = 100
SESSY_THRESHOLD_W = 100
HIGH_IMPORT_THRESHOLD_W = 3000

_DEVICE_NOT_FOUND = set()


def configured_device_names(plugin):
    sessy_raw = (domoticz_runtime.Parameters.get('Mode23', '') or '').strip()
    return {
        'p1': _param_name('Mode21', P1_DEFAULT_NAME),
        'solar': _param_name('Mode22', SOLAR_DEFAULT_NAME),
        'sessy': sessy_raw or '(uit)',
    }


def energy_hints_enabled(plugin):
    """Mode20: default aan."""
    raw = (domoticz_runtime.Parameters.get('Mode20', '') or '').strip().lower()
    if raw in ('uit', '0', 'false', 'no', 'off'):
        return False
    return True


def _param_name(key, default):
    raw = (domoticz_runtime.Parameters.get(key, '') or '').strip()
    return raw or default


def _parse_power_part(value):
    try:
        return int(round(float(str(value).replace(',', '.'))))
    except Exception:
        return 0


def _parse_energy_svalue(svalue):
    """First semicolon field = instant power (W)."""
    parts = str(svalue or '').split(';')
    if not parts:
        return 0
    return _parse_power_part(parts[0])


def _parse_p1_svalue(svalue):
    """P1: importW;importWh;exportW;exportWh (or shorter energy layouts)."""
    parts = [p.strip() for p in str(svalue or '').split(';') if p.strip() != '']
    if len(parts) >= 4:
        return _parse_power_part(parts[0]), _parse_power_part(parts[2])
    if len(parts) >= 2:
        p0 = _parse_power_part(parts[0])
        p1 = _parse_power_part(parts[1])
        if p0 < 0:
            return 0, abs(p0)
        return p0, max(0, p1)
    if len(parts) == 1:
        p0 = _parse_power_part(parts[0])
        if p0 < 0:
            return 0, abs(p0)
        return max(0, p0), 0
    return 0, 0


def _device_subtype(unit):
    try:
        return int(domoticz_runtime.Devices[unit].SubType)
    except Exception:
        return None


def _name_matches(plugin, dev_name, query):
    dn = easee_helpers.norm(plugin, dev_name).lower()
    q = easee_helpers.norm(plugin, query).lower()
    if not q:
        return False
    return dn == q or q in dn


def _is_easee_device(dev):
    devid = str(getattr(dev, 'DeviceID', '') or '')
    name = str(getattr(dev, 'Name', '') or '').lower()
    return devid.startswith('EASEE_') or 'easee' in name


def _resolve_device(plugin, name_or_idx, role):
    """Resolve by numeric idx or name; skip Easee plugin devices."""
    raw = (name_or_idx or '').strip()
    if not raw:
        return None, None

    if raw.isdigit():
        idx = int(raw)
        dev = domoticz_runtime.Devices.get(idx)
        if dev is not None and not _is_easee_device(dev):
            return idx, dev
        key = f'idx:{idx}:{role}'
        if key not in _DEVICE_NOT_FOUND:
            _DEVICE_NOT_FOUND.add(key)
            easee_logging.debug(
                'domoticz_energy_hints',
                f'{role}: idx {idx} niet gevonden of is Easee-tegel — hint overgeslagen',
            )
        return None, None

    matches = []
    for unit, dev in domoticz_runtime.Devices.items():
        if _is_easee_device(dev):
            continue
        if _name_matches(plugin, dev.Name, raw):
            matches.append((unit, dev))

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches[0]

    key = f'name:{raw}:{role}'
    if key not in _DEVICE_NOT_FOUND:
        _DEVICE_NOT_FOUND.add(key)
        easee_logging.debug(
            'domoticz_energy_hints',
            f'{role}: apparaat "{raw}" niet gevonden — hint overgeslagen',
        )
    return None, None


def _find_p1_fallback(plugin):
    """Default search: Energy/P1-like device named Power."""
    energy_subtype = DEVICE_TYPES['Energy']['Subtype']
    candidates = []
    for unit, dev in domoticz_runtime.Devices.items():
        if _is_easee_device(dev):
            continue
        if _device_subtype(unit) != energy_subtype:
            continue
        name = easee_helpers.norm(plugin, dev.Name).lower()
        if 'power' in name or 'p1' in name or 'smart meter' in name:
            candidates.append((unit, dev))
    if len(candidates) == 1:
        return candidates[0]
    for unit, dev in candidates:
        if easee_helpers.norm(plugin, dev.Name).lower() == 'power':
            return unit, dev
    return None, None


def read_energy_context(plugin):
    """Read P1 / solar / Sessy watts from Domoticz Devices (cached per poll)."""
    cache_key = '_energy_hint_context'
    cached = getattr(plugin, cache_key, None)
    if cached is not None:
        return cached

    ctx = {
        'import_w': 0,
        'export_w': 0,
        'solar_w': 0,
        'sessy_w': 0,
        'p1_ok': False,
        'solar_ok': False,
        'sessy_ok': False,
    }
    if not energy_hints_enabled(plugin):
        setattr(plugin, cache_key, ctx)
        return ctx

    p1_name = _param_name('Mode21', P1_DEFAULT_NAME)
    unit, dev = _resolve_device(plugin, p1_name, 'P1')
    if dev is None and p1_name.lower() == P1_DEFAULT_NAME.lower():
        unit, dev = _find_p1_fallback(plugin)
    if dev is not None:
        imp, exp = _parse_p1_svalue(getattr(dev, 'sValue', ''))
        ctx['import_w'] = max(0, imp)
        ctx['export_w'] = max(0, exp)
        ctx['p1_ok'] = True

    solar_name = _param_name('Mode22', SOLAR_DEFAULT_NAME)
    unit, dev = _resolve_device(plugin, solar_name, 'Zonnepanelen')
    if dev is not None:
        solar_w = _parse_energy_svalue(getattr(dev, 'sValue', ''))
        ctx['solar_w'] = max(0, solar_w)
        ctx['solar_ok'] = True

    sessy_raw = (domoticz_runtime.Parameters.get('Mode23', '') or '').strip()
    if sessy_raw:
        unit, dev = _resolve_device(plugin, sessy_raw, 'Sessy')
        if dev is not None:
            ctx['sessy_w'] = _parse_energy_svalue(getattr(dev, 'sValue', ''))
            ctx['sessy_ok'] = True

    setattr(plugin, cache_key, ctx)
    return ctx


def clear_energy_context_cache(plugin):
    if hasattr(plugin, '_energy_hint_context'):
        delattr(plugin, '_energy_hint_context')


def _eq_export_active(plugin):
    for data in (getattr(plugin, 'latest_equalizers', None) or {}).values():
        export_w = easee_helpers.safe_int(plugin, data.get('export'), 0)
        if export_w > EXPORT_THRESHOLD_W:
            return True
    return False


def _collect_hints(plugin, ctx, charging=False):
    hints = []
    import_w = ctx.get('import_w', 0)
    export_w = ctx.get('export_w', 0)
    solar_w = ctx.get('solar_w', 0)
    sessy_w = ctx.get('sessy_w', 0)

    solar_surplus = (
        (ctx.get('solar_ok') and solar_w > EXPORT_THRESHOLD_W and solar_w > import_w)
        or (ctx.get('p1_ok') and export_w > EXPORT_THRESHOLD_W)
    )
    if solar_surplus:
        hints.append('☀️ Zonne-overschot')
    elif ctx.get('p1_ok') and export_w > 0 and not _eq_export_active(plugin):
        hints.append('↩️ Teruglevering')

    if ctx.get('sessy_ok') and abs(sessy_w) > SESSY_THRESHOLD_W:
        hints.append('🔋 Sessy actief')

    if charging and ctx.get('p1_ok') and import_w >= HIGH_IMPORT_THRESHOLD_W:
        hints.append('📥 Hoog netverbruik')

    return hints


def global_hints_text(plugin, any_charging=False):
    if not energy_hints_enabled(plugin):
        return ''
    ctx = read_energy_context(plugin)
    hints = _collect_hints(plugin, ctx, charging=any_charging)
    return ' · '.join(hints)


def charging_context_hint(plugin, power_w, session_active=False):
    """Extra hints on charger Status while charging (Tibber hint is separate)."""
    if not energy_hints_enabled(plugin) or not session_active or power_w <= 50:
        return ''
    ctx = read_energy_context(plugin)
    hints = _collect_hints(plugin, ctx, charging=True)
    return ' · '.join(hints)
