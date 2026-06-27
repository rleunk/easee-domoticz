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
        if easee_helpers.manual_tariff_type(plugin) == 'Dag/nacht':
            now_rate = easee_helpers.manual_rate_at(plugin)
            dal = easee_helpers.manual_dal_rate(plugin)
            if abs(now_rate - dal) < 0.0001:
                return '🟢'
            return '🟡'
        return '🟡'
    if source == 'Geen' or not easee_helpers.pricing_enabled(plugin):
        return '⚪'
    return tibber_pricing.price_status_emoji(plugin)


def price_emoji(plugin, price_total, cache=None):
    source = easee_helpers.pricing_source(plugin)
    if source == 'Handmatig':
        if easee_helpers.manual_tariff_type(plugin) == 'Vast':
            return '🟡'
        dal = easee_helpers.manual_dal_rate(plugin)
        if abs(easee_helpers.safe_float(plugin, price_total, 0.0) - dal) < 0.0001:
            return '🟢'
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
        provider = get_provider(plugin)
        return provider.cheapest_window_text(hours=hours)
    return tibber_pricing.cheapest_window_text(plugin, hours=hours)


def dagrapport_cheapest_line(plugin) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return ''
    if source == 'Handmatig':
        provider = get_provider(plugin)
        return provider.dagrapport_cheapest_line()
    return tibber_pricing.dagrapport_cheapest_line(plugin)


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None) -> str:
    if not easee_helpers.tibber_enabled(plugin):
        return ''
    return tibber_pricing.charging_hint(
        plugin, power_w, session_active, eq_lb_active=eq_lb_active, lb_active=lb_active,
    )
