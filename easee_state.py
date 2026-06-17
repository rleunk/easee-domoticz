# -*- coding: utf-8 -*-

import os, json, time
from datetime import datetime
from easee_constants import STATE_FILE

def state_path(plugin):
    return os.path.join(plugin.plugin_dir, STATE_FILE)

def load_state(plugin):
    try:
        fp = plugin.state_path()
        if os.path.isfile(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    plugin.state.update(loaded)
    except Exception as e:
        plugin.debug(f'state load failed: {e}')

def save_state(plugin):
    try:
        with open(plugin.state_path(), 'w', encoding='utf-8') as f:
            json.dump(plugin.state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        plugin.debug(f'state save failed: {e}')

    # ---- index ----

def today_key(plugin):
    return datetime.now().strftime('%Y-%m-%d')

def now_ts(plugin):
    return time.time()

def charger_state(plugin, cid):
    store = plugin.state.setdefault('chargers', {})
    st = store.setdefault(cid, {
        'prev_total_kwh': None,
        'prev_session_kwh': None,
        'session_active': False,
        'session_start_ts': None,
        'session_start_kwh': None,
        'session_cost_total': 0.0,
        'session_cost_energy': 0.0,
        'session_cost_tax': 0.0,
        'last_session_kwh': 0.0,
        'last_session_cost_total': 0.0,
        'last_session_cost_energy': 0.0,
        'last_session_cost_tax': 0.0,
        'last_session_duration': '00:00',
        'day_key': plugin.today_key(),
        'day_cost_total': 0.0,
        'day_cost_energy': 0.0,
        'day_cost_tax': 0.0,
    })
    if st.get('day_key') != plugin.today_key():
        st['day_key'] = plugin.today_key()
        st['day_cost_total'] = 0.0
        st['day_cost_energy'] = 0.0
        st['day_cost_tax'] = 0.0
    return st
