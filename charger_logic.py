# -*- coding: utf-8 -*-

import domoticz_runtime
from easee_constants import OP_MODE_LABELS
from easee_api_keys import CHARGER_KEYS
import easee_logging
import domoticz_devices
import easee_api
import easee_helpers
import easee_state
import tibber_pricing

def session_energy_kwh(plugin, values, session):
    for source in (values, session if isinstance(session, dict) else {}):
        if not isinstance(source, dict):
            continue
        val = easee_helpers.first_dict_value(plugin, source, CHARGER_KEYS['session_energy'])
        if val is not None:
            return easee_helpers.kwh_value(plugin, val)
    return None

def session_start_timestamp(plugin, values, session):
    for source in (session if isinstance(session, dict) else {}, values):
        if not isinstance(source, dict):
            continue
        val = easee_helpers.first_dict_value(plugin, source, CHARGER_KEYS['session_start'])
        if val:
            dt = easee_helpers.parse_iso(plugin, val)
            if dt is not None:
                return dt.timestamp()
    return None

def is_session_resume(plugin, st, session_active, session, power_w):
    """Recover mid-session after plugin restart — not when sessionEnergy is stale from a prior session."""
    if not session_active:
        return False
    had_session = (
        st.get('session_start_ts') is not None
        or st.get('session_start_kwh') is not None
        or easee_helpers.safe_float(plugin, st.get('session_cost_total'), 0.0) > 0
    )
    if not had_session:
        return False
    return bool(session) or power_w > 50

def sync_day_energy(plugin, st, total_kwh, session_active, power_w):
    """Track today's kWh with a midnight baseline; integrate power when lifetimeEnergy is stale."""
    skip_monotonic = bool(st.pop('day_energy_reset', False))
    if st.get('day_baseline_kwh') is None:
        st['day_baseline_kwh'] = total_kwh
        st['day_last_lifetime_kwh'] = total_kwh
        st['day_kwh'] = 0.0

    baseline = easee_helpers.safe_float(plugin, st.get('day_baseline_kwh'), total_kwh)
    prev_day_kwh = easee_helpers.safe_float(plugin, st.get('day_kwh'), 0.0)
    last_lifetime = st.get('day_last_lifetime_kwh')
    day_delta = 0.0

    if last_lifetime is not None:
        delta_lifetime = max(0.0, float(total_kwh) - float(last_lifetime))
        if delta_lifetime > 0:
            st['day_last_lifetime_kwh'] = total_kwh
            st['day_kwh'] = round(max(prev_day_kwh, float(total_kwh) - baseline), 6)
            day_delta = max(0.0, st['day_kwh'] - prev_day_kwh)
        elif session_active and power_w > 50:
            day_delta = power_integrated_kwh(plugin, power_w)
            st['day_kwh'] = round(prev_day_kwh + day_delta, 6)
    else:
        st['day_last_lifetime_kwh'] = total_kwh

    display_wh = int(round(baseline * 1000.0)) + int(round(easee_helpers.safe_float(plugin, st.get('day_kwh'), 0.0) * 1000.0))
    prev_display = easee_helpers.safe_int(plugin, st.get('display_wh'), 0)
    if not skip_monotonic and display_wh < prev_display:
        display_wh = prev_display
    st['display_wh'] = display_wh
    return display_wh, easee_helpers.safe_float(plugin, st.get('day_kwh'), 0.0), day_delta

def power_integrated_kwh(plugin, power_w):
    if power_w <= 50:
        return 0.0
    interval = float(easee_helpers.poll_interval_sec(plugin))
    return round((float(power_w) / 1000.0) * (interval / 3600.0), 6)

