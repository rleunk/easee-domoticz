# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import Domoticz
from easee_constants import TIBBER_GQL
from easee_api_keys import TIBBER_KEYS
import easee_logging
import easee_helpers
import easee_state

_TIBBER_QH_QUERY = (
    '{ viewer { homes { id currentSubscription { '
    'priceInfo(resolution: QUARTER_HOURLY) { '
    'current { total energy tax currency startsAt } '
    'today { total energy tax startsAt } '
    'tomorrow { total energy tax startsAt } '
    '} } } } }'
)
_TIBBER_HOURLY_QUERY = (
    '{ viewer { homes { id currentSubscription { priceInfo { '
    'current { total energy tax currency startsAt } '
    'today { total energy tax startsAt } '
    'tomorrow { total energy tax startsAt } '
    '} } } } }'
)


def tibber_query(plugin, query):
    token = easee_helpers.tibber_token(plugin)
    if not token:
        return None
    try:
        r = plugin.session.post(
            TIBBER_GQL,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'query': query},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()
        easee_logging.debug('tibber_pricing', f'tibber query http {r.status_code}: {r.text[:300]}')
    except Exception as e:
        easee_logging.debug('tibber_pricing', f'tibber query failed: {e}')
    return None


def _parse_price_cache(plugin, info):
    cache = {}
    curr = info.get(TIBBER_KEYS['bucket_current']) or {}
    total_k, energy_k, tax_k = TIBBER_KEYS['price']
    starts_at = TIBBER_KEYS['starts_at']
    currency_k = TIBBER_KEYS['currency']
    if curr.get(currency_k):
        plugin.state['currency'] = str(curr.get(currency_k))
    for bucket_name in TIBBER_KEYS['buckets']:
        for node in (info.get(bucket_name) or []):
            start = node.get(starts_at)
            total = node.get(total_k)
            if start and total is not None:
                cache[str(start)] = {
                    total_k: easee_helpers.safe_float(plugin, total, 0.0),
                    energy_k: easee_helpers.safe_float(plugin, node.get(energy_k), 0.0),
                    tax_k: easee_helpers.safe_float(plugin, node.get(tax_k), 0.0),
                }
    if curr.get(starts_at) and curr.get(total_k) is not None:
        cache[str(curr.get(starts_at))] = {
            total_k: easee_helpers.safe_float(plugin, curr.get(total_k), 0.0),
            energy_k: easee_helpers.safe_float(plugin, curr.get(energy_k), 0.0),
            tax_k: easee_helpers.safe_float(plugin, curr.get(tax_k), 0.0),
        }
    return cache


def refresh_tibber_prices(plugin):
    if not easee_helpers.tibber_enabled(plugin):
        plugin.state['price_cache'] = {}
        plugin.state['currency'] = 'EUR'
        plugin.state.pop('price_resolution', None)
        return
    result = tibber_query(plugin, _TIBBER_QH_QUERY)
    resolution = 'QUARTER_HOURLY'
    if not result:
        result = tibber_query(plugin, _TIBBER_HOURLY_QUERY)
        resolution = 'HOURLY'
    if not result:
        return
    try:
        homes = (((result or {}).get('data') or {}).get('viewer') or {}).get('homes') or []
        if not homes:
            return
        info = ((((homes[0] or {}).get('currentSubscription') or {}).get('priceInfo')) or {})
        cache = _parse_price_cache(plugin, info)
        if not cache:
            return
        plugin.state['price_cache'] = cache
        plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(plugin))
        plugin.state['price_resolution'] = resolution
        easee_logging.debug(
            'tibber_pricing',
            f'Tibber prijzen geladen: {len(cache)} slots ({resolution})',
            'cost',
        )
    except Exception as e:
        easee_logging.debug('tibber_pricing', f'parse tibber prices failed: {e}')


def sorted_price_points(plugin, today_only=False):
    cache = plugin.state.get('price_cache') or {}
    points = []
    today = datetime.now().astimezone().date()
    for start_s, data in cache.items():
        dt = easee_helpers.parse_iso(plugin, start_s)
        if dt is None:
            continue
        if today_only and dt.date() != today:
            continue
        points.append((dt, easee_helpers.safe_float(plugin, data.get('total'), 0.0), data))
    points.sort(key=lambda x: x[0])
    return points


def _slot_interval_sec(plugin, points):
    if len(points) < 2:
        res = plugin.state.get('price_resolution', 'HOURLY')
        return 900 if res == 'QUARTER_HOURLY' else 3600
    deltas = []
    for i in range(1, min(len(points), 6)):
        d = (points[i][0] - points[i - 1][0]).total_seconds()
        if 600 <= d <= 3900:
            deltas.append(d)
    if not deltas:
        return 3600
    return int(round(sum(deltas) / len(deltas)))


