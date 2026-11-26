# -*- coding: utf-8 -*-
"""Read optional P1 / solar / home battery Domoticz devices for context hints (no control)."""

import json
import re
import domoticz_runtime
import easee_helpers
import easee_i18n
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
        'thuisbatterij': sessy_raw or easee_i18n.t(plugin, 'disabled'),
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


_NON_POWER_UNITS = ('m3', 'm³', 'kwh', '°', 'celsius', '%', 'volt', 'amp', 'lux', 'ppm', 'hz', 'bar')


def parse_watt_label(text, allow_bare=False):
    """Watts from a Domoticz label such as '800 Watt' or '-1500 W'. None when the unit is not power."""
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    compact = raw.lower().replace(' ', '')
    looks_like_power = 'watt' in compact or compact.endswith('w')
    if any(unit in compact for unit in _NON_POWER_UNITS) and not looks_like_power:
        return None
    if not allow_bare and not looks_like_power and not re.fullmatch(r'-?\d+(?:[.,]\d+)?', raw):
        return None
    match = re.search(r'-?\d+(?:[.,]\d+)?', raw)
    if not match:
        return None
    return _parse_power_part(match.group(0))


def p1_watts_from_api(device):
    """Import and export watts from a Domoticz JSON device. None when the device has no power."""
    if not isinstance(device, dict):
        return None
    usage = device.get('Usage')
    delivered = device.get('UsageDeliv')
    if usage is None and delivered is None:
        data = parse_watt_label(device.get('Data'), allow_bare=True)
        if data is None:
            return None
        if data < 0:
            return 0, abs(data)
        return data, 0
    return max(0, parse_watt_label(usage, allow_bare=True) or 0), max(0, parse_watt_label(delivered, allow_bare=True) or 0)


def power_watts_from_api(device):
    """Signed watts. A negative Data value wins over an unsigned Usage field."""
    if not isinstance(device, dict):
        return None
    data = device.get('Data')
    if isinstance(data, str) and data.strip().startswith('-'):
        watts = parse_watt_label(data, allow_bare=True)
        if watts is not None:
            return watts
    usage = parse_watt_label(device.get('Usage'), allow_bare=True)
    if usage is not None:
        return usage
    return parse_watt_label(data, allow_bare=True)


def _api_is_easee(device):
    name = str(device.get('Name') or '').lower()
    device_id = str(device.get('DeviceID') or device.get('ID') or '')
    return 'easee' in name or device_id.upper().startswith('EASEE_')


def select_api_device(plugin, devices, query):
    """Pick one Domoticz device by Idx or name. Status is ok, missing, or ambiguous."""
    raw = (query or '').strip()
    if not raw or not devices:
        return None, 'missing'
    if raw.isdigit():
        for device in devices:
            if isinstance(device, dict) and str(device.get('idx', '')).strip() == raw:
                return device, 'ok'
        return None, 'missing'
    wanted = easee_helpers.norm(plugin, raw).lower()
    exact = []
    partial = []
    for device in devices:
        if not isinstance(device, dict) or _api_is_easee(device):
            continue
        name = easee_helpers.norm(plugin, device.get('Name') or '')
        if not name:
            continue
        lowered = name.lower()
        if lowered == wanted:
            exact.append(device)
        elif wanted in lowered:
            partial.append(device)
    if len(exact) == 1:
        return exact[0], 'ok'
    if len(exact) > 1:
        return None, 'ambiguous'
    if len(partial) == 1:
        return partial[0], 'ok'
    if len(partial) > 1:
        return None, 'ambiguous'
    return None, 'missing'


def api_bases_from_args(args):
    """HTTP bases from a Domoticz command line. Defaults to localhost port 8080."""
    http_port = None
    ssl_port = None
    items = list(args or [])
    index = 0
    while index < len(items):
        arg = items[index]
        if arg in ('-www', '--www') and index + 1 < len(items):
            http_port = items[index + 1]
            index += 2
            continue
        if arg in ('-sslwww', '--sslwww') and index + 1 < len(items):
            ssl_port = items[index + 1]
            index += 2
            continue
        index += 1
    bases = []
    if http_port and http_port != '0':
        bases.append(f'http://127.0.0.1:{http_port}')
    if ssl_port and ssl_port != '0':
        bases.append(f'https://127.0.0.1:{ssl_port}')
    if not bases:
        bases.append('http://127.0.0.1:8080')
    return bases


