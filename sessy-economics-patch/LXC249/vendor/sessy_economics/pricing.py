"""Resolve import/export prices from MQTT cache and configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_ENERGY_TAX_EXPORT,
    CONF_ENERGY_TAX_IMPORT,
    CONF_EXPORT_PRICE_ENTITY,
    CONF_FEED_IN_TARIFF,
    CONF_INCLUDE_VAT,
    CONF_P1_EXPORT_POWER_ENTITY,
    CONF_P1_HOST,
    CONF_P1_IMPORT_POWER_ENTITY,
    CONF_PRICE_MODE,
    CONF_SOLAR_COST_MODE,
    CONF_SPOT_PRICE_ENTITY,
    CONF_TIBBER_PRICE_ENTITY,
    CONF_TIBBER_SPOT_ATTRIBUTE,
    CONF_TIBBER_SPOT_ENTITY,
    CONF_USE_PV_ATTRIBUTION,
    CONF_USE_SESSY_P1_API,
    CONF_USE_TIBBER_ENERGY_ATTRIBUTE,
    CONF_VAT_FACTOR,
    DEFAULT_ENERGY_TAX_EXPORT,
    DEFAULT_ENERGY_TAX_IMPORT,
    DEFAULT_FEED_IN_TARIFF,
    DEFAULT_INCLUDE_VAT,
    DEFAULT_TIBBER_INKOOPVERGOEDING,
    DEFAULT_TIBBER_SPOT_ATTRIBUTE,
    DEFAULT_TIBBER_VERKOOPVERGOEDING,
    DEFAULT_USE_SESSY_P1_API,
    DEFAULT_USE_TIBBER_ENERGY_ATTRIBUTE,
    DEFAULT_VAT_FACTOR,
    PRICE_MODE_GROSS,
    PRICE_MODE_SPOT_PLUS_TAX,
    SOLAR_COST_FREE,
    SOLAR_COST_OPPORTUNITY,
)
from .tariff import TariffComponents


@dataclass
class PriceContext:
    """Runtime values from Sessy API (refreshed each poll)."""

    sessy_epex_eur_kwh: float | None = None
    p1_import_w: int | None = None
    p1_export_w: int | None = None
    p1_import_register_wh: int | None = None
    p1_export_register_wh: int | None = None


@dataclass(frozen=True)
class EconomicsConfig:
    """Runtime configuration for economics calculations."""

    price_mode: str
    import_price_entity: str
    spot_price_entity: str | None
    export_price_entity: str | None
    energy_tax_import: float
    energy_tax_export: float
    vat_factor: float
    feed_in_tariff: float
    include_vat: bool
    solar_cost_mode: str
    use_pv_attribution: bool
    p1_import_power_entity: str | None
    p1_export_power_entity: str | None
    use_tibber_energy_attribute: bool
    tibber_spot_entity: str | None
    tibber_spot_attribute: str
    use_sessy_p1_api: bool
    p1_host: str | None

    @classmethod
    def from_entry_data(cls, data: dict[str, Any]) -> EconomicsConfig:
        return cls(
            price_mode=data.get(CONF_PRICE_MODE, PRICE_MODE_GROSS),
            import_price_entity=data.get(CONF_TIBBER_PRICE_ENTITY, ""),
            spot_price_entity=data.get(CONF_SPOT_PRICE_ENTITY) or None,
            export_price_entity=data.get(CONF_EXPORT_PRICE_ENTITY) or None,
            energy_tax_import=float(
                data.get(CONF_ENERGY_TAX_IMPORT, DEFAULT_ENERGY_TAX_IMPORT)
            ),
            energy_tax_export=float(
                data.get(CONF_ENERGY_TAX_EXPORT, DEFAULT_ENERGY_TAX_EXPORT)
            ),
            vat_factor=float(data.get(CONF_VAT_FACTOR, DEFAULT_VAT_FACTOR)),
            feed_in_tariff=float(data.get(CONF_FEED_IN_TARIFF, DEFAULT_FEED_IN_TARIFF)),
            include_vat=bool(data.get(CONF_INCLUDE_VAT, DEFAULT_INCLUDE_VAT)),
            solar_cost_mode=data.get(CONF_SOLAR_COST_MODE, SOLAR_COST_OPPORTUNITY),
            use_pv_attribution=bool(data.get(CONF_USE_PV_ATTRIBUTION, True)),
            p1_import_power_entity=data.get(CONF_P1_IMPORT_POWER_ENTITY) or None,
            p1_export_power_entity=data.get(CONF_P1_EXPORT_POWER_ENTITY) or None,
            use_tibber_energy_attribute=bool(
                data.get(
                    CONF_USE_TIBBER_ENERGY_ATTRIBUTE,
                    DEFAULT_USE_TIBBER_ENERGY_ATTRIBUTE,
                )
            ),
            tibber_spot_entity=data.get(CONF_TIBBER_SPOT_ENTITY) or None,
            tibber_spot_attribute=data.get(
                CONF_TIBBER_SPOT_ATTRIBUTE, DEFAULT_TIBBER_SPOT_ATTRIBUTE
            ),
            use_sessy_p1_api=bool(
                data.get(CONF_USE_SESSY_P1_API, DEFAULT_USE_SESSY_P1_API)
            ),
            p1_host=data.get(CONF_P1_HOST) or None,
        )


@dataclass
class PriceCache:
    """Latest Tibber prices from MQTT (or static config overrides)."""

    import_eur_kwh: float | None = None
    spot_eur_kwh: float | None = None
    tax_eur_kwh: float | None = None
    export_eur_kwh: float | None = None
    static_import_eur_kwh: float | None = None
    static_spot_eur_kwh: float | None = None
    static_export_eur_kwh: float | None = None


class PriceResolver:
    """Compute import, export and solar opportunity prices."""

    def __init__(self, cache: PriceCache, config: EconomicsConfig) -> None:
        self._cache = cache
        self._config = config
        self._context = PriceContext()

    def set_context(self, context: PriceContext) -> None:
        self._context = context

    @property
    def config(self) -> EconomicsConfig:
        return self._config

    def _apply_vat(self, net_price: float) -> float:
        if self._config.include_vat:
            return net_price * self._config.vat_factor
        return net_price

    def _tibber_spot(self) -> float | None:
        if not self._config.use_tibber_energy_attribute:
            return None
        if self._cache.spot_eur_kwh is not None:
            return self._cache.spot_eur_kwh
        return self._cache.static_spot_eur_kwh

    def _resolve_spot(self) -> float | None:
        if self._cache.spot_eur_kwh is not None:
            return self._cache.spot_eur_kwh
        if self._cache.static_spot_eur_kwh is not None:
            return self._cache.static_spot_eur_kwh
        return self._tibber_spot()

    def _vat(self, value: float) -> float:
        if self._config.include_vat:
            return value * self._config.vat_factor
        return value

    def _resolve_energy_tax(self) -> float:
        tax = self._cache.tax_eur_kwh
        if tax is not None and tax > 0:
            return self._vat(tax)
        return self._vat(self._config.energy_tax_import)

    def _resolve_energy_tax_export(self) -> float:
        return self._vat(self._config.energy_tax_export)

    def import_tariff(self) -> TariffComponents | None:
        purchase_fee = self._vat(DEFAULT_TIBBER_INKOOPVERGOEDING)
        energy_tax = self._resolve_energy_tax()
        spot = self._resolve_spot()
        if spot is not None:
            return TariffComponents(self._vat(spot), purchase_fee, energy_tax)

        all_in = self.import_price()
        if all_in is None:
            return None
        spot_est = max(0.0, all_in - purchase_fee - energy_tax)
        return TariffComponents(spot_est, purchase_fee, energy_tax)

    def export_tariff(self) -> TariffComponents | None:
        purchase_fee = self._vat(DEFAULT_TIBBER_INKOOPVERGOEDING)
        sales_fee = self._vat(DEFAULT_TIBBER_VERKOOPVERGOEDING)
        energy_tax = self._resolve_energy_tax_export()
        spot = self._resolve_spot()
        if spot is None and self._context.sessy_epex_eur_kwh is not None:
            spot = self._context.sessy_epex_eur_kwh
        if spot is None:
            export_all = self.export_price()
            if export_all is None:
                return None
            # credit ≈ spot − fees − export tax; gross export_all ≈ spot − sales_fee
            spot_est = max(0.0, export_all + sales_fee - purchase_fee + energy_tax)
            return TariffComponents(spot_est, purchase_fee, energy_tax, sales_fee)
        return TariffComponents(self._vat(spot), purchase_fee, energy_tax, sales_fee)

    def import_price(self) -> float | None:
        mode = self._config.price_mode

        cached = self._cache.import_eur_kwh
        if cached is not None and cached > 0:
            return cached

        static = self._cache.static_import_eur_kwh
        if static is not None:
            return static

        if mode == PRICE_MODE_SPOT_PLUS_TAX:
            spot = self._resolve_spot()
            if spot is None:
                return None
            net = spot + self._config.energy_tax_import
            return self._apply_vat(net)

        spot = self._tibber_spot()
        tax = self._cache.tax_eur_kwh
        if spot is not None and tax is not None:
            return spot + tax

        return None

    def export_price(self) -> float | None:
        explicit = self._cache.static_export_eur_kwh or self._cache.export_eur_kwh
        if explicit is not None:
            return explicit

        if self._config.price_mode == PRICE_MODE_GROSS:
            import_p = self.import_price()
            if import_p is not None:
                return max(0.0, import_p - DEFAULT_TIBBER_VERKOOPVERGOEDING)

        spot = self._tibber_spot()
        if spot is not None:
            return spot

        if self._context.sessy_epex_eur_kwh is not None:
            return self._context.sessy_epex_eur_kwh

        mode = self._config.price_mode
        if mode == PRICE_MODE_SPOT_PLUS_TAX:
            resolved = self._resolve_spot()
            if resolved is None:
                return self._config.feed_in_tariff
            net = resolved - self._config.energy_tax_export
            return self._apply_vat(max(resolved, net))

        return self._config.feed_in_tariff

    def solar_cost_price(self) -> float:
        if self._config.solar_cost_mode == SOLAR_COST_FREE:
            return 0.0
        export = self.export_price()
        if export is not None:
            return export
        return self._config.feed_in_tariff

    def p1_import_power_w(self) -> int | None:
        if self._context.p1_import_w is not None:
            return self._context.p1_import_w
        return None

    def p1_export_power_w(self) -> int | None:
        if self._context.p1_export_w is not None:
            return self._context.p1_export_w
        return None

