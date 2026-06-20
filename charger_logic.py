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

def session_energy_kwh(plugin, values, session, ongoing_fetched=False):
    # Prefer /sessions/ongoing over /state — state sessionEnergy can stay stale after 429 or day change.
    def _positive_kwh(raw):
        if raw is None:
            return None
        kwh = easee_helpers.kwh_value(plugin, raw)
        return kwh if kwh > 0 else None

    if isinstance(session, dict) and session:
        val = easee_helpers.first_dict_value(plugin, session, CHARGER_KEYS['session_energy'])
        parsed = _positive_kwh(val)
        if parsed is not None:
            return parsed
    if ongoing_fetched:
        return None
    if isinstance(values, dict):
        val = easee_helpers.first_dict_value(plugin, values, CHARGER_KEYS['session_energy'])
        return _positive_kwh(val)
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
    )
    if not had_session:
        return False
    return bool(session) or power_w > 50

def sync_day_energy(plugin, st, total_kwh, session_active, power_w):
    """Track today's kWh; Domoticz CounterToday = Counter - Counter@midnight.

    Counter (sValue Wh) must stay lifetime-style: midnight baseline Wh + day Wh.
    Sending day-only Wh leaves Domoticz CounterToday baseline at the old lifetime
    total and produces negative *Vandaag* values.
    """
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
            if session_active and power_w > 50:
                # lifetimeEnergy can jump with stale session totals during active charging
                day_delta = power_integrated_kwh(plugin, power_w)
                st['day_kwh'] = round(prev_day_kwh + day_delta, 6)
            else:
                st['day_kwh'] = round(max(prev_day_kwh, float(total_kwh) - baseline), 6)
                day_delta = max(0.0, st['day_kwh'] - prev_day_kwh)
        elif session_active and power_w > 50:
            day_delta = power_integrated_kwh(plugin, power_w)
            st['day_kwh'] = round(prev_day_kwh + day_delta, 6)
    else:
        st['day_last_lifetime_kwh'] = total_kwh
        if session_active and power_w > 50:
            day_delta = power_integrated_kwh(plugin, power_w)
            st['day_kwh'] = round(prev_day_kwh + day_delta, 6)

    day_kwh = easee_helpers.safe_float(plugin, st.get('day_kwh'), 0.0)
    counter_wh = int(round(baseline * 1000.0)) + int(round(day_kwh * 1000.0))
    if not skip_monotonic:
        prev_counter = easee_helpers.safe_int(plugin, st.get('counter_wh'), 0)
        if counter_wh < prev_counter:
            counter_wh = prev_counter
    st['counter_wh'] = counter_wh
    st['day_wh'] = int(round(day_kwh * 1000.0))
    return counter_wh, day_kwh, day_delta

def power_integrated_kwh(plugin, power_w):
    if power_w <= 50:
        return 0.0
    interval = float(easee_helpers.poll_interval_sec(plugin))
    return round((float(power_w) / 1000.0) * (interval / 3600.0), 6)

def delta_kwh_for_cost(plugin, session_active, api_session_kwh, prev_session_kwh, total_kwh, prev_total, power_w, day_delta=0.0):
    """Pick the best positive kWh delta for cost accumulation.

    sessionEnergy can be stale in /state when /sessions/ongoing is 429'd; lifetimeEnergy
    often does not move during an active session. During active charging prefer day_track
    and power integration over stale lifetime deltas.
    Returns (delta_kwh, source_label).
    """
    if session_active and api_session_kwh is not None and prev_session_kwh is not None:
        session_delta = max(0.0, float(api_session_kwh) - float(prev_session_kwh))
        if session_delta > 0:
            return session_delta, 'sessionEnergy'
    if session_active and power_w > 50:
        if day_delta > 0:
            return day_delta, 'day_track'
        power_delta = power_integrated_kwh(plugin, power_w)
        if power_delta > 0:
            return power_delta, 'power'
    if prev_total is not None:
        lifetime_delta = max(0.0, float(total_kwh) - float(prev_total))
        if lifetime_delta > 0:
            return lifetime_delta, 'lifetimeEnergy'
    return 0.0, 'none'

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

