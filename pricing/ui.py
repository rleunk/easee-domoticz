# -*- coding: utf-8 -*-

"""Provider-aware pricing UI helpers — use instead of direct tibber_pricing imports."""

import easee_helpers
import tibber_pricing
from pricing.factory import get_provider


def current_price(plugin) -> dict:
    return get_provider(plugin).get_current_price()


def price_status_emoji(plugin) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Handmatig':
        return '🟡'
    if source == 'Geen' or not easee_helpers.pricing_enabled(plugin):
        return '⚪'
    return tibber_pricing.price_status_emoji(plugin)


def price_emoji(plugin, price_total, cache=None):
    source = easee_helpers.pricing_source(plugin)
    if source == 'Handmatig':
        return '🟡'
    if source == 'Geen':
        return '⚪'
    if cache is None:
        cache = plugin.state.get('price_cache') or {}
    return tibber_pricing.price_emoji(plugin, price_total, cache)


def cheapest_window_text(plugin, hours=None) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return '—'
    if source == 'Handmatig':
        rate = easee_helpers.manual_rate(plugin)
        return f'Vast tarief €{rate:.2f}/kWh'
    return tibber_pricing.cheapest_window_text(plugin, hours=hours)


def dagrapport_cheapest_line(plugin) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return ''
    if source == 'Handmatig':
        rate = easee_helpers.manual_rate(plugin)
        return f'Vast tarief €{rate:.2f}/kWh'
    return tibber_pricing.dagrapport_cheapest_line(plugin)


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None) -> str:
    if not easee_helpers.tibber_enabled(plugin):
        return ''
    return tibber_pricing.charging_hint(
        plugin, power_w, session_active, eq_lb_active=eq_lb_active, lb_active=lb_active,
    )
