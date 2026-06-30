# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class PricingProvider(ABC):
    """Abstract pricing source for kWh cost calculations."""

    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_current_price(self) -> dict:
        pass

    @abstractmethod
    def get_today_prices(self) -> list:
        pass

    @abstractmethod
    def get_tomorrow_prices(self) -> list:
        pass

    def refresh(self) -> None:
        """Refresh cached prices when supported."""
