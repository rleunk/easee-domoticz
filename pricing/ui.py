# -*- coding: utf-8 -*-

"""Provider-aware pricing UI helpers — use instead of direct tibber_pricing imports."""

import easee_helpers
import tibber_pricing
from pricing import entsoe as entsoe_pricing
from pricing import energyzero as energyzero_pricing
from pricing.factory import get_provider


def current_price(plugin) -> dict:
    return get_provider(plugin).get_current_price()


def price_status_emoji(plugin) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Handmatig':
        tariff_type = easee_helpers.manual_tariff_type(plugin)
        if tariff_type == 'Vast':
            return '🟡'
        period = easee_helpers.manual_tariff_period(plugin)
        if period == 'dal':
            return '🟢'
        if period == 'piek':
            return '🔴'
        return '🟡'
    if source == 'Geen' or not easee_helpers.pricing_enabled(plugin):
        return '⚪'
    if source == 'ENTSO-E':
        return entsoe_pricing.price_status_emoji(plugin)
    if source == 'EnergyZero':
        return energyzero_pricing.price_status_emoji(plugin)
    return tibber_pricing.price_status_emoji(plugin)


def price_emoji(plugin, price_total, cache=None):
    source = easee_helpers.pricing_source(plugin)
    if source == 'Handmatig':
        if easee_helpers.manual_tariff_type(plugin) == 'Vast':
            return '🟡'
        dal = easee_helpers.manual_dal_rate(plugin)
        piek = easee_helpers.manual_piek_rate(plugin)
        total = easee_helpers.safe_float(plugin, price_total, 0.0)
        if abs(total - dal) < 0.0001:
            return '🟢'
        if abs(total - piek) < 0.0001:
            return '🔴'
        return '🟡'
    if source == 'Geen':
        return '⚪'
    if cache is None:
        cache = plugin.state.get('price_cache') or {}
    if source == 'ENTSO-E':
        return entsoe_pricing.price_emoji(plugin, price_total, cache)
    if source == 'EnergyZero':
        return energyzero_pricing.price_emoji(plugin, price_total, cache)
    return tibber_pricing.price_emoji(plugin, price_total, cache)


def cheapest_window_text(plugin, hours=None) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return '—'
    if source == 'Handmatig':
        provider = get_provider(plugin)
        return provider.cheapest_window_text(hours=hours)
    if source == 'ENTSO-E':
        return entsoe_pricing.cheapest_window_text(plugin, hours=hours)
    if source == 'EnergyZero':
        return energyzero_pricing.cheapest_window_text(plugin, hours=hours)
    return tibber_pricing.cheapest_window_text(plugin, hours=hours)


def dagrapport_cheapest_line(plugin) -> str:
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return ''
    if source == 'Handmatig':
        provider = get_provider(plugin)
        return provider.dagrapport_cheapest_line()
    if source == 'ENTSO-E':
        return entsoe_pricing.dagrapport_cheapest_line(plugin)
    if source == 'EnergyZero':
        return energyzero_pricing.dagrapport_cheapest_line(plugin)
    return tibber_pricing.dagrapport_cheapest_line(plugin)


def status_prijsbron_part(plugin) -> str:
    """Leading ' | ...' fragment for Status tile — all five Prijsbron (Mode9) values."""
    source = easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return ' | Prijsbron: Geen'
    if source == 'Tibber':
        if easee_helpers.pricing_enabled(plugin):
            return ' | Tibber actief'
        return ' | Prijsbron: Tibber'
    if source == 'ENTSO-E':
        if easee_helpers.pricing_enabled(plugin):
            rate = easee_helpers.safe_float(plugin, current_price(plugin).get('total'), 0.0)
            return f' | ENTSO-E spot €{easee_helpers.euro_str(plugin, rate)}/kWh'
        return ' | Prijsbron: ENTSO-E'
    if source == 'EnergyZero':
        rate = easee_helpers.safe_float(plugin, current_price(plugin).get('total'), 0.0)
        return f' | EnergyZero €{easee_helpers.euro_str(plugin, rate)}/kWh'
    if source == 'Handmatig':
        tariff_type = easee_helpers.manual_tariff_type(plugin)
        if tariff_type == 'Vast':
            rate = easee_helpers.manual_rate(plugin)
            return f' | Handmatig €{easee_helpers.euro_str(plugin, rate)}/kWh'
        rate = easee_helpers.manual_rate_at(plugin)
        period = easee_helpers.manual_tariff_period(plugin)
        return (
            f' | Handmatig {tariff_type.lower()} ({period}) '
            f'€{easee_helpers.euro_str(plugin, rate)}/kWh'
        )
    return ''


def charging_hint(plugin, power_w, session_active=False, eq_lb_active=False, lb_active=None) -> str:
    hints = []
    if easee_helpers.tibber_enabled(plugin):
        tibber_hint = tibber_pricing.charging_hint(
            plugin, power_w, session_active, eq_lb_active=eq_lb_active, lb_active=lb_active,
        )
        if tibber_hint:
            hints.append(tibber_hint)
    elif easee_helpers.entsoe_enabled(plugin):
        entsoe_hint = entsoe_pricing.charging_hint(
            plugin, power_w, session_active, eq_lb_active=eq_lb_active, lb_active=lb_active,
        )
        if entsoe_hint:
            hints.append(entsoe_hint)
    elif easee_helpers.energyzero_enabled(plugin):
        energyzero_hint = energyzero_pricing.charging_hint(
            plugin, power_w, session_active, eq_lb_active=eq_lb_active, lb_active=lb_active,
        )
        if energyzero_hint:
            hints.append(energyzero_hint)
    if session_active and power_w > 50:
        import domoticz_energy_hints
        energy_hint = domoticz_energy_hints.charging_context_hint(
            plugin, power_w, session_active=session_active,
        )
        if energy_hint:
            hints.append(energy_hint)
    return ' · '.join(hints)
