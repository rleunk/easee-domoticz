# -*- coding: utf-8 -*-

from pricing.base import PricingProvider


class NoPricingProvider(PricingProvider):
    """No pricing source — costs disabled."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'Geen'

    def is_available(self) -> bool:
        return False

    def get_current_price(self) -> dict:
        return {'total': 0.0, 'energy': 0.0, 'tax': 0.0, 'currency': 'EUR'}

    def get_today_prices(self) -> list:
        return []

    def get_tomorrow_prices(self) -> list:
        return []