def delta_kwh_for_cost(plugin, session_active, api_session_kwh, prev_session_kwh, total_kwh, prev_total, power_w, day_delta=0.0):
    """Pick the best positive kWh delta for cost accumulation.

    sessionEnergy can be stale in /state when /sessions/ongoing is 429'd; lifetimeEnergy
    often does not move during an active session. Fall back to day-track / power integration.
    Returns (delta_kwh, source_label).
    """
    delta_kwh = 0.0
    source = 'none'
    if session_active and api_session_kwh is not None and prev_session_kwh is not None:
        delta_kwh = max(0.0, float(api_session_kwh) - float(prev_session_kwh))
        if delta_kwh > 0:
            source = 'sessionEnergy'
    if delta_kwh <= 0 and prev_total is not None:
        delta_kwh = max(0.0, float(total_kwh) - float(prev_total))
        if delta_kwh > 0:
            source = 'lifetimeEnergy'
    if delta_kwh <= 0 and day_delta > 0:
        delta_kwh = day_delta
        source = 'day_track'
    if delta_kwh <= 0 and session_active and power_w > 50:
        delta_kwh = power_integrated_kwh(plugin, power_w)
        if delta_kwh > 0:
            source = 'power'
    return delta_kwh, source

def custom_charger_name(plugin, index):
    if index == 0:
        return easee_helpers.clean_label(plugin, domoticz_runtime.Parameters.get('Mode2', '') or '')
    if index == 1:
        return easee_helpers.clean_label(plugin, domoticz_runtime.Parameters.get('Mode3', '') or '')
    extras = easee_helpers.extra_charger_names(plugin)
    extra_index = index - 2
    if 0 <= extra_index < len(extras):
        return extras[extra_index]
    return ''

def charger_display_name(plugin, charger, index):
    custom = custom_charger_name(plugin, index)
    if custom:
        return custom
    api_name = easee_helpers.clean_label(plugin, str(charger.get('name') or '').strip())
    cid = str(charger.get('id') or '').strip()
    if api_name and api_name.lower() not in (cid.lower(), easee_helpers.short_id(plugin, cid).lower()):
        return api_name
    return f'Laadpaal {index + 1}'

def charger_dev_name(plugin, display, label):
    return easee_helpers.clean_label(plugin, f'{display} - {label}')

def op_mode_label(plugin, value):
    if value is None or value == '':
        return 'Onbekend'
    try:
        return OP_MODE_LABELS.get(int(value), f'Modus {int(value)}')
    except Exception:
        text = str(value).strip()
        return text if text else 'Onbekend'

def power_emoji(plugin, power_w):
    """Emoji based on power level"""
    if power_w >= 7000:
        return '⚡⚡'
    elif power_w >= 3500:
        return '⚡'
    elif power_w > 50:
        return '🔌'
    else:
        return '⏸️'

def status_emoji(plugin, online, session_active):
    """Emoji for charger status"""
    if not online:
        return '❌'
    elif session_active:
        return '✅'
    else:
        return '🔴'

def compute_duration_text(plugin, start_ts):
    if not start_ts:
        return '00:00'
    secs = max(0, int(easee_state.now_ts(plugin) - float(start_ts)))
    return f'{secs // 3600:02d}:{(secs % 3600) // 60:02d}'

    # ---- discovery ----

def discover_chargers(plugin):
    chargers = []
    flt = domoticz_runtime.Parameters.get('Mode5', '').strip().lower()
    try:
        data = easee_api.api_get(plugin, '/chargers') or []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                cid = easee_helpers.first_dict_value(plugin, item, CHARGER_KEYS['id'])
                name = str(easee_helpers.first_dict_value(plugin, item, CHARGER_KEYS['name']) or 'Lader')
                site = str(easee_helpers.first_dict_value(plugin, item, CHARGER_KEYS['site']) or '')
                if cid and (not flt or flt in name.lower() or flt in site.lower()):
                    chargers.append({'id': str(cid).strip(), 'name': name, 'siteName': site})
        easee_logging.info('charger_logic', f'Discovery: {len(chargers)} laadpaal(en) gevonden', 'discovery')
    except Exception as e:
        easee_logging.error('charger_logic', f'Discovery chargers mislukt: {e}', 'discovery')
    return sorted({c['id']: c for c in chargers}.values(), key=lambda x: x['id'])

