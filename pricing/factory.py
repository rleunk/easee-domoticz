# -*- coding: utf-8 -*-

import easee_helpers
from pricing.manual import ManualPricingProvider
from pricing.none import NoPricingProvider
from pricing.tibber import TibberPricingProvider


def get_provider(plugin, config=None):
    """Return pricing provider based on Prijsbron (Mode9) selection."""
    source = config if config is not None else easee_helpers.pricing_source(plugin)
    if source == 'Geen':
        return NoPricingProvider(plugin)
    if source == 'Handmatig':
        return ManualPricingProvider(plugin)
    return TibberPricingProvider(plugin)
