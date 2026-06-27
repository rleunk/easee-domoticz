# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from xml.etree import ElementTree

import easee_helpers
import easee_logging
import easee_state
from pricing.base import PricingProvider


def _local_tag(tag):
    return tag.split('}')[-1] if '}' in tag else tag


def _entsoe_period_fmt(dt):
    """Aware datetime → yyyyMMddHHmm UTC for ENTSO-E API."""
    from datetime import timezone
    return dt.astimezone(timezone.utc).strftime('%Y%m%d%H%M')


def _spot_to_consumer_price(plugin, spot_eur_kwh):
    """All-in consumer estimate: spot + surcharges + BTW."""
    opslag = easee_helpers.entsoe_opslag(plugin)
    belasting = easee_helpers.entsoe_energiebelasting(plugin)
    btw_pct = easee_helpers.entsoe_btw_pct(plugin)
    subtotal = spot_eur_kwh + opslag + belasting
    total = subtotal * (1.0 + btw_pct / 100.0)
    energy = spot_eur_kwh
    tax = total - energy
    return {'total': total, 'energy': energy, 'tax': tax}


def _parse_resolution_minutes(resolution_text):
    if not resolution_text:
        return 60
    text = str(resolution_text).upper()
    if text.startswith('PT') and text.endswith('M'):
        try:
            return int(text[2:-1])
        except ValueError:
            return 60
    return 60


def _parse_entsoe_xml(plugin, xml_text):
    """Parse A44 day-ahead XML → {iso_start: price_dict}."""
    cache = {}
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as e:
        easee_logging.debug('entsoe', f'XML parse failed: {e}')
        return cache

    for ts in root.iter():
        if _local_tag(ts.tag) != 'TimeSeries':
            continue
        for child in ts:
            if _local_tag(child.tag) != 'Period':
                continue
            period_start = None
            resolution_min = 60
            for pc in child:
                ltag = _local_tag(pc.tag)
                if ltag == 'timeInterval':
                    for ti in pc:
                        if _local_tag(ti.tag) == 'start' and ti.text:
                            period_start = easee_helpers.parse_iso(plugin, ti.text.strip())
                elif ltag == 'resolution':
                    resolution_min = _parse_resolution_minutes(pc.text)
            if period_start is None:
                continue
            for pc in child:
                if _local_tag(pc.tag) != 'Point':
                    continue
                position = None
                amount = None
                for pt in pc:
                    ltag = _local_tag(pt.tag)
                    if ltag == 'position' and pt.text:
                        position = int(pt.text)
                    elif ltag == 'price.amount' and pt.text:
                        amount = easee_helpers.safe_float(plugin, pt.text, None)
                if position is None or amount is None:
                    continue
                slot_start = period_start + timedelta(minutes=resolution_min * (position - 1))
                spot_kwh = amount / 1000.0
                price = _spot_to_consumer_price(plugin, spot_kwh)
                cache[slot_start.isoformat()] = price
    return cache


def entsoe_query(plugin, period_start, period_end):
    from easee_constants import ENTSOE_API_URL, ENTSOE_DOC_TYPE, ENTSOE_NL_DOMAIN
    token = easee_helpers.entsoe_token(plugin)
    if not token or not plugin.session:
        return None
    params = {
        'securityToken': token,
        'documentType': ENTSOE_DOC_TYPE,
        'in_Domain': ENTSOE_NL_DOMAIN,
        'out_Domain': ENTSOE_NL_DOMAIN,
        'periodStart': _entsoe_period_fmt(period_start),
        'periodEnd': _entsoe_period_fmt(period_end),
    }
    try:
        r = plugin.session.get(ENTSOE_API_URL, params=params, timeout=30)
        if r.status_code == 200 and r.text.strip():
            return r.text
        easee_logging.debug(
            'entsoe',
            f'ENTSO-E http {r.status_code}: {(r.text or "")[:300]}',
        )
    except Exception as e:
        easee_logging.debug('entsoe', f'ENTSO-E query failed: {e}')
    return None


