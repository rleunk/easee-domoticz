# -*- coding: utf-8 -*-

import domoticz_runtime
from easee_constants import OP_MODE_LABELS
from easee_api_keys import CHARGER_KEYS
import easee_logging

def session_energy_kwh(plugin, values, session):
    for source in (values, session if isinstance(session, dict) else {}):
        if not isinstance(source, dict):
            continue
        val = plugin.first_dict_value(source, CHARGER_KEYS['session_energy'])
        if val is not None:
            return plugin.kwh_value(val)
    return None

def power_integrated_kwh(plugin, power_w):
    if power_w <= 50:
        return 0.0
    interval = float(plugin.poll_interval_sec())
    return round((float(power_w) / 1000.0) * (interval / 3600.0), 6)

def custom_charger_name(plugin, index):
    if index == 0:
        return plugin.clean_label(domoticz_runtime.Parameters.get('Mode2', '') or '')
    if index == 1:
        return plugin.clean_label(domoticz_runtime.Parameters.get('Mode3', '') or '')
    extras = plugin.extra_charger_names()
    extra_index = index - 2
    if 0 <= extra_index < len(extras):
        return extras[extra_index]
    return ''

def charger_display_name(plugin, charger, index):
    custom = plugin.custom_charger_name(index)
    if custom:
        return custom
    api_name = plugin.clean_label(str(charger.get('name') or '').strip())
    cid = str(charger.get('id') or '').strip()
    if api_name and api_name.lower() not in (cid.lower(), plugin.short_id(cid).lower()):
        return api_name
    return f'Laadpaal {index + 1}'

def charger_dev_name(plugin, display, label):
    return plugin.clean_label(f'{display} - {label}')

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
    secs = max(0, int(plugin.now_ts() - float(start_ts)))
    return f'{secs // 3600:02d}:{(secs % 3600) // 60:02d}'

    # ---- discovery ----

