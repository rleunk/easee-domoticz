# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import easee_helpers
import easee_state
from pricing.base import PricingProvider


class ManualPricingProvider(PricingProvider):
    """Manual €/kWh — vast, dag/nacht, or dal/piek (Mode10–Mode19)."""

    def __init__(self, plugin):
        self.plugin = plugin

    def provider_name(self) -> str:
        return 'Handmatig'

    def is_available(self) -> bool:
        return easee_helpers.pricing_source(self.plugin) == 'Handmatig'

    def _rate_at(self, dt=None) -> float:
        return easee_helpers.manual_rate_at(self.plugin, dt)

    def _price_dict(self, dt=None) -> dict:
        rate = self._rate_at(dt)
        return {'total': rate, 'energy': rate, 'tax': 0.0, 'currency': 'EUR'}

    def get_current_price(self) -> dict:
        now = datetime.now().astimezone()
        out = self._price_dict(now)
        out['startsAt'] = now.isoformat()
        return out

    def _hourly_points(self, today_only=False, tomorrow_only=False):
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
                rate = self._rate_at(dt)
                price = {'total': rate, 'energy': rate, 'tax': 0.0}
                points.append((dt, rate, dict(price)))
        points.sort(key=lambda x: x[0])
        return points

    def sorted_price_points(self, today_only=False, tomorrow_only=False):
        """(datetime, rate, price_dict) tuples for today and/or tomorrow."""
        return self._hourly_points(today_only=today_only, tomorrow_only=tomorrow_only)

    def get_today_prices(self) -> list:
        return self._hourly_points(today_only=True)

    def get_tomorrow_prices(self) -> list:
        return self._hourly_points(tomorrow_only=True)

    def cheapest_hour_today(self):
        points = self.sorted_price_points(today_only=True)
        if not points:
            return None, None
        best = min(points, key=lambda p: p[1])
        return best[0].strftime('%H:%M'), best[1]

    def cheapest_window_text(self, hours=None) -> str:
        if easee_helpers.manual_tariff_type(self.plugin) == 'Vast':
            rate = easee_helpers.manual_rate(self.plugin)
            return f'Vast tarief €{rate:.2f}/kWh'
        if hours is None:
            hours = easee_helpers.beste_laden_hours(self.plugin)
        hours = max(1, min(int(hours), 12))
        points = self.sorted_price_points()
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

    def dagrapport_cheapest_line(self) -> str:
        if easee_helpers.manual_tariff_type(self.plugin) == 'Vast':
            rate = easee_helpers.manual_rate(self.plugin)
            return f'Vast tarief €{rate:.2f}/kWh'
        hour, price = self.cheapest_hour_today()
        if hour and price is not None:
            return f'Goedkoopste: {hour} (€{price:.2f}/kWh)'
        return 'Goedkoopste: onbekend'

    def refresh(self) -> None:
        cache = {}
        now = datetime.now().astimezone()
        for day_offset in (0, 1):
            day = (now + timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            for hour in range(24):
                dt = day + timedelta(hours=hour)
                rate = self._rate_at(dt)
                cache[dt.isoformat()] = {'total': rate, 'energy': rate, 'tax': 0.0}
        self.plugin.state['price_cache'] = cache
        self.plugin.state['price_cache_refreshed'] = int(easee_state.now_ts(self.plugin))
        self.plugin.state['price_resolution'] = 'HOURLY'
        self.plugin.state['currency'] = 'EUR'