def poll_charger(plugin, charger):
    cid = charger['id']
    values = {}
    session = {}
    try:
        state = easee_api.api_get(plugin, f'/chargers/{cid}/state') or {}
        if isinstance(state, dict):
            values.update(state)
    except Exception as e:
        easee_logging.error('charger_logic', f'State ophalen mislukt voor lader {cid}: {e}', 'poll')
    if not easee_api.is_charger_rate_limited(plugin):
        cfg = easee_api.api_get_optional(plugin, f'/chargers/{cid}/config') or {}
        if isinstance(cfg, dict):
            values.update(cfg)
    if not easee_api.should_skip_ongoing(plugin):
        sess = easee_api.api_get_optional(plugin, f'/chargers/{cid}/sessions/ongoing') or {}
        if isinstance(sess, dict):
            session = sess

    power_w = easee_helpers.power_watts(plugin, values.get(CHARGER_KEYS['power'][0]))
    total_kwh = easee_helpers.kwh_value(plugin, values.get(CHARGER_KEYS['lifetime_energy'][0]))
    online = values.get(CHARGER_KEYS['online'][0])
    op_mode = values.get(CHARGER_KEYS['op_mode'][0])
    status_label = op_mode_label(plugin, op_mode)
    session_status = easee_helpers.first_dict_value(plugin, session, CHARGER_KEYS['session_status']) or ''
    if session_status and not str(session_status).strip().isdigit():
        status_label = str(session_status)
    session_active = bool(session) or power_w > 50
    api_session_kwh = session_energy_kwh(plugin, values, session)

    st = easee_state.charger_state(plugin, cid)
    prev_total = st.get('prev_total_kwh')
    display_wh, day_kwh, day_delta = sync_day_energy(plugin, st, total_kwh, session_active, power_w)

    if session_active and not st.get('session_active'):
        resuming = is_session_resume(plugin, st, session_active, session, power_w)
        api_start_ts = session_start_timestamp(plugin, values, session)
        st['session_active'] = True
        if resuming:
            if api_start_ts is not None:
                st['session_start_ts'] = api_start_ts
            elif st.get('session_start_ts') is None:
                st['session_start_ts'] = easee_state.now_ts(plugin)
            if api_session_kwh is not None:
                st['session_start_kwh'] = max(0.0, float(total_kwh) - float(api_session_kwh))
            elif st.get('session_start_kwh') is None:
                st['session_start_kwh'] = total_kwh
            st['prev_session_kwh'] = None
        else:
            st['session_start_ts'] = api_start_ts if api_start_ts is not None else easee_state.now_ts(plugin)
            st['session_start_kwh'] = total_kwh
            st['prev_session_kwh'] = None
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0

    ending_session = (not session_active) and st.get('session_active')

    delta_kwh, delta_source = delta_kwh_for_cost(
        plugin, session_active, api_session_kwh, st.get('prev_session_kwh'),
        total_kwh, prev_total, power_w, day_delta=day_delta,
    )
    if session_active and api_session_kwh is not None and st.get('prev_session_kwh') is not None:
        if float(api_session_kwh) > float(st.get('prev_session_kwh')):
            st['prev_session_kwh'] = api_session_kwh
    elif session_active and api_session_kwh is not None and st.get('prev_session_kwh') is None:
        st['prev_session_kwh'] = api_session_kwh

    if easee_helpers.tibber_enabled(plugin) and delta_kwh > 0:
        easee_logging.debug(
            'charger_logic',
            f'Kosten delta lader {cid}: {delta_kwh:.6f} kWh via {delta_source}',
            'cost',
        )
        price = tibber_pricing.current_tibber_price(plugin)
        p_total = easee_helpers.safe_float(plugin, price.get('total'), 0.0)
        p_energy = easee_helpers.safe_float(plugin, price.get('energy'), 0.0)
        p_tax = easee_helpers.safe_float(plugin, price.get('tax'), 0.0)
        add_total = delta_kwh * p_total
        add_energy = delta_kwh * p_energy
        add_tax = delta_kwh * p_tax
        st['day_cost_total'] = round(easee_helpers.safe_float(plugin, st.get('day_cost_total', 0.0), 0.0) + add_total, 4)
        st['day_cost_energy'] = round(easee_helpers.safe_float(plugin, st.get('day_cost_energy', 0.0), 0.0) + add_energy, 4)
        st['day_cost_tax'] = round(easee_helpers.safe_float(plugin, st.get('day_cost_tax', 0.0), 0.0) + add_tax, 4)
        if st.get('session_active'):
            st['session_cost_total'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0) + add_total, 4)
            st['session_cost_energy'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0) + add_energy, 4)
            st['session_cost_tax'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0) + add_tax, 4)

    if ending_session:
        if api_session_kwh is not None:
            st['last_session_kwh'] = api_session_kwh
        elif st.get('session_start_kwh') is not None:
            st['last_session_kwh'] = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
        st['last_session_cost_total'] = easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0)
        st['last_session_cost_energy'] = easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0)
        st['last_session_cost_tax'] = easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0)
        st['last_session_duration'] = compute_duration_text(plugin, st.get('session_start_ts'))
        st['session_active'] = False
        st['session_start_ts'] = None
        st['session_start_kwh'] = None
        st['prev_session_kwh'] = None

    if st.get('session_active'):
        if api_session_kwh is not None:
            session_kwh = api_session_kwh
        elif st.get('session_start_kwh') is not None:
            session_kwh = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
        else:
            session_kwh = 0.0
        laadduur = compute_duration_text(plugin, st.get('session_start_ts'))
        session_cost = easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0)
        session_cost_energy = easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0)
        session_cost_tax = easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0)
    else:
        session_kwh = easee_helpers.safe_float(plugin, st.get('last_session_kwh', 0.0), 0.0)
        laadduur = st.get('last_session_duration', '00:00')
        session_cost = easee_helpers.safe_float(plugin, st.get('last_session_cost_total', 0.0), 0.0)
        session_cost_energy = easee_helpers.safe_float(plugin, st.get('last_session_cost_energy', 0.0), 0.0)
        session_cost_tax = easee_helpers.safe_float(plugin, st.get('last_session_cost_tax', 0.0), 0.0)

    st['prev_total_kwh'] = total_kwh

    # UPDATE DEVICES
    domoticz_devices.update_charger_energy(plugin, cid, 'Laden', power_w, display_wh)
    
    totaal_sessie = f'{int(round(total_kwh))} kWh | Sessie: {session_kwh:.3f} kWh'
    domoticz_devices.update_charger_custom(plugin, cid, 'Totaal & Sessie', totaal_sessie)
    
    status_text = (
        f'{status_emoji(plugin, online, session_active)} '
        f'{power_emoji(plugin, power_w)} {status_label} | ⏱️ {laadduur}'
    )
    domoticz_devices.update_charger_text(plugin, cid, 'Status', status_text)
    
    if easee_helpers.tibber_enabled(plugin):
        day_cost = easee_helpers.safe_float(plugin, st.get('day_cost_total', 0.0), 0.0)
        domoticz_devices.update_charger_costs(plugin, cid, session_cost, day_cost, session_kwh, session_active)
    
    plugin.latest_chargers[cid] = {
        'power': power_w,
        'kwh': total_kwh,
        'wh': display_wh,
        'day_kwh': day_kwh,
        'day_cost': easee_helpers.safe_float(plugin, st.get('day_cost_total', 0.0), 0.0),
        'day_energy_cost': easee_helpers.safe_float(plugin, st.get('day_cost_energy', 0.0), 0.0),
        'day_tax_cost': easee_helpers.safe_float(plugin, st.get('day_cost_tax', 0.0), 0.0),
        'online': online,
    }