def session_elapsed_hours(plugin, start_ts):
    if start_ts is None:
        return 0.0
    return max(0.0, (easee_state.now_ts(plugin) - float(start_ts)) / 3600.0)

def estimate_session_kwh_from_power(power_w, elapsed_h):
    if power_w <= 50 or elapsed_h <= 0:
        return 0.0
    return round((float(power_w) / 1000.0) * elapsed_h, 6)

def _session_day_delta(plugin, st, day_kwh):
    start_day = st.get('session_start_day_kwh')
    if start_day is None:
        return None
    return max(0.0, float(day_kwh) - float(start_day))

def _estimate_session_kwh_so_far(plugin, st, day_kwh, power_w, api_session_kwh=None):
    """Best-effort session energy for baseline repair (API → integrated → day delta → power×time)."""
    if api_session_kwh is not None and float(api_session_kwh) > 0:
        return float(api_session_kwh)
    integrated = easee_helpers.safe_float(plugin, st.get('session_integrated_kwh', 0.0), 0.0)
    if integrated > 0:
        return integrated
    day_delta = _session_day_delta(plugin, st, day_kwh)
    if day_delta is not None and day_delta > 0:
        return day_delta
    elapsed_h = session_elapsed_hours(plugin, st.get('session_start_ts'))
    return estimate_session_kwh_from_power(power_w, elapsed_h)

def ensure_session_start_day_kwh(plugin, st, day_kwh, api_session_kwh=None, power_w=0, start_ts=None, cid=''):
    """Baseline day_kwh at session start — same counter source as the Laden tile."""
    existing = st.get('session_start_day_kwh')
    if existing is not None:
        if power_w > 50 and float(day_kwh) > 0.05:
            delta = _session_day_delta(plugin, st, day_kwh)
            stuck = abs(float(day_kwh) - float(existing)) < 0.001
            if delta is not None and (stuck or delta < 0.5):
                unstick_session_day_baseline(
                    plugin, st, day_kwh, power_w, api_session_kwh=api_session_kwh, cid=cid,
                    force=stuck,
                )
        return
    integrated = easee_helpers.safe_float(plugin, st.get('session_integrated_kwh', 0.0), 0.0)
    if api_session_kwh is not None and float(api_session_kwh) > 0:
        st['session_start_day_kwh'] = max(0.0, float(day_kwh) - float(api_session_kwh))
        return
    if integrated > 0:
        st['session_start_day_kwh'] = max(0.0, float(day_kwh) - integrated)
        return
    ts = start_ts if start_ts is not None else st.get('session_start_ts')
    elapsed_h = session_elapsed_hours(plugin, ts)
    if ts is not None and power_w > 50 and elapsed_h > 0:
        est_session = estimate_session_kwh_from_power(power_w, elapsed_h)
        st['session_start_day_kwh'] = max(0.0, float(day_kwh) - est_session)
        return
    if float(day_kwh) > 0.05 and power_w > 50:
        st['session_start_day_kwh'] = 0.0
        return
    st['session_start_day_kwh'] = float(day_kwh)

