# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import easee_helpers
import easee_logging
import easee_state
from pricing.base import PricingProvider
from pricing.entsoe import (
    cheapest_window_text,
    current_entsoe_price,
    dagrapport_cheapest_line,
    price_emoji,
    price_status_emoji,
    price_tier,
    sorted_price_points,
)


def _reading_date_local(plugin, reading_date):
    """EnergyZero timestamps use local wall-clock hours with a Z suffix."""
    if not reading_date:
        return None
    text = str(reading_date).replace('Z', '')
    try:
        naive = datetime.fromisoformat(text)
    except ValueError:
        return easee_helpers.parse_iso(plugin, reading_date)
    local_tz = datetime.now().astimezone().tzinfo
    return naive.replace(tzinfo=local_tz)


def _price_from_api(plugin, price_eur_kwh):
    """All-in price (inclBtw=true): no energy/tax split available."""
    total = easee_helpers.safe_float(plugin, price_eur_kwh, 0.0)
    return {'total': total, 'energy': total, 'tax': 0.0}


def _parse_energyzero_json(plugin, data):
    cache = {}
    for node in (data.get('Prices') or []):
        reading_date = node.get('readingDate')
        price = node.get('price')
        if not reading_date or price is None:
            continue
        slot_start = _reading_date_local(plugin, reading_date)
        if slot_start is None:
            continue
        cache[slot_start.isoformat()] = _price_from_api(plugin, price)
    return cache


def energyzero_query(plugin, from_date, till_date):
    from easee_constants import ENERGYZERO_API_URL
    if not plugin.session:
        return None
    params = {
        'fromDate': from_date,
        'tillDate': till_date,
        'interval': 4,
        'usageType': 1,
        'inclBtw': 'true',
    }
    try:
        r = plugin.session.get(ENERGYZERO_API_URL, params=params, timeout=30)
        if r.status_code == 200 and r.text.strip():
            return r.json()
        easee_logging.debug(
            'energyzero',
            f'EnergyZero http {r.status_code}: {(r.text or "")[:300]}',
        )
    except Exception as e:
        easee_logging.debug('energyzero', f'EnergyZero query failed: {e}')
    return None


def refresh_energyzero_prices(plugin):
    if not easee_helpers.energyzero_enabled(plugin):
        plugin.state['price_cache'] = {}
        plugin.state['currency'] = 'EUR'
        plugin.state.pop('price_resolution', None)
        return
    today = datetime.now().astimezone().date()
    from_date = f'{today.isoformat()}T00:00:00.000Z'
    till_date = f'{(today + timedelta(days=2)).isoformat()}T00:00:00.000Z'
    data = energyzero_query(plugin, from_date, till_date)
    if not data:
        return
    cache = _parse_energyzero_json(plugin, data)
    if not cache:
        return
    plugin.state['price_cache'] = cache
    plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(plugin))
    plugin.state['price_resolution'] = 'HOURLY'
    plugin.state['currency'] = 'EUR'
    easee_logging.debug(
        'energyzero',
        f'EnergyZero prijzen geladen: {len(cache)} uur-slots',
        'cost',
    )


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None):
    if lb_active is not None:
        eq_lb_active = lb_active
    if not session_active or power_w <= 50 or not easee_helpers.energyzero_enabled(plugin):
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


class EnergyZeroPricingProvider(PricingProvider):
    """EnergyZero public API — hourly NL prices, no token."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'EnergyZero'

    def is_available(self) -> bool:
        return easee_helpers.energyzero_enabled(self.plugin)

    def get_current_price(self) -> dict:
        return current_entsoe_price(self.plugin)

    def get_today_prices(self) -> list:
        return sorted_price_points(self.plugin, today_only=True)

    def get_tomorrow_prices(self) -> list:
        points = sorted_price_points(self.plugin)
        today = datetime.now().astimezone().date()
        return [p for p in points if p[0].date() > today]

    def refresh(self) -> None:
        refresh_energyzero_prices(self.plugin)
