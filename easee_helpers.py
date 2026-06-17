# -*- coding: utf-8 -*-

import math
from datetime import datetime
import hashlib
import Domoticz
import domoticz_runtime

def norm(plugin, value):
    return ' '.join(str(value).strip().split())

def prefix(plugin):
    return 'Easee'

def extra_charger_names(plugin):
    raw = (domoticz_runtime.Parameters.get('Mode4', '') or '').strip()
    if not raw or raw.lower() == 'easee':
        return []
    return [plugin.clean_label(part.strip()) for part in raw.split(',') if part.strip()]

def pref(plugin, label):
    return f'{plugin.prefix()} - {label}'

def clean_label(plugin, name):
    """Verwijder dubbele Easee/hardware prefix uit device-namen."""
    name = plugin.norm(name)
    if not name:
        return name
    prefixes = []
    for p in (plugin.prefix(), 'Easee'):
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
    x = plugin.safe_float(value, 0.0)
    if 0 < abs(x) < 100:
        x *= 1000.0
    if x < 0:
        x = 0.0
    return int(round(x))

def kwh_value(plugin, value):
    x = plugin.safe_float(value, 0.0)
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
    return max(10, plugin.safe_int(domoticz_runtime.Parameters.get('Mode1', '30'), 30))

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

def tibber_token(plugin):
    return (domoticz_runtime.Parameters.get('Mode7', '') or '').strip()

def tibber_enabled(plugin):
    return bool(plugin.tibber_token())

    # ---- emoji & status helpers ----

def kw_to_watts(plugin, value):
    x = plugin.safe_float(value, 0.0)
    if x <= 0:
        return 0
    if abs(x) < 100:
        return int(round(x * 1000.0))
    return int(round(x))

def format_amp(plugin, value):
    x = plugin.safe_float(value, 0.0)
    if x <= 0:
        return None
    if abs(x - round(x)) < 0.05:
        return f'{int(round(x))} A'
    return f'{x:.1f} A'

def current_from_power_3phase(plugin, power_w):
    """Bereken lijnstroom (A) uit actief vermogen op 3×230 V."""
    p = plugin.safe_float(power_w, 0.0)
    if p <= 0:
        return 0.0
    return p / (math.sqrt(3.0) * 230.0)

def amps_balanced_3phase_from_power(plugin, power_w, voltage=230):
    """Max import vermogen (W) → lijnstroom (A) bij evenwichtige 3-fase (17200 W → 24,9 A)."""
    p = plugin.safe_float(power_w, 0.0)
    if p <= 0:
        return 0.0
    return p / (3.0 * voltage)

def phase_currents_from_values(plugin, values):
    phases = []
    any_obs = False
    for key in ('currentL1', 'currentL2', 'currentL3'):
        if key in values and values.get(key) is not None:
            any_obs = True
            phases.append(plugin.safe_float(values.get(key), 0.0))
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
    l1, l2, l3, load_a, has_phases = plugin.phase_currents_from_values(values)
    if has_phases:
        parts = [plugin.format_phase_amp(v) for v in (l1, l2, l3)]
        return f'📊 L1/L2/L3: {" / ".join(parts)} A', load_a
    calc_a = plugin.current_from_power_3phase(power_w)
    if calc_a > 0:
        return f'📊 Actuele stroom: {calc_a:.1f} A (3-fase)', calc_a
    return None, 0.0

def format_kw(plugin, value):
    x = plugin.safe_float(value, 0.0)
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
