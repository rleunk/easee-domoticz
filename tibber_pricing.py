# -*- coding: utf-8 -*-

from datetime import datetime
import Domoticz
from easee_constants import TIBBER_GQL
from easee_api_keys import TIBBER_KEYS
import easee_logging
import easee_helpers
import easee_state

def tibber_query(plugin, query):
    token = easee_helpers.tibber_token(plugin)
    if not token:
        return None
    try:
        r = plugin.session.post(TIBBER_GQL, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json={'query': query}, timeout=20)
        if r.status_code == 200:
            return r.json()
        easee_logging.debug('tibber_pricing', f'tibber query http {r.status_code}: {r.text[:300]}')
    except Exception as e:
        easee_logging.debug('tibber_pricing', f'tibber query failed: {e}')
    return None

def refresh_tibber_prices(plugin):
    if not easee_helpers.tibber_enabled(plugin):
        plugin.state['price_cache'] = {}
        plugin.state['currency'] = 'EUR'
        return
    query = '{ viewer { homes { id currentSubscription { priceInfo { current { total energy tax currency startsAt } today { total energy tax startsAt } tomorrow { total energy tax startsAt } } } } } }'
    result = tibber_query(plugin, query)
    if not result:
        return
    try:
        homes = (((result or {}).get('data') or {}).get('viewer') or {}).get('homes') or []
        if not homes:
            return
        info = ((((homes[0] or {}).get('currentSubscription') or {}).get('priceInfo')) or {})
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
        plugin.state['price_cache'] = cache
        plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(plugin))
    except Exception as e:
        easee_logging.debug('tibber_pricing', f'parse tibber prices failed: {e}')

def current_tibber_price(plugin):
    cache = plugin.state.get('price_cache') or {}
    if not cache:
        return {'total':0.0,'energy':0.0,'tax':0.0,'currency': plugin.state.get('currency','EUR')}
    now = datetime.now().astimezone()
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
    out['currency'] = plugin.state.get('currency','EUR')
    out['startsAt'] = best_start
    return out

def price_status_emoji(plugin):
    cache = plugin.state.get('price_cache') or {}
    current = current_tibber_price(plugin)
    cur = easee_helpers.safe_float(plugin, current.get('total'), 0.0)
    return price_emoji(plugin, cur, cache)

def cheapest_window_text(plugin, hours=3):
    cache = plugin.state.get('price_cache') or {}
    points = []
    for start_s, data in cache.items():
        dt = easee_helpers.parse_iso(plugin, start_s)
        if dt is None:
            continue
        points.append((dt, easee_helpers.safe_float(plugin, data.get('total'),0.0)))
    points.sort(key=lambda x: x[0])
    if len(points) < hours:
        return 'Onvoldoende prijsdata'
    best_idx = None
    best_avg = None
    for i in range(0, len(points)-hours+1):
        avg = sum(p[1] for p in points[i:i+hours]) / float(hours)
        if best_avg is None or avg < best_avg:
            best_avg = avg
            best_idx = i
    if best_idx is None:
        return 'Onvoldoende prijsdata'
    start = points[best_idx][0]
    end = points[best_idx+hours-1][0]
    return f'{start.strftime("%H:%M")} - {end.strftime("%H:%M")} | €{best_avg:.2f}/kWh'

    # ---- charger state ----

def price_emoji(plugin, price_total, cache):
    """Emoji for price level"""
    if not cache:
        return '⚪'
    prices = sorted(easee_helpers.safe_float(plugin, v.get('total'), 0.0) for v in cache.values() if isinstance(v, dict))
    if len(prices) < 3:
        return '⚪'
    lo = prices[max(0, int(len(prices)*0.33)-1)]
    hi = prices[max(0, int(len(prices)*0.66)-1)]
    if price_total <= lo:
        return '🟢'
    if price_total >= hi:
        return '🔴'
    return '🟡'

    # ---- state ----