def unstick_session_day_baseline(plugin, st, day_kwh, power_w, api_session_kwh=None, cid='', force=False):
    """Repair session_start_day_kwh when day-track delta is stuck near 0 during active charging."""
    if power_w <= 50 or float(day_kwh) < 0.05:
        return False
    start_day = st.get('session_start_day_kwh')
    if start_day is None:
        return False
    delta = _session_day_delta(plugin, st, day_kwh)
    if delta is None:
        return False
    stuck = abs(float(day_kwh) - float(start_day)) < 0.001 and float(day_kwh) > 0.05
    if not force and not stuck and delta >= 0.5:
        return False
    session_so_far = _estimate_session_kwh_so_far(plugin, st, day_kwh, power_w, api_session_kwh)
    if session_so_far < 0.05:
        session_so_far = float(day_kwh)
    new_baseline = max(0.0, float(day_kwh) - session_so_far)
    if abs(new_baseline - float(start_day)) < 0.001 and float(day_kwh) > 0.05:
        new_baseline = 0.0
    if abs(new_baseline - float(start_day)) < 0.001:
        return False
    old_baseline = float(start_day)
    st['session_start_day_kwh'] = new_baseline
    elapsed_h = session_elapsed_hours(plugin, st.get('session_start_ts'))
    easee_logging.info(
        'charger_logic',
        f'Sessie-baseline gecorrigeerd lader {cid}: day_kwh={day_kwh:.3f}, '
        f'was start_day={old_baseline:.3f}, nu={new_baseline:.3f} '
        f'(delta={delta:.3f}, sessie≈{session_so_far:.3f}, timer={elapsed_h * 60:.0f}m, {power_w}W)',
        'session',
    )
    st.pop('session_kwh_zero_warned', None)
    st['session_kwh_zero_polls'] = 0
    return True

def display_session_kwh(plugin, st, session_kwh, day_kwh, power_w, session_active, api_session_kwh=None):
    """Unified session kWh for CustomkWh header and sValue — never show 0 while day_kwh grows."""
    if not (session_active and power_w > 50):
        return float(session_kwh)
    start_day = float(st.get('session_start_day_kwh') or 0.0)
    day_delta = max(0.0, float(day_kwh) - start_day)
    elapsed_h = session_elapsed_hours(plugin, st.get('session_start_ts'))
    power_est = estimate_session_kwh_from_power(power_w, elapsed_h)
    api_kwh = float(api_session_kwh) if api_session_kwh else 0.0
    display = max(float(session_kwh), day_delta, power_est, api_kwh)
    # CustomkWh header uses int(round(kWh)) — values below 0.5 kWh render as 0.
    if int(round(display)) == 0 and float(day_kwh) > 0.05:
        display = float(day_kwh)
        if st.get('session_start_day_kwh') is not None:
            st['session_start_day_kwh'] = 0.0
    return round(display, 6)

def track_session_kwh_zero_polls(plugin, st, display_kwh, day_kwh, power_w, session_active, cid=''):
    """WARNING after 3 polls with 0 kWh display while charging and day_kwh > 0."""
    if not (session_active and power_w > 50 and float(day_kwh) > 0.05):
        st['session_kwh_zero_polls'] = 0
        return
    if int(round(float(display_kwh))) > 0:
        st['session_kwh_zero_polls'] = 0
        st.pop('session_kwh_zero_warned', None)
        return
    polls = easee_helpers.safe_int(plugin, st.get('session_kwh_zero_polls', 0), 0) + 1
    st['session_kwh_zero_polls'] = polls
    if polls >= 3 and not st.get('session_kwh_zero_warned'):
        st['session_kwh_zero_warned'] = True
        easee_logging.warning(
            'charger_logic',
            f'Sessie-kWh header nog 0 na {polls} polls lader {cid}: day_kwh={day_kwh:.3f}, '
            f'display={display_kwh:.3f}, start_day={st.get("session_start_day_kwh")}, '
            f'integrated={st.get("session_integrated_kwh")}, timer={compute_duration_text(plugin, st.get("session_start_ts"))}',
            'session',
        )

def ensure_session_tracking(plugin, st, values, session, session_active, total_kwh, day_kwh=0.0, api_session_kwh=None, power_w=0, cid=''):
    """Keep session clock/baseline when session_active persisted without start metadata."""
    if not session_active:
        return
    api_start_ts = session_start_timestamp(plugin, values, session)
    if st.get('session_start_ts') is None:
        st['session_start_ts'] = api_start_ts if api_start_ts is not None else easee_state.now_ts(plugin)
    elif api_start_ts is not None:
        st['session_start_ts'] = api_start_ts
    if st.get('session_start_kwh') is None:
        st['session_start_kwh'] = total_kwh
    ensure_session_start_day_kwh(
        plugin, st, day_kwh, api_session_kwh=api_session_kwh, power_w=power_w,
        start_ts=api_start_ts if api_start_ts is not None else st.get('session_start_ts'),
        cid=cid,
    )