def refresh_entsoe_prices(plugin):
    if not easee_helpers.entsoe_enabled(plugin):
        plugin.state['price_cache'] = {}
        plugin.state['currency'] = 'EUR'
        plugin.state.pop('price_resolution', None)
        return
    now_local = datetime.now().astimezone()
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = today_start + timedelta(days=2)
    xml_text = entsoe_query(plugin, today_start, period_end)
    if not xml_text:
        return
    cache = _parse_entsoe_xml(plugin, xml_text)
    if not cache:
        return
    plugin.state['price_cache'] = cache
    plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(plugin))
    plugin.state['price_resolution'] = 'HOURLY'
    plugin.state['currency'] = 'EUR'
    easee_logging.debug(
        'entsoe',
        f'ENTSO-E prijzen geladen: {len(cache)} uur-slots',
        'cost',
    )


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


def normalize_price_parts(plugin, price):
    if not isinstance(price, dict):
        return {'total': 0.0, 'energy': 0.0, 'tax': 0.0}
    out = dict(price)
    total = easee_helpers.safe_float(plugin, out.get('total'), 0.0)
    energy = easee_helpers.safe_float(plugin, out.get('energy'), 0.0)
    tax = easee_helpers.safe_float(plugin, out.get('tax'), 0.0)
    if total <= 0:
        return out
    if energy <= 0 and tax <= 0:
        out['energy'] = total
        out['tax'] = 0.0
    elif energy <= 0:
        out['energy'] = max(0.0, total - tax)
    elif tax <= 0:
        out['tax'] = max(0.0, total - energy)
    out['total'] = total
    return out


def current_entsoe_price(plugin):
    cache = plugin.state.get('price_cache') or {}
    if not cache:
        return {'total': 0.0, 'energy': 0.0, 'tax': 0.0, 'currency': 'EUR'}
    now = datetime.now().astimezone()
    points = sorted_price_points(plugin)
    if points:
        for dt, total, data in reversed(points):
            if (now - dt).total_seconds() >= 0 and (now - dt).total_seconds() < 3660:
                out = normalize_price_parts(plugin, dict(data))
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
    out = normalize_price_parts(plugin, dict(best or {}))
    out['currency'] = plugin.state.get('currency', 'EUR')
    out['startsAt'] = best_start
    return out


def price_tier(plugin, price_total, cache=None):
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


def price_emoji(plugin, price_total, cache):
    if not cache:
        return '⚪'
    tier = price_tier(plugin, price_total, cache)
    if tier == 'cheap':
        return '🟢'
    if tier == 'expensive':
        return '🔴'
    return '🟡'


def price_status_emoji(plugin):
    cache = plugin.state.get('price_cache') or {}
    current = current_entsoe_price(plugin)
    cur = easee_helpers.safe_float(plugin, current.get('total'), 0.0)
    return price_emoji(plugin, cur, cache)


def cheapest_hour_today(plugin):
    points = sorted_price_points(plugin, today_only=True)
    if not points:
        return None, None
    best = min(points, key=lambda p: p[1])
    return best[0].strftime('%H:%M'), best[1]


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
    window_slots = hours
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
    end_dt = points[best_idx + window_slots - 1][0] + timedelta(hours=1)
    return f'{start.strftime("%H:%M")} - {end_dt.strftime("%H:%M")} ({hours}u) | €{best_avg:.2f}/kWh'


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None):
    if lb_active is not None:
        eq_lb_active = lb_active
    if not session_active or power_w <= 50 or not easee_helpers.entsoe_enabled(plugin):
        return ''
    current = current_entsoe_price(plugin)
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


def surcharges_summary(plugin) -> str:
    """Human-readable surcharge config for startup log (no token)."""
    opslag = easee_helpers.entsoe_opslag(plugin)
    belasting = easee_helpers.entsoe_energiebelasting(plugin)
    btw = easee_helpers.entsoe_btw_pct(plugin)
    return (
        f'opslag €{opslag:.4f}/kWh, energiebelasting €{belasting:.4f}/kWh, BTW {btw:.0f}%'
    )


class EntsoePricingProvider(PricingProvider):
    """ENTSO-E day-ahead spot + configurable surcharges."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'ENTSO-E'

    def is_available(self) -> bool:
        return bool(easee_helpers.entsoe_token(self.plugin))

    def get_current_price(self) -> dict:
        return current_entsoe_price(self.plugin)

    def get_today_prices(self) -> list:
        return sorted_price_points(self.plugin, today_only=True)

    def get_tomorrow_prices(self) -> list:
        points = sorted_price_points(self.plugin)
        today = datetime.now().astimezone().date()
        return [p for p in points if p[0].date() > today]

    def refresh(self) -> None:
        refresh_entsoe_prices(self.plugin)
