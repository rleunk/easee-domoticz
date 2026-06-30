# -*- coding: utf-8 -*-

from datetime import datetime

import easee_helpers
import tibber_pricing
from pricing.base import PricingProvider


class TibberPricingProvider(PricingProvider):
    """Delegates to existing tibber_pricing module."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'Tibber'

    def is_available(self) -> bool:
        return bool(easee_helpers.tibber_token(self.plugin))

    def get_current_price(self) -> dict:
        return tibber_pricing.current_tibber_price(self.plugin)

    def get_today_prices(self) -> list:
        return tibber_pricing.sorted_price_points(self.plugin, today_only=True)

    def get_tomorrow_prices(self) -> list:
        points = tibber_pricing.sorted_price_points(self.plugin)
        today = datetime.now().astimezone().date()
        return [p for p in points if p[0].date() > today]

    def refresh(self) -> None:
        tibber_pricing.refresh_tibber_prices(self.plugin)