def resolve_session_kwh(plugin, st, session_active, api_session_kwh, total_kwh, power_w, day_kwh=0.0):
    """Session kWh: sessionEnergy → day_track delta → lifetime delta → power×time."""
    if not session_active:
        return easee_helpers.safe_float(plugin, st.get('last_session_kwh', 0.0), 0.0)
    if api_session_kwh is not None and float(api_session_kwh) > 0:
        st['session_integrated_kwh'] = float(api_session_kwh)
        return float(api_session_kwh)
    start_day = st.get('session_start_day_kwh')
    if start_day is not None:
        day_session = max(0.0, float(day_kwh) - float(start_day))
        if day_session > 0:
            st['session_integrated_kwh'] = day_session
            return day_session
    start_kwh = st.get('session_start_kwh')
    if start_kwh is not None:
        lifetime_delta = max(0.0, float(total_kwh) - float(start_kwh))
        if lifetime_delta > 0:
            st['session_integrated_kwh'] = lifetime_delta
            return lifetime_delta
    if power_w > 50:
        prev = easee_helpers.safe_float(plugin, st.get('session_integrated_kwh', 0.0), 0.0)
        integrated = round(prev + power_integrated_kwh(plugin, power_w), 6)
        st['session_integrated_kwh'] = integrated
        if integrated > 0:
            return integrated
        elapsed_h = session_elapsed_hours(plugin, st.get('session_start_ts'))
        est = estimate_session_kwh_from_power(power_w, elapsed_h)
        if est > 0:
            st['session_integrated_kwh'] = est
            return est
    return easee_helpers.safe_float(plugin, st.get('session_integrated_kwh', 0.0), 0.0)

    # ---- discovery ----

def discover_chargers(plugin):
    chargers = []
    flt = domoticz_runtime.Parameters.get('Mode5', '').strip().lower()
    try:
        data = easee_api.api_get(plugin, '/chargers')
        if data is None:
            if plugin.chargers:
                easee_logging.warning(
                    'charger_logic',
                    'Discovery chargers mislukt (geen API-data) — vorige cache behouden',
                    'discovery',
                )
                return list(plugin.chargers)
            return []
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
        easee_logging.warning('charger_logic', f'Discovery chargers mislukt: {e}', 'discovery')
        if plugin.chargers:
            return list(plugin.chargers)
    return sorted({c['id']: c for c in chargers}.values(), key=lambda x: x['id'])

