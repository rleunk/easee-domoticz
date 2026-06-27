# -*- coding: utf-8 -*-

import math
from datetime import datetime
import hashlib
import Domoticz
import domoticz_runtime
from easee_api_keys import EQUALIZER_KEYS

def norm(plugin, value):
    return ' '.join(str(value).strip().split())

def prefix(plugin):
    return 'Easee'

def extra_charger_names(plugin):
    raw = (domoticz_runtime.Parameters.get('Mode4', '') or '').strip()
    if not raw or raw.lower() == 'easee':
        return []
    return [clean_label(plugin, part.strip()) for part in raw.split(',') if part.strip()]

def pref(plugin, label):
    return f'{prefix(plugin)} - {label}'

def clean_label(plugin, name):
    """Verwijder dubbele Easee/hardware prefix uit device-namen."""
    name = norm(plugin, name)
    if not name:
        return name
    prefixes = []
    for p in (prefix(plugin), 'Easee'):
        p = str(p).strip()
        if p and p.lower() not in [x.lower() for x in prefixes]:
            prefixes.append(p)
    changed = True
    while changed:
        changed = False
        for p in prefixes:
            token = f'{p} - '
            if name.lower().startswith(token.lower()):
                name = name[len(token):].strip()
                changed = True
    return name

def safe_float(plugin, value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def safe_int(plugin, value, default=0):
    try:
        return int(value)
    except Exception:
        return default

def truthy(plugin, value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1','true','yes','on')
    if isinstance(value, (int,float)):
        return bool(value)
    return False

def euro_str(plugin, value):
    try:
        return f'{float(value):.2f}'
    except Exception:
        return '0.00'

def power_watts(plugin, value):
    x = safe_float(plugin, value, 0.0)
    if 0 < abs(x) < 100:
        x *= 1000.0
    if x < 0:
        x = 0.0
    return int(round(x))

def kwh_value(plugin, value):
    x = safe_float(plugin, value, 0.0)
    if x > 10000:
        x /= 1000.0
    if x < 0:
        x = 0.0
    return round(x, 3)

def wh_from_kwh(plugin, value):
    try:
        return int(round(float(value) * 1000.0))
    except Exception:
        return 0

def poll_interval_sec(plugin):
    return max(10, safe_int(plugin, domoticz_runtime.Parameters.get('Mode1', '30'), 30))

def short_id(plugin, full_id):
    s = str(full_id).strip()
    return s[-8:] if len(s) > 8 else s

def parse_iso(plugin, value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None

def _mode7_token(plugin):
    return (domoticz_runtime.Parameters.get('Mode7', '') or '').strip()

def tibber_token(plugin):
    from easee_constants import TIBBER_TOKEN_STATE_KEY
    mode7 = _mode7_token(plugin)
    if mode7:
        backup = plugin.state.get(TIBBER_TOKEN_STATE_KEY, '')
        if backup != mode7:
            plugin.state[TIBBER_TOKEN_STATE_KEY] = mode7
        return mode7
    return (plugin.state.get(TIBBER_TOKEN_STATE_KEY) or '').strip()

def _mode24_token(plugin):
    return (domoticz_runtime.Parameters.get('Mode24', '') or '').strip()

def entsoe_token(plugin):
    from easee_constants import ENTSOE_TOKEN_STATE_KEY
    mode24 = _mode24_token(plugin)
    if mode24:
        backup = plugin.state.get(ENTSOE_TOKEN_STATE_KEY, '')
        if backup != mode24:
            plugin.state[ENTSOE_TOKEN_STATE_KEY] = mode24
        return mode24
    return (plugin.state.get(ENTSOE_TOKEN_STATE_KEY) or '').strip()

def entsoe_opslag(plugin):
    from easee_constants import ENTSOE_OPSLAG_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode25', '') or '').strip()
    return _parse_tariff_float(plugin, raw, ENTSOE_OPSLAG_DEFAULT)

def entsoe_energiebelasting(plugin):
    from easee_constants import ENTSOE_ENERGIEBELASTING_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode26', '') or '').strip()
    return _parse_tariff_float(plugin, raw, ENTSOE_ENERGIEBELASTING_DEFAULT)

def entsoe_btw_pct(plugin):
    from easee_constants import ENTSOE_BTW_PCT_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode27', '') or '').strip()
    if not raw:
        return ENTSOE_BTW_PCT_DEFAULT
    try:
        pct = float(str(raw).replace(',', '.'))
    except Exception:
        return ENTSOE_BTW_PCT_DEFAULT
    return max(0.0, min(pct, 100.0))

def pricing_source(plugin):
    """Prijsbron hardware parameter (Mode9). Default Tibber for backward compatibility."""
    raw = (domoticz_runtime.Parameters.get('Mode9', '') or '').strip()
    if not raw:
        return 'Tibber'
    return raw

def _parse_tariff_float(plugin, raw, default):
    if not raw:
        return default
    try:
        return max(0.0, float(str(raw).replace(',', '.')))
    except Exception:
        return default

def _parse_hour_param(plugin, raw, default):
    if not raw:
        return default
    try:
        hour = int(float(str(raw).strip()))
    except Exception:
        return default
    if hour < 0 or hour > 23:
        return default
    return hour

def manual_tariff_type(plugin):
    """Handmatig subtype (Mode11): Vast (default), Dag/nacht, or Dal/piek."""
    raw = (domoticz_runtime.Parameters.get('Mode11', '') or '').strip()
    if raw == 'Dag/nacht':
        return 'Dag/nacht'
    if raw == 'Dal/piek':
        return 'Dal/piek'
    return 'Vast'

def manual_rate(plugin):
    """Vast tarief €/kWh (Mode10, default 0.25)."""
    from easee_constants import MANUAL_RATE_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode10', '') or '').strip()
    return _parse_tariff_float(plugin, raw, MANUAL_RATE_DEFAULT)

def manual_dal_rate(plugin):
    """Dal tarief €/kWh (Mode12, default 0.22)."""
    from easee_constants import MANUAL_DAL_RATE_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode12', '') or '').strip()
    return _parse_tariff_float(plugin, raw, MANUAL_DAL_RATE_DEFAULT)

def manual_normal_rate(plugin):
    """Normal tarief €/kWh (Mode13, default 0.28)."""
    from easee_constants import MANUAL_NORMAL_RATE_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode13', '') or '').strip()
    return _parse_tariff_float(plugin, raw, MANUAL_NORMAL_RATE_DEFAULT)

def manual_dal_start_hour(plugin):
    """Dal start uur 0–23 (Mode14, default 23)."""
    from easee_constants import MANUAL_DAL_START_HOUR_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode14', '') or '').strip()
    return _parse_hour_param(plugin, raw, MANUAL_DAL_START_HOUR_DEFAULT)

def manual_dal_end_hour(plugin):
    """Dal eind uur 0–23 (Mode15, default 7)."""
    from easee_constants import MANUAL_DAL_END_HOUR_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode15', '') or '').strip()
    return _parse_hour_param(plugin, raw, MANUAL_DAL_END_HOUR_DEFAULT)

def manual_piek_rate(plugin):
    """Piek tarief €/kWh (Mode16, default 0.35)."""
    from easee_constants import MANUAL_PIEK_RATE_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode16', '') or '').strip()
    return _parse_tariff_float(plugin, raw, MANUAL_PIEK_RATE_DEFAULT)

def manual_piek_start_hour(plugin):
    """Piek start uur 0–23 (Mode17, default 17)."""
    from easee_constants import MANUAL_PIEK_START_HOUR_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode17', '') or '').strip()
    return _parse_hour_param(plugin, raw, MANUAL_PIEK_START_HOUR_DEFAULT)

def manual_piek_end_hour(plugin):
    """Piek eind uur 0–23 (Mode18, default 21)."""
    from easee_constants import MANUAL_PIEK_END_HOUR_DEFAULT
    raw = (domoticz_runtime.Parameters.get('Mode18', '') or '').strip()
    return _parse_hour_param(plugin, raw, MANUAL_PIEK_END_HOUR_DEFAULT)

def manual_weekend_all_dal(plugin):
    """Weekend volledig dal (Mode19, default Ja)."""
    raw = (domoticz_runtime.Parameters.get('Mode19', '') or '').strip().lower()
    if raw in ('nee', '0', 'false', 'no', 'uit', 'off'):
        return False
    return True

def is_dal_period(dt, start_hour, end_hour):
    """True when datetime falls in dal window (supports overnight, e.g. 23–07)."""
    hour = dt.hour
    if start_hour == end_hour:
        return False
    if start_hour < end_hour:
        return start_hour <= hour < end_hour
    return hour >= start_hour or hour < end_hour

def is_piek_period(dt, start_hour, end_hour):
    """True when datetime falls in piek window (e.g. 17–21 on weekdays)."""
    hour = dt.hour
    if start_hour == end_hour:
        return False
    if start_hour < end_hour:
        return start_hour <= hour < end_hour
    return hour >= start_hour or hour < end_hour

def manual_tariff_period(plugin, dt=None):
    """Return dal, normal, piek, or vast for Handmatig at given datetime."""
    if dt is None:
        dt = datetime.now().astimezone()
    tariff_type = manual_tariff_type(plugin)
    if tariff_type == 'Vast':
        return 'vast'
    is_weekend = dt.weekday() >= 5
    if tariff_type == 'Dal/piek' and is_weekend and manual_weekend_all_dal(plugin):
        return 'dal'
    if is_dal_period(dt, manual_dal_start_hour(plugin), manual_dal_end_hour(plugin)):
        return 'dal'
    if tariff_type == 'Dag/nacht':
        return 'normal'
    if not is_weekend and is_piek_period(
        dt, manual_piek_start_hour(plugin), manual_piek_end_hour(plugin),
    ):
        return 'piek'
    return 'normal'

def manual_rate_at(plugin, dt=None):
    """Current €/kWh for Handmatig (Vast, Dag/nacht, or Dal/piek at given datetime)."""
    if dt is None:
        dt = datetime.now().astimezone()
    if manual_tariff_type(plugin) == 'Vast':
        return manual_rate(plugin)
    period = manual_tariff_period(plugin, dt)
    if period == 'dal':
        return manual_dal_rate(plugin)
    if period == 'piek':
        return manual_piek_rate(plugin)
    return manual_normal_rate(plugin)

def pricing_enabled(plugin):
    """True when kWh×tarief kosten actief zijn (Handmatig, Tibber of ENTSO-E met token)."""
    source = pricing_source(plugin)
    if source == 'Handmatig':
        return True
    if source == 'Geen':
        return False
    if source == 'ENTSO-E':
        return bool(entsoe_token(plugin))
    return bool(tibber_token(plugin))

def dag_overzicht_enabled(plugin):
    """Dag overzicht-tegel: Geen/Handmatig altijd; Tibber/ENTSO-E alleen met token."""
    source = pricing_source(plugin)
    if source in ('Geen', 'Handmatig'):
        return True
    if source == 'ENTSO-E':
        return entsoe_enabled(plugin)
    return tibber_enabled(plugin)

def beste_laden_enabled(plugin):
    """Beste laden-tegel: uit bij Geen; Handmatig, Tibber of ENTSO-E met token."""
    source = pricing_source(plugin)
    if source == 'Geen':
        return False
    if source == 'Handmatig':
        return True
    if source == 'ENTSO-E':
        return entsoe_enabled(plugin)
    return tibber_enabled(plugin)

def tibber_enabled(plugin):
    source = pricing_source(plugin)
    if source in ('Geen', 'Handmatig', 'ENTSO-E'):
        return False
    return bool(tibber_token(plugin))

def entsoe_enabled(plugin):
    source = pricing_source(plugin)
    if source != 'ENTSO-E':
        return False
    return bool(entsoe_token(plugin))

def _parse_besteladen_hours_raw(raw):
    """Parse 1–12 uur; None when leeg, plugin-key of ongeldig."""
    if not raw:
        return None
    lowered = str(raw).strip().lower()
    if 'easee' in lowered or 'autodiscovery' in lowered:
        return None
    try:
        hours = int(float(raw))
    except Exception:
        return None
    if hours < 1 or hours > 12:
        return None
    return hours

def _read_besteladen_hours_param(plugin):
    """Lees venster uit hardware; migreert legacy Extra indien numerisch."""
    from easee_constants import PLUGIN_KEY
    for key in ('BesteLadenHours', 'Extra'):
        raw = (domoticz_runtime.Parameters.get(key, '') or '').strip()
        if not raw:
            continue
        if key == 'Extra':
            if raw == PLUGIN_KEY or PLUGIN_KEY.startswith(raw):
                continue
        hours = _parse_besteladen_hours_raw(raw)
        if hours is not None:
            return hours
    return None

def beste_laden_hours(plugin):
    """Sliding window lengte voor Beste laden (BesteLadenHours, default 3 uur)."""
    from easee_constants import BESTE_LADEN_HOURS_STATE_KEY
    from_params = _read_besteladen_hours_param(plugin)
    if from_params is not None:
        if plugin.state.get(BESTE_LADEN_HOURS_STATE_KEY) != from_params:
            plugin.state[BESTE_LADEN_HOURS_STATE_KEY] = from_params
        return from_params
    backup = plugin.state.get(BESTE_LADEN_HOURS_STATE_KEY)
    try:
        hours = int(backup)
        if 1 <= hours <= 12:
            return hours
    except Exception:
        pass
    return 3

    # ---- emoji & status helpers ----

def kw_to_watts(plugin, value):
    x = safe_float(plugin, value, 0.0)
    if x <= 0:
        return 0
    if abs(x) < 100:
        return int(round(x * 1000.0))
    return int(round(x))

def format_amp(plugin, value):
    x = safe_float(plugin, value, 0.0)
    if x <= 0:
        return None
    if abs(x - round(x)) < 0.05:
        return f'{int(round(x))} A'
    return f'{x:.1f} A'

def current_from_power_3phase(plugin, power_w):
    """Bereken lijnstroom (A) uit actief vermogen op 3×230 V."""
    p = safe_float(plugin, power_w, 0.0)
    if p <= 0:
        return 0.0
    return p / (math.sqrt(3.0) * 230.0)

def amps_balanced_3phase_from_power(plugin, power_w, voltage=230):
    """Max import vermogen (W) → lijnstroom (A) bij evenwichtige 3-fase (17200 W → 24,9 A)."""
    p = safe_float(plugin, power_w, 0.0)
    if p <= 0:
        return 0.0
    return p / (3.0 * voltage)

def phase_currents_from_values(plugin, values):
    phases = []
    any_obs = False
    for key in EQUALIZER_KEYS['phase_current']:
        if key in values and values.get(key) is not None:
            any_obs = True
            phases.append(safe_float(plugin, values.get(key), 0.0))
        else:
            phases.append(None)
    if not any_obs:
        return None, None, None, 0.0, False
    nums = [p for p in phases if p is not None]
    load_a = max(nums) if nums else 0.0
    return phases[0], phases[1], phases[2], load_a, True

def format_phase_amp(plugin, val):
    if val is None:
        return '—'
    if val <= 0:
        return '0.0'
    if abs(val - round(val)) < 0.05:
        return f'{int(round(val))}.0'
    return f'{val:.1f}'

def actual_current_line(plugin, values, power_w):
    l1, l2, l3, load_a, has_phases = phase_currents_from_values(plugin, values)
    if has_phases:
        parts = [format_phase_amp(plugin, v) for v in (l1, l2, l3)]
        return f'📊 L1/L2/L3: {" / ".join(parts)} A', load_a
    calc_a = current_from_power_3phase(plugin, power_w)
    if calc_a > 0:
        return f'📊 Actuele stroom: {calc_a:.1f} A (3-fase)', calc_a
    return None, 0.0

def format_kw(plugin, value):
    x = safe_float(plugin, value, 0.0)
    if x <= 0:
        return None
    if abs(x) >= 100:
        x /= 1000.0
    if abs(x - round(x)) < 0.05:
        return f'{int(round(x))} kW'
    return f'{x:.1f} kW'

def first_dict_value(plugin, data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        if data.get(key) is not None:
            return data.get(key)
    return None