def _process_args():
    try:
        with open('/proc/self/cmdline', 'rb') as handle:
            raw = handle.read().split(b'\0')
        return [part.decode('utf-8', 'replace') for part in raw if part]
    except Exception:
        return []


def fetch_domoticz_devices(bases, get_json):
    """Return (devices, error). devices is None when every base failed."""
    last_error = 'geen antwoord'
    for base in bases or []:
        url = f'{str(base).rstrip("/")}/json.htm?type=devices&filter=all'
        try:
            payload = get_json(url)
        except Exception as exc:
            last_error = str(exc)
            continue
        if isinstance(payload, dict) and payload.get('status') == 'OK' and isinstance(payload.get('result'), list):
            return payload['result'], None
        last_error = 'onverwacht antwoord'
    return None, last_error


def _requests_get_json(url):
    import requests
    response = requests.get(
        url,
        timeout=4,
        verify=not str(url).startswith('https://'),
        headers={'Accept': 'application/json'},
    )
    if response.status_code != 200:
        raise RuntimeError(f'HTTP {response.status_code}')
    return response.json()


def _urllib_get_json(url):
    import ssl
    import urllib.request
    context = ssl._create_unverified_context() if str(url).startswith('https://') else None
    with urllib.request.urlopen(url, timeout=4, context=context) as response:
        return json.loads(response.read().decode('utf-8', 'replace'))


def _http_get_json(url):
    try:
        return _requests_get_json(url)
    except ImportError:
        return _urllib_get_json(url)


def _api_device_list(plugin):
    if getattr(plugin, '_energy_hint_api_tried', False):
        return getattr(plugin, '_energy_hint_api_devices', None)
    plugin._energy_hint_api_tried = True
    fetcher = getattr(plugin, '_domoticz_devices_fetcher', None)
    if fetcher is not None:
        devices, error = fetcher()
    else:
        devices, error = fetch_domoticz_devices(api_bases_from_args(_process_args()), _http_get_json)
    plugin._energy_hint_api_devices = devices
    if devices is None:
        easee_logging.debug(
            'domoticz_energy_hints',
            f'Domoticz-apparaatlijst niet gelezen ({error}) — hints alleen binnen dit hardware-item',
        )
    return devices