def poll_charger(plugin, charger):
    cid = charger['id']
    values = {}
    session = {}
    ongoing_fetched = False
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
        ongoing_fetched = True
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
    api_session_kwh = session_energy_kwh(plugin, values, session, ongoing_fetched=ongoing_fetched)

    st = easee_state.charger_state(plugin, cid)
    prev_total = st.get('prev_total_kwh')
    counter_wh, day_kwh, day_delta = sync_day_energy(plugin, st, total_kwh, session_active, power_w)

    resuming = False
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
            ensure_session_start_day_kwh(
                plugin, st, day_kwh, api_session_kwh=api_session_kwh, power_w=power_w,
                start_ts=st.get('session_start_ts'), cid=cid,
            )
            st['prev_session_kwh'] = None
        else:
            st['session_start_ts'] = api_start_ts if api_start_ts is not None else easee_state.now_ts(plugin)
            st['session_start_kwh'] = total_kwh
            ensure_session_start_day_kwh(
                plugin, st, day_kwh, api_session_kwh=api_session_kwh, power_w=power_w,
                start_ts=api_start_ts, cid=cid,
            )
            st['prev_session_kwh'] = None
            if st.get('session_start_day_kwh') is None or abs(float(day_kwh) - float(st.get('session_start_day_kwh'))) < 0.001:
                st['session_integrated_kwh'] = 0.0
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0
            st['cost_delta_warned'] = False
            st.pop('session_kwh_zero_warned', None)
            st['session_kwh_zero_polls'] = 0
    elif session_active:
        ensure_session_tracking(
            plugin, st, values, session, session_active, total_kwh,
            day_kwh=day_kwh, api_session_kwh=api_session_kwh, power_w=power_w, cid=cid,
        )

    ending_session = (not session_active) and st.get('session_active')

    delta_kwh, delta_source = delta_kwh_for_cost(
        plugin, session_active, api_session_kwh, st.get('prev_session_kwh'),
        total_kwh, prev_total, power_w, day_delta=day_delta,
    )
    if session_active and api_session_kwh is not None:
        prev_sess = st.get('prev_session_kwh')
        if prev_sess is not None and float(api_session_kwh) > float(prev_sess):
            st['prev_session_kwh'] = api_session_kwh
        elif prev_sess is None and not resuming and ongoing_fetched and session:
            st['prev_session_kwh'] = api_session_kwh

    if easee_helpers.tibber_enabled(plugin) and delta_kwh > 0:
        st['cost_delta_warned'] = False
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
        easee_state.track_global_charge(plugin, day_delta if day_delta > 0 else delta_kwh, add_total, session_active and power_w > 50)
        if st.get('session_active'):
            st['session_cost_total'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0) + add_total, 4)
            st['session_cost_energy'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0) + add_energy, 4)
            st['session_cost_tax'] = round(easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0) + add_tax, 4)

    if ending_session:
        if api_session_kwh is not None and float(api_session_kwh) > 0:
            st['last_session_kwh'] = float(api_session_kwh)
        elif st.get('session_start_day_kwh') is not None:
            st['last_session_kwh'] = max(0.0, float(day_kwh) - float(st.get('session_start_day_kwh')))
        elif st.get('session_start_kwh') is not None:
            st['last_session_kwh'] = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
        elif easee_helpers.safe_float(plugin, st.get('session_integrated_kwh'), 0.0) > 0:
            st['last_session_kwh'] = st['session_integrated_kwh']
        st['last_session_cost_total'] = easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0)
        st['last_session_cost_energy'] = easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0)
        st['last_session_cost_tax'] = easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0)
        st['last_session_duration'] = compute_duration_text(plugin, st.get('session_start_ts'))
        st['session_active'] = False
        st['session_start_ts'] = None
        st['session_start_kwh'] = None
        st['session_start_day_kwh'] = None
        st['prev_session_kwh'] = None
        st['session_integrated_kwh'] = 0.0
        st['session_cost_total'] = 0.0
        st['session_cost_energy'] = 0.0
        st['session_cost_tax'] = 0.0
        st.pop('session_kwh_zero_warned', None)
        st['session_kwh_zero_polls'] = 0

    tracking_active = session_active and bool(st.get('session_active'))
    if tracking_active:
        unstick_session_day_baseline(
            plugin, st, day_kwh, power_w, api_session_kwh=api_session_kwh, cid=cid,
            force=abs(float(day_kwh) - float(st.get('session_start_day_kwh') or -1)) < 0.001,
        )

    session_kwh = resolve_session_kwh(
        plugin, st, tracking_active, api_session_kwh, total_kwh, power_w, day_kwh=day_kwh,
    )

    display_kwh = display_session_kwh(
        plugin, st, session_kwh, day_kwh, power_w, tracking_active, api_session_kwh=api_session_kwh,
    )
    track_session_kwh_zero_polls(
        plugin, st, display_kwh, day_kwh, power_w, tracking_active, cid=cid,
    )
    if (
        tracking_active and power_w > 50
        and int(round(float(display_kwh))) == 0 and float(day_kwh) > 0.05
        and easee_helpers.safe_int(plugin, st.get('session_kwh_zero_polls', 0), 0) == 1
    ):
        easee_logging.info(
            'charger_logic',
            f'Sessie-kWh=0 terwijl day_kwh={day_kwh:.3f} en laden ({power_w}W) lader {cid}: '
            f'start_day={st.get("session_start_day_kwh")}, integrated={st.get("session_integrated_kwh")}, '
            f'api_session={api_session_kwh}, timer={compute_duration_text(plugin, st.get("session_start_ts"))}',
            'session',
        )
    if st.get('session_active'):
        laadduur = compute_duration_text(plugin, st.get('session_start_ts'))
        session_cost = easee_helpers.safe_float(plugin, st.get('session_cost_total', 0.0), 0.0)
        session_cost_energy = easee_helpers.safe_float(plugin, st.get('session_cost_energy', 0.0), 0.0)
        session_cost_tax = easee_helpers.safe_float(plugin, st.get('session_cost_tax', 0.0), 0.0)
    else:
        laadduur = st.get('last_session_duration', '00:00')
        session_cost = easee_helpers.safe_float(plugin, st.get('last_session_cost_total', 0.0), 0.0)
        session_cost_energy = easee_helpers.safe_float(plugin, st.get('last_session_cost_energy', 0.0), 0.0)
        session_cost_tax = easee_helpers.safe_float(plugin, st.get('last_session_cost_tax', 0.0), 0.0)

    st['prev_total_kwh'] = total_kwh

    if easee_helpers.tibber_enabled(plugin) and session_active and power_w > 50 and delta_kwh <= 0:
        if not st.get('cost_delta_warned'):
            st['cost_delta_warned'] = True
            easee_logging.warning(
                'charger_logic',
                f'Kosten overgeslagen lader {cid}: delta=0 ({power_w}W, sessionEnergy={api_session_kwh}, '
                f'day_delta={day_delta:.6f}, prev_session={st.get("prev_session_kwh")})',
                'cost',
            )

    # UPDATE DEVICES
    domoticz_devices.update_charger_energy(plugin, cid, 'Laden', power_w, counter_wh)

    totaal_sessie = (
        f'🔋 Deze sessie: {display_kwh:.3f} kWh | 📅 Vandaag: {day_kwh:.3f} kWh'
        f' | Totaal: {total_kwh:.1f} kWh'
    )
    domoticz_devices.update_charger_custom(
        plugin, cid, 'Totaal & Sessie', totaal_sessie,
        nvalue=display_kwh,
    )

    eq_lb = any(bool(v.get('loadbal')) for v in (plugin.latest_equalizers or {}).values())
    hint = tibber_pricing.charging_hint(plugin, power_w, session_active, eq_lb_active=eq_lb)
    hint_part = f' | 💡 {hint}' if hint else ''
    status_text = (
        f'{status_emoji(plugin, online, session_active)} '
        f'{power_emoji(plugin, power_w)} {status_label} | ⏱️ {laadduur}{hint_part}'
    )
    domoticz_devices.update_charger_text(plugin, cid, 'Status', status_text)
    
    if easee_helpers.tibber_enabled(plugin):
        day_cost = easee_helpers.safe_float(plugin, st.get('day_cost_total', 0.0), 0.0)
        domoticz_devices.update_charger_costs(plugin, cid, session_cost, day_cost, session_kwh, session_active)
    
    plugin.latest_chargers[cid] = {
        'power': power_w,
        'kwh': total_kwh,
        'wh': counter_wh,
        'counter_wh': counter_wh,
        'day_wh': int(round(day_kwh * 1000.0)),
        'day_kwh': day_kwh,
        'day_cost': easee_helpers.safe_float(plugin, st.get('day_cost_total', 0.0), 0.0),
        'day_energy_cost': easee_helpers.safe_float(plugin, st.get('day_cost_energy', 0.0), 0.0),
        'day_tax_cost': easee_helpers.safe_float(plugin, st.get('day_cost_tax', 0.0), 0.0),
        'online': online,
    }
