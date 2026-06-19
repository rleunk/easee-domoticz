# -*- coding: utf-8 -*-

import os, json, time
from datetime import datetime
from easee_constants import STATE_FILE, LEGACY_STATE_FILE, PLUGIN_VERSION
import easee_logging

def state_path(plugin):
    return os.path.join(plugin.plugin_dir, STATE_FILE)

def legacy_state_path(plugin):
    return os.path.join(plugin.plugin_dir, LEGACY_STATE_FILE)

def _migrate_state_file(plugin):
    new_fp = state_path(plugin)
    old_fp = legacy_state_path(plugin)
    if os.path.isfile(old_fp) and not os.path.isfile(new_fp):
        try:
            os.rename(old_fp, new_fp)
            easee_logging.info('easee_state', f'State-bestand gemigreerd: {LEGACY_STATE_FILE} → {STATE_FILE}', 'migration')
        except Exception as e:
            easee_logging.warning('easee_state', f'State-migratie mislukt ({LEGACY_STATE_FILE}): {e}', 'migration')

def _resolve_state_file(plugin):
    new_fp = state_path(plugin)
    if os.path.isfile(new_fp):
        return new_fp
    old_fp = legacy_state_path(plugin)
    if os.path.isfile(old_fp):
        return old_fp
    return new_fp

def load_state(plugin):
    _migrate_state_file(plugin)
    try:
        fp = _resolve_state_file(plugin)
        if os.path.isfile(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    plugin.state.update(loaded)
    except Exception as e:
        easee_logging.debug('easee_state', f'state load failed: {e}', 'load')

def save_state(plugin):
    fp = state_path(plugin)
    tmp_fp = fp + '.tmp'
    try:
        with open(tmp_fp, 'w', encoding='utf-8') as f:
            json.dump(plugin.state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_fp, fp)
    except Exception as e:
        if os.path.isfile(tmp_fp):
            try:
                os.remove(tmp_fp)
            except OSError:
                pass
        easee_logging.error('easee_state', f'state save failed: {e}', 'save')

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
        'day_key': today_key(plugin),
        'day_cost_total': 0.0,
        'day_cost_energy': 0.0,
        'day_cost_tax': 0.0,
        'day_energy_key': today_key(plugin),
        'day_baseline_kwh': None,
        'day_kwh': 0.0,
        'day_last_lifetime_kwh': None,
        'day_wh': 0,
        'counter_wh': 0,
    })
    tk = today_key(plugin)
    if st.get('day_key') != tk:
        st['day_key'] = tk
        st['day_cost_total'] = 0.0
        st['day_cost_energy'] = 0.0
        st['day_cost_tax'] = 0.0
    if st.get('day_energy_key') != tk:
        st['day_energy_key'] = tk
        st['day_baseline_kwh'] = None
        st['day_kwh'] = 0.0
        st['day_last_lifetime_kwh'] = None
        st['day_wh'] = 0
        st['counter_wh'] = 0
        st['day_energy_reset'] = True
    elif 'display_wh' in st:
        # v10.9.25 used lifetime+baseline Counter; reset day track on upgrade
        st.pop('display_wh', None)
        st['day_baseline_kwh'] = None
        st['day_kwh'] = 0.0
        st['day_last_lifetime_kwh'] = None
        st['day_wh'] = 0
        st['counter_wh'] = 0
        st['day_energy_reset'] = True
    return st

def migrate_state_for_version(plugin):
    """One-time resets when energy/cost tracking logic changes."""
    key = 'energy_track_version'
    if plugin.state.get(key) == PLUGIN_VERSION:
        return
    for st in (plugin.state.get('chargers') or {}).values():
        if not isinstance(st, dict):
            continue
        st.pop('display_wh', None)
        st['day_baseline_kwh'] = None
        st['day_kwh'] = 0.0
        st['day_last_lifetime_kwh'] = None
        st['day_wh'] = 0
        st['counter_wh'] = 0
        st['day_energy_reset'] = True
        st['prev_session_kwh'] = None
    plugin.state[key] = PLUGIN_VERSION
    easee_logging.info(
        'easee_state',
        f'State gemigreerd naar {PLUGIN_VERSION} (dag-kWh/kosten-teller gereset)',
        'migration',
    )

def equalizer_state(plugin, eid):
    store = plugin.state.setdefault('equalizers', {})
    return store.setdefault(eid, {
        'integrated_kwh': 0.0,
        'last_import_w': None,
        'last_export_w': None,
        'last_power_ts': None,
    })