def _hint_from_api(plugin, query, role):
    """Return (state, device). state is unavailable, missing, ambiguous, or ok."""
    devices = _api_device_list(plugin)
    if devices is None:
        return 'unavailable', None
    device, status = select_api_device(plugin, devices, query)
    if status == 'ambiguous':
        key = f'ambiguous:{query}:{role}'
        if key not in _DEVICE_NOT_FOUND:
            _DEVICE_NOT_FOUND.add(key)
            easee_logging.debug(
                'domoticz_energy_hints',
                f'{role}: meerdere Domoticz-apparaten passen bij "{query}" — hint overgeslagen',
            )
        return 'ambiguous', None
    if status == 'ok':
        return 'ok', device
    return 'missing', None


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
    """Read P1 / solar / home battery watts from Domoticz Devices (cached per poll)."""
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
    p1_state, api_p1 = _hint_from_api(plugin, p1_name, 'P1')
    if p1_state == 'ok':
        parsed = p1_watts_from_api(api_p1)
        if parsed is None:
            easee_logging.debug(
                'domoticz_energy_hints',
                f'P1: {api_p1.get("Name")} (idx {api_p1.get("idx")}) heeft geen vermogen in watt',
            )
        else:
            ctx['import_w'] = max(0, parsed[0])
            ctx['export_w'] = max(0, parsed[1])
            ctx['p1_ok'] = True
            easee_logging.debug(
                'domoticz_energy_hints',
                f'P1: {api_p1.get("Name")} (idx {api_p1.get("idx")}), import {ctx["import_w"]} W, export {ctx["export_w"]} W',
            )
    elif p1_state in ('unavailable', 'missing'):
        unit, dev = _resolve_device(plugin, p1_name, 'P1')
        if dev is None and p1_name.lower() == P1_DEFAULT_NAME.lower():
            unit, dev = _find_p1_fallback(plugin)
        if dev is not None:
            imp, exp = _parse_p1_svalue(getattr(dev, 'sValue', ''))
            ctx['import_w'] = max(0, imp)
            ctx['export_w'] = max(0, exp)
            ctx['p1_ok'] = True

    solar_name = _param_name('Mode22', SOLAR_DEFAULT_NAME)
    solar_state, api_solar = _hint_from_api(plugin, solar_name, 'Zonnepanelen')
    if solar_state == 'ok':
        solar_w = power_watts_from_api(api_solar)
        if solar_w is None:
            easee_logging.debug(
                'domoticz_energy_hints',
                f'Zonnepanelen: {api_solar.get("Name")} (idx {api_solar.get("idx")}) heeft geen vermogen in watt',
            )
        else:
            ctx['solar_w'] = max(0, solar_w)
            ctx['solar_ok'] = True
            easee_logging.debug(
                'domoticz_energy_hints',
                f'Zonnepanelen: {api_solar.get("Name")} (idx {api_solar.get("idx")}), {ctx["solar_w"]} W',
            )
    elif solar_state in ('unavailable', 'missing'):
        unit, dev = _resolve_device(plugin, solar_name, 'Zonnepanelen')
        if dev is not None:
            solar_w = _parse_energy_svalue(getattr(dev, 'sValue', ''))
            ctx['solar_w'] = max(0, solar_w)
            ctx['solar_ok'] = True

    sessy_raw = (domoticz_runtime.Parameters.get('Mode23', '') or '').strip()
    if sessy_raw:
        battery_state, api_battery = _hint_from_api(plugin, sessy_raw, 'Thuisbatterij')
        if battery_state == 'ok':
            battery_w = power_watts_from_api(api_battery)
            if battery_w is None:
                easee_logging.debug(
                    'domoticz_energy_hints',
                    f'Thuisbatterij: {api_battery.get("Name")} (idx {api_battery.get("idx")}) heeft geen vermogen in watt',
                )
            else:
                ctx['sessy_w'] = battery_w
                ctx['sessy_ok'] = True
                easee_logging.debug(
                    'domoticz_energy_hints',
                    f'Thuisbatterij: {api_battery.get("Name")} (idx {api_battery.get("idx")}), {ctx["sessy_w"]} W',
                )
        elif battery_state in ('unavailable', 'missing'):
            unit, dev = _resolve_device(plugin, sessy_raw, 'Thuisbatterij')
            if dev is not None:
                ctx['sessy_w'] = _parse_energy_svalue(getattr(dev, 'sValue', ''))
                ctx['sessy_ok'] = True

    setattr(plugin, cache_key, ctx)
    return ctx


def clear_energy_context_cache(plugin):
    for attr in ('_energy_hint_context', '_energy_hint_api_devices', '_energy_hint_api_tried'):
        if hasattr(plugin, attr):
            delattr(plugin, attr)


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
        hints.append(easee_i18n.t(plugin, 'hint.solar_surplus'))
    elif ctx.get('p1_ok') and export_w > 0 and not _eq_export_active(plugin):
        hints.append(easee_i18n.t(plugin, 'hint.export'))

    if ctx.get('sessy_ok') and abs(sessy_w) > SESSY_THRESHOLD_W:
        hints.append(easee_i18n.t(plugin, 'hint.battery'))

    if charging and ctx.get('p1_ok') and import_w >= HIGH_IMPORT_THRESHOLD_W:
        hints.append(easee_i18n.t(plugin, 'hint.high_import'))

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
