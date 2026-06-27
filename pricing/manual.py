# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import easee_helpers
import easee_state
from pricing.base import PricingProvider


class ManualPricingProvider(PricingProvider):
    """Fixed manual €/kWh rate (Mode10)."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'Handmatig'

    def is_available(self) -> bool:
        return easee_helpers.pricing_source(self.plugin) == 'Handmatig'

    def _rate(self) -> float:
        return easee_helpers.manual_rate(self.plugin)

    def _price_dict(self) -> dict:
        rate = self._rate()
        return {'total': rate, 'energy': rate, 'tax': 0.0, 'currency': 'EUR'}

    def get_current_price(self) -> dict:
        out = self._price_dict()
        out['startsAt'] = datetime.now().astimezone().isoformat()
        return out

    def _hourly_points(self, today_only=False, tomorrow_only=False):
        rate = self._rate()
        price = {'total': rate, 'energy': rate, 'tax': 0.0}
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        points = []
        for day_offset in (0, 1):
            day = (now + timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            if today_only and day.date() != today:
                continue
            if tomorrow_only and day.date() != tomorrow:
                continue
            for hour in range(24):
                dt = day + timedelta(hours=hour)
                points.append((dt, rate, dict(price)))
        points.sort(key=lambda x: x[0])
        return points

    def get_today_prices(self) -> list:
        return self._hourly_points(today_only=True)

    def get_tomorrow_prices(self) -> list:
        return self._hourly_points(tomorrow_only=True)

    def refresh(self) -> None:
        rate = self._rate()
        cache = {}
        now = datetime.now().astimezone()
        for day_offset in (0, 1):
            day = (now + timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            for hour in range(24):
                dt = day + timedelta(hours=hour)
                cache[dt.isoformat()] = {'total': rate, 'energy': rate, 'tax': 0.0}
        self.plugin.state['price_cache'] = cache
        self.plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(self.plugin))
        self.plugin.state['price_resolution'] = 'HOURLY'
        self.plugin.state['currency'] = 'EUR'
