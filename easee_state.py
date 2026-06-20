# -*- coding: utf-8 -*-

import os, json, time
from datetime import datetime
from easee_constants import STATE_FILE, LEGACY_STATE_FILE, PLUGIN_VERSION, TIBBER_TOKEN_STATE_KEY
import easee_logging
import easee_helpers

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

def sync_tibber_token_backup(plugin):
    """Persist Mode7 token in state; use backup when Domoticz clears password on save."""
    import domoticz_runtime
    mode7 = (domoticz_runtime.Parameters.get('Mode7', '') or '').strip()
    backup = (plugin.state.get(TIBBER_TOKEN_STATE_KEY) or '').strip()
    if mode7:
        if backup != mode7:
            plugin.state[TIBBER_TOKEN_STATE_KEY] = mode7
            return 'updated'
        return 'unchanged'
    if backup:
        return 'restored'
    return 'missing'

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
        'session_start_day_kwh': None,
        'session_integrated_kwh': 0.0,
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
        if st.get('session_active'):
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0
            st['session_integrated_kwh'] = 0.0
            st['prev_session_kwh'] = None
    if st.get('day_energy_key') != tk:
        st['day_energy_key'] = tk
        st['day_baseline_kwh'] = None
        st['day_kwh'] = 0.0
        st['day_last_lifetime_kwh'] = None
        st['day_wh'] = 0
        st['counter_wh'] = 0
        st['day_energy_reset'] = True
    elif 'display_wh' in st:
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
    target = '10.9.27-lifetime-counter'
    current = plugin.state.get(key)
    if current == target:
        return
    for st in (plugin.state.get('chargers') or {}).values():
        if not isinstance(st, dict):
            continue
        st.pop('display_wh', None)
        st.pop('counter_wh', None)
        st['day_baseline_kwh'] = None
        st['day_kwh'] = 0.0
        st['day_last_lifetime_kwh'] = None
        st['day_wh'] = 0
        st['counter_wh'] = 0
        st['day_energy_reset'] = True
        st['prev_session_kwh'] = None
    plugin.state[key] = target
    from_ver = current or 'geen'
    easee_logging.info(
        'easee_state',
        f'State gemigreerd naar {PLUGIN_VERSION} lifetime Counter (was {from_ver}; energy track reset)',
        'migration',
    )

def migrate_cost_tracking(plugin):
    """One-time reset of session cost baselines when cost delta logic changes."""
    key = 'cost_track_version'
    target = '10.10.2-session-cost-reset'
    if plugin.state.get(key) == target:
        return
    for st in (plugin.state.get('chargers') or {}).values():
        if not isinstance(st, dict):
            continue
        st['prev_session_kwh'] = None
        st.pop('cost_delta_warned', None)
        if not st.get('session_active'):
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0
            st['session_integrated_kwh'] = 0.0
    plugin.state[key] = target
    easee_logging.info(
        'easee_state',
        f'Kosten-tracking gemigreerd naar {PLUGIN_VERSION} (prev_session_kwh gereset)',
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


def daily_report_state(plugin):
    """Alias for global_day_state (Dagrapport tile)."""
    return global_day_state(plugin)


def track_daily_report(plugin, day_kwh_delta=0.0, day_cost_delta=0.0, charging=False):
    track_global_charge(plugin, day_kwh_delta, day_cost_delta, charging)


def format_charge_duration(seconds):
    secs = max(0, int(seconds or 0))
    h, rem = divmod(secs, 3600)
    m = rem // 60
    if h > 0:
        return f'{h}u {m:02d}m'
    return f'{m}m'


def global_day_state(plugin):
    """Dagtotalen voor Dagrapport-tegel (alle laders samen)."""
    store = plugin.state.setdefault('global_day', {})
    tk = today_key(plugin)
    if store.get('day_key') != tk:
        store.clear()
        store.update({
            'day_key': tk,
            'charge_kwh': 0.0,
            'charge_hours': 0.0,
            'charge_cost': 0.0,
            'last_track_ts': None,
        })
    return store

def track_global_charge(plugin, day_kwh_delta=0.0, day_cost_delta=0.0, any_charging=False):
    """Accumuleer laaduren en kWh voor Dagrapport."""
    g = global_day_state(plugin)
    if day_kwh_delta > 0:
        g['charge_kwh'] = round(easee_helpers.safe_float(plugin, g.get('charge_kwh'), 0.0) + day_kwh_delta, 4)
    if day_cost_delta > 0:
        g['charge_cost'] = round(easee_helpers.safe_float(plugin, g.get('charge_cost'), 0.0) + day_cost_delta, 4)
    if any_charging:
        interval_h = float(easee_helpers.poll_interval_sec(plugin)) / 3600.0
        g['charge_hours'] = round(easee_helpers.safe_float(plugin, g.get('charge_hours'), 0.0) + interval_h, 4)
    g['last_track_ts'] = now_ts(plugin)