def current_tibber_price(plugin):
    cache = plugin.state.get('price_cache') or {}
    if not cache:
        return {'total': 0.0, 'energy': 0.0, 'tax': 0.0, 'currency': plugin.state.get('currency', 'EUR')}
    now = datetime.now().astimezone()
    points = sorted_price_points(plugin)
    if points:
        interval = _slot_interval_sec(plugin, points)
        for dt, total, data in reversed(points):
            if (now - dt).total_seconds() >= 0 and (now - dt).total_seconds() < interval + 60:
                out = dict(data)
                out['currency'] = plugin.state.get('currency', 'EUR')
                out['startsAt'] = dt.isoformat()
                return out
    best = None
    best_delta = None
    best_start = None
    for start_s, data in cache.items():
        dt = easee_helpers.parse_iso(plugin, start_s)
        if dt is None:
            continue
        delta = (now - dt).total_seconds()
        if delta >= 0 and (best_delta is None or delta < best_delta):
            best_delta = delta
            best = data
            best_start = start_s
    if best is None:
        for start_s, data in cache.items():
            dt = easee_helpers.parse_iso(plugin, start_s)
            if dt is None:
                continue
            delta = abs((dt - now).total_seconds())
            if best_delta is None or delta < best_delta:
                best_delta = delta
                best = data
                best_start = start_s
    out = dict(best or {})
    out['currency'] = plugin.state.get('currency', 'EUR')
    out['startsAt'] = best_start
    return out


def price_status_emoji(plugin):
    cache = plugin.state.get('price_cache') or {}
    current = current_tibber_price(plugin)
    cur = easee_helpers.safe_float(plugin, current.get('total'), 0.0)
    return price_emoji(plugin, cur, cache)


def price_tier(plugin, price_total, cache=None):
    """Return 'cheap', 'normal', or 'expensive' relative to cached prices."""
    cache = cache if cache is not None else (plugin.state.get('price_cache') or {})
    if not cache:
        return 'normal'
    prices = sorted(
        easee_helpers.safe_float(plugin, v.get('total'), 0.0)
        for v in cache.values() if isinstance(v, dict)
    )
    if len(prices) < 3:
        return 'normal'
    lo = prices[max(0, int(len(prices) * 0.33) - 1)]
    hi = prices[max(0, int(len(prices) * 0.66) - 1)]
    if price_total <= lo:
        return 'cheap'
    if price_total >= hi:
        return 'expensive'
    return 'normal'


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None):
    """Infer charging context from power + Tibber price."""
    if lb_active is not None:
        eq_lb_active = lb_active
    if not session_active or power_w <= 50 or not easee_helpers.tibber_enabled(plugin):
        return ''
    current = current_tibber_price(plugin)
    cur = easee_helpers.safe_float(plugin, current.get('total'), 0.0)
    cache = plugin.state.get('price_cache') or {}
    tier = price_tier(plugin, cur, cache)
    if tier == 'expensive':
        return 'Laden bij duur tarief'
    if tier == 'cheap' and not eq_lb_active:
        return 'Waarschijnlijk Grid Rewards'
    if tier == 'cheap':
        return 'Laden bij goedkoop tarief'
    return ''


def dagrapport_cheapest_line(plugin):
    hour, price = cheapest_hour_today(plugin)
    if hour and price is not None:
        return f'Goedkoopste: {hour} (€{price:.2f}/kWh)'
    return 'Goedkoopste: onbekend'


def cheapest_window_text(plugin, hours=None):
    if hours is None:
        hours = easee_helpers.beste_laden_hours(plugin)
    hours = max(1, min(int(hours), 12))
    points = sorted_price_points(plugin)
    if not points:
        return 'Onvoldoende prijsdata'
    slot_sec = _slot_interval_sec(plugin, points)
    slots_per_hour = max(1, int(round(3600.0 / float(slot_sec))))
    window_slots = hours * slots_per_hour
    if len(points) < window_slots:
        return 'Onvoldoende prijsdata'
    best_idx = None
    best_avg = None
    for i in range(0, len(points) - window_slots + 1):
        avg = sum(p[1] for p in points[i:i + window_slots]) / float(window_slots)
        if best_avg is None or avg < best_avg:
            best_avg = avg
            best_idx = i
    if best_idx is None:
        return 'Onvoldoende prijsdata'
    start = points[best_idx][0]
    end_dt = points[best_idx + window_slots - 1][0] + timedelta(seconds=slot_sec)
    return f'{start.strftime("%H:%M")} - {end_dt.strftime("%H:%M")} ({hours}u) | €{best_avg:.2f}/kWh'


def cheapest_hour_today(plugin):
    """Return (HH:MM, price) for cheapest single slot today."""
    points = sorted_price_points(plugin, today_only=True)
    if not points:
        return None, None
    best = min(points, key=lambda p: p[1])
    return best[0].strftime('%H:%M'), best[1]


def price_emoji(plugin, price_total, cache):
    """Emoji for price level"""
    if not cache:
        return '⚪'
    tier = price_tier(plugin, price_total, cache)
    if tier == 'cheap':
        return '🟢'
    if tier == 'expensive':
        return '🔴'
    return '🟡'