def discover_chargers(plugin):
    chargers = []
    flt = domoticz_runtime.Parameters.get('Mode5', '').strip().lower()
    try:
        data = plugin.api_get('/chargers') or []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                cid = plugin.first_dict_value(item, CHARGER_KEYS['id'])
                name = str(plugin.first_dict_value(item, CHARGER_KEYS['name']) or 'Lader')
                site = str(plugin.first_dict_value(item, CHARGER_KEYS['site']) or '')
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
        state = plugin.api_get(f'/chargers/{cid}/state') or {}
        if isinstance(state, dict):
            values.update(state)
    except Exception as e:
        easee_logging.error('charger_logic', f'State ophalen mislukt voor lader {cid}: {e}', 'poll')
    try:
        cfg = plugin.api_get(f'/chargers/{cid}/config') or {}
        if isinstance(cfg, dict):
            values.update(cfg)
    except Exception:
        pass
    try:
        sess = plugin.api_get(f'/chargers/{cid}/sessions/ongoing') or {}
        if isinstance(sess, dict):
            session = sess
    except Exception:
        pass

    power_w = plugin.power_watts(values.get(CHARGER_KEYS['power'][0]))
    total_kwh = plugin.kwh_value(values.get(CHARGER_KEYS['lifetime_energy'][0]))
    total_wh = plugin.wh_from_kwh(total_kwh)
    online = values.get(CHARGER_KEYS['online'][0])
    op_mode = values.get(CHARGER_KEYS['op_mode'][0])
    status_label = plugin.op_mode_label(op_mode)
    session_status = plugin.first_dict_value(session, CHARGER_KEYS['session_status']) or ''
    if session_status and not str(session_status).strip().isdigit():
        status_label = str(session_status)
    session_active = bool(session) or power_w > 50
    api_session_kwh = plugin.session_energy_kwh(values, session)

    st = plugin.charger_state(cid)
    prev_total = st.get('prev_total_kwh')

    if session_active and not st.get('session_active'):
        st['session_active'] = True
        st['session_start_ts'] = plugin.now_ts()
        st['session_start_kwh'] = total_kwh
        st['prev_session_kwh'] = api_session_kwh if api_session_kwh is not None else None
        st['session_cost_total'] = 0.0
        st['session_cost_energy'] = 0.0
        st['session_cost_tax'] = 0.0

    ending_session = (not session_active) and st.get('session_active')

    delta_kwh = 0.0
    if session_active and api_session_kwh is not None:
        prev_session = st.get('prev_session_kwh')
        if prev_session is not None:
            delta_kwh = max(0.0, float(api_session_kwh) - float(prev_session))
        st['prev_session_kwh'] = api_session_kwh
    elif prev_total is not None:
        delta_kwh = max(0.0, float(total_kwh) - float(prev_total))
    if delta_kwh <= 0 and session_active and power_w > 50 and api_session_kwh is None:
        delta_kwh = plugin.power_integrated_kwh(power_w)

    if plugin.tibber_enabled() and delta_kwh > 0:
        price = plugin.current_tibber_price()
        p_total = plugin.safe_float(price.get('total'), 0.0)
        p_energy = plugin.safe_float(price.get('energy'), 0.0)
        p_tax = plugin.safe_float(price.get('tax'), 0.0)
        add_total = delta_kwh * p_total
        add_energy = delta_kwh * p_energy
        add_tax = delta_kwh * p_tax
        st['day_cost_total'] = round(plugin.safe_float(st.get('day_cost_total', 0.0), 0.0) + add_total, 4)
        st['day_cost_energy'] = round(plugin.safe_float(st.get('day_cost_energy', 0.0), 0.0) + add_energy, 4)
        st['day_cost_tax'] = round(plugin.safe_float(st.get('day_cost_tax', 0.0), 0.0) + add_tax, 4)
        if st.get('session_active'):
            st['session_cost_total'] = round(plugin.safe_float(st.get('session_cost_total', 0.0), 0.0) + add_total, 4)
            st['session_cost_energy'] = round(plugin.safe_float(st.get('session_cost_energy', 0.0), 0.0) + add_energy, 4)
            st['session_cost_tax'] = round(plugin.safe_float(st.get('session_cost_tax', 0.0), 0.0) + add_tax, 4)

    if ending_session:
        if api_session_kwh is not None:
            st['last_session_kwh'] = api_session_kwh
        elif st.get('session_start_kwh') is not None:
            st['last_session_kwh'] = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
        st['last_session_cost_total'] = plugin.safe_float(st.get('session_cost_total', 0.0), 0.0)
        st['last_session_cost_energy'] = plugin.safe_float(st.get('session_cost_energy', 0.0), 0.0)
        st['last_session_cost_tax'] = plugin.safe_float(st.get('session_cost_tax', 0.0), 0.0)
        st['last_session_duration'] = plugin.compute_duration_text(st.get('session_start_ts'))
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
        laadduur = plugin.compute_duration_text(st.get('session_start_ts'))
        session_cost = plugin.safe_float(st.get('session_cost_total', 0.0), 0.0)
        session_cost_energy = plugin.safe_float(st.get('session_cost_energy', 0.0), 0.0)
        session_cost_tax = plugin.safe_float(st.get('session_cost_tax', 0.0), 0.0)
    else:
        session_kwh = plugin.safe_float(st.get('last_session_kwh', 0.0), 0.0)
        laadduur = st.get('last_session_duration', '00:00')
        session_cost = plugin.safe_float(st.get('last_session_cost_total', 0.0), 0.0)
        session_cost_energy = plugin.safe_float(st.get('last_session_cost_energy', 0.0), 0.0)
        session_cost_tax = plugin.safe_float(st.get('last_session_cost_tax', 0.0), 0.0)

    st['prev_total_kwh'] = total_kwh

    # UPDATE DEVICES
    plugin.update_charger_energy(cid, 'Laden', power_w, total_wh)
    
    totaal_sessie = f'{int(round(total_kwh))} kWh | Sessie: {int(round(session_kwh))} kWh'
    plugin.update_charger_custom(cid, 'Totaal & Sessie', totaal_sessie)
    
    power_emoji = plugin.power_emoji(power_w)
    status_emoji = plugin.status_emoji(online, session_active)
    status_text = f'{status_emoji} {power_emoji} {status_label} | ⏱️ {laadduur}'
    plugin.update_charger_text(cid, 'Status', status_text)
    
    if plugin.tibber_enabled():
        day_cost = plugin.safe_float(st.get('day_cost_total', 0.0), 0.0)
        plugin.update_charger_costs(cid, session_cost, day_cost, session_kwh, bool(st.get('session_active')))
    
    plugin.latest_chargers[cid] = {
        'power': power_w,
        'kwh': total_kwh,
        'wh': total_wh,
        'day_cost': plugin.safe_float(st.get('day_cost_total', 0.0), 0.0),
        'day_energy_cost': plugin.safe_float(st.get('day_cost_energy', 0.0), 0.0),
        'day_tax_cost': plugin.safe_float(st.get('day_cost_tax', 0.0), 0.0),
        'online': online,
    }
