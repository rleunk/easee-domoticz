    p1_import_cost_month: float = 0.0
    p1_export_spot_eur_month: float = 0.0
    p1_export_fee_eur_month: float = 0.0
    p1_export_sales_fee_eur_month: float = 0.0
    p1_export_tax_eur_month: float = 0.0
    p1_export_revenue_month: float = 0.0
    p1_net_month: float = 0.0


def _parse_counter(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _delta_kwh(current_wh: float, previous_wh: float) -> float:
    delta_wh = current_wh - previous_wh
    if delta_wh < 0:
        _LOGGER.warning(
            "Energy counter decreased (%.3f -> %.3f Wh); resetting baseline",
            previous_wh,
            current_wh,
        )
        return 0.0
    return delta_wh / 1000.0


def _start_of_day(now: datetime) -> datetime:
    local = now.astimezone()
    return local.replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(timezone.utc)


def _start_of_month(now: datetime) -> datetime:
    local = now.astimezone()
    return local.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).astimezone(timezone.utc)


def _start_of_year(now: datetime) -> datetime:
    local = now.astimezone()
    return local.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    ).astimezone(timezone.utc)


def _week_ago(now: datetime) -> datetime:
    local = now.astimezone()
    return (local - timedelta(days=7)).astimezone(timezone.utc)


# Ignore round-trip ratio until at least this much charge is tracked in FIFO.
_MIN_CHARGE_FOR_EFFICIENCY_KWH = 0.01


def _roundtrip_efficiency(charged_kwh: float, discharged_kwh: float) -> float | None:
    """Energy-out / energy-in; None when charge data is insufficient."""
    if charged_kwh < _MIN_CHARGE_FOR_EFFICIENCY_KWH or discharged_kwh <= 0:
        return None
    return min(discharged_kwh / charged_kwh, 1.0)


@dataclass
class _CachedStats:
    profit_today: float
    profit_week: float
    profit_month: float
    profit_year: float
    profit_total: float
    export_revenue_today: float
    charged_total_kwh: float
    charged_solar_kwh: float
    charged_grid_kwh: float
    discharged_total_kwh: float


def _empty_stats() -> _CachedStats:
    return _CachedStats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class EconomicsEngine:
    """Turns Sessy meter deltas + prices into FIFO bookkeeping."""

    def __init__(
        self,
        hass: HomeAssistant,
        db: SessyEconomicsDatabase,
        config: EconomicsConfig,
    ) -> None:
        self._hass = hass
        self._db = db
        self._config = config
        self._pricing = PriceResolver(hass, config)
        self._inventory: FIFOInventory | None = None
        self._stats_cache: _CachedStats | None = None
        self._stats_day: str | None = None

    async def _refresh_stats(self, now: datetime) -> _CachedStats:
        charged_total = await self._db.charged_total_kwh()
        discharged_total = await self._db.discharged_total_kwh()
        return _CachedStats(
            profit_today=await self._db.profit_sum_since(_start_of_day(now)),
            profit_week=await self._db.profit_sum_since(_week_ago(now)),
            profit_month=await self._db.profit_sum_since(_start_of_month(now)),
            profit_year=await self._db.profit_sum_since(_start_of_year(now)),
            profit_total=await self._db.profit_total(),
            export_revenue_today=await self._db.export_revenue_sum_since(
                _start_of_day(now)
            ),
            charged_total_kwh=charged_total,
            charged_solar_kwh=await self._db.charged_total_by_source(SOURCE_SOLAR),
            charged_grid_kwh=await self._db.charged_total_by_source(SOURCE_GRID),
            discharged_total_kwh=discharged_total,
        )

    def _roll_stats_day(self, now: datetime) -> None:
        day = now.astimezone().date().isoformat()
        if self._stats_cache is not None and self._stats_day != day:
            self._stats_cache.profit_today = 0.0
            self._stats_cache.export_revenue_today = 0.0
        self._stats_day = day

    def _apply_activity_to_cache(
        self,
        *,
        charge_solar_kwh: float,
        charge_grid_kwh: float,
        discharge_kwh: float,
        last_profit: float,
        last_discharge_revenue: float,
    ) -> None:
        if self._stats_cache is None:
            return
        charge_total = charge_solar_kwh + charge_grid_kwh
        if charge_total > 0:
            self._stats_cache.charged_total_kwh += charge_total
            self._stats_cache.charged_solar_kwh += charge_solar_kwh
            self._stats_cache.charged_grid_kwh += charge_grid_kwh
        if discharge_kwh > 0:
            self._stats_cache.discharged_total_kwh += discharge_kwh
        if last_profit:
            self._stats_cache.profit_today += last_profit
            self._stats_cache.profit_week += last_profit
            self._stats_cache.profit_month += last_profit
            self._stats_cache.profit_year += last_profit
            self._stats_cache.profit_total += last_profit
        if last_discharge_revenue:
            self._stats_cache.export_revenue_today += last_discharge_revenue

    async def load_stats_cache(self) -> None:
        """Load profit totals from DB once in background (never during poll)."""
        now = datetime.now(timezone.utc)
        self._stats_cache = await self._refresh_stats(now)
        self._stats_day = now.astimezone().date().isoformat()
        _LOGGER.debug("Profit stats cache loaded from database")

    async def async_setup(self) -> None:
        self._inventory = await self._db.load_inventory()

    @property
    def inventory(self) -> FIFOInventory:
        assert self._inventory is not None
        return self._inventory

    @property
    def pricing(self) -> PriceResolver:
        return self._pricing

    async def _add_charge_batch(
        self,
        energy_kwh: float,
        cost_price: float,
        source: str,
        now: datetime,
        *,
        commit: bool = False,
    ) -> None:
        assert self._inventory is not None
        batch = self._inventory.add_batch(
            energy_kwh, cost_price, source=source, timestamp=now
        )
        if batch is not None:
            batch.id = await self._db.insert_batch(batch, commit=commit)
            _LOGGER.debug(
                "Charged %.4f kWh (%s) at €%.4f/kWh (batch #%s)",
                energy_kwh,
                source,
                cost_price,
                batch.id,
            )

    async def process(
        self,
        *,
        import_wh: float,
        export_wh: float,
        power_w: int,
        pv_power_w: int,
        state_of_charge: float,
        p1_import_w: int | None = None,
        p1_export_w: int | None = None,
        p1_import_register_wh: int | None = None,
        p1_export_register_wh: int | None = None,
    ) -> EconomicsSnapshot:
        assert self._inventory is not None
        now = datetime.now(timezone.utc)
        self._roll_stats_day(now)
        import_price = self._pricing.import_price()
        export_price = self._pricing.export_price()
        solar_cost = self._pricing.solar_cost_price()

        last_import = _parse_counter(await self._db.get_state(STATE_LAST_IMPORT_WH))
        last_export = _parse_counter(await self._db.get_state(STATE_LAST_EXPORT_WH))

        charge_kwh = 0.0
        charge_solar_kwh = 0.0
        charge_grid_kwh = 0.0
        discharge_kwh = 0.0
        last_profit = 0.0
        last_discharge_revenue = 0.0
        persist_counters = True

        p1_import = self._pricing.p1_import_power_w()
        p1_export = self._pricing.p1_export_power_w()

        if last_import is not None:
            charge_kwh = _delta_kwh(import_wh, last_import)
            if charge_kwh > 0:
                if import_price is None:
                    persist_counters = False
                    _LOGGER.warning(
                        "Skipped %.4f kWh charge — import price unavailable",
                        charge_kwh,
                    )
                else:
                    split = attribute_charge(
                        charge_kwh,
                        power_w=power_w,
                        pv_power_w=pv_power_w,
                        p1_import_w=p1_import,
                        use_pv_attribution=self._config.use_pv_attribution,
                    )
                    charge_solar_kwh = split.solar_kwh
                    charge_grid_kwh = split.grid_kwh

                    if charge_solar_kwh > 0:
                        await self._add_charge_batch(
                            charge_solar_kwh, solar_cost, SOURCE_SOLAR, now
                        )
                    if charge_grid_kwh > 0:
                        await self._add_charge_batch(
                            charge_grid_kwh, import_price, SOURCE_GRID, now
                        )

        if last_export is not None:
            discharge_kwh = _delta_kwh(export_wh, last_export)
            if discharge_kwh > 0:
                sale = discharge_sale_price(
                    power_w=power_w,
                    p1_export_w=p1_export,
                    import_price=import_price or 0.0,
                    export_price=export_price or 0.0,
                )
                if import_price is None and export_price is None:
                    persist_counters = False
                    _LOGGER.warning(
                        "Skipped %.4f kWh discharge — prices unavailable",
                        discharge_kwh,
                    )
                else:
                    result = self._inventory.consume(discharge_kwh)
                    if result.energy_kwh > 0:
                        revenue = result.energy_kwh * sale
                        profit = revenue - result.purchase_cost
                        last_profit += profit
                        last_discharge_revenue += revenue
                        await self._db.record_profit(
                            timestamp=now,
                            energy_kwh=result.energy_kwh,
                            purchase_price=result.avg_purchase_price,
                            sale_price=sale,
                            profit=profit,
                            solar_kwh=result.solar_kwh,
                            grid_kwh=result.grid_kwh,
                            commit=False,
                        )
                        await self._db.persist_inventory(
                            self._inventory, commit=False
                        )
                        self._inventory.prune_depleted()
                        _LOGGER.debug(
                            "Discharged %.4f kWh at €%.4f/kWh: "
                            "cost €%.4f, profit €%.4f",
                            result.energy_kwh,
                            sale,
                            result.purchase_cost,
                            profit,
                        )

                    untracked_kwh = discharge_kwh - result.energy_kwh
                    if untracked_kwh > 1e-9:
                        untracked_revenue = untracked_kwh * sale
                        last_profit += untracked_revenue
                        last_discharge_revenue += untracked_revenue
                        await self._db.record_profit(
                            timestamp=now,
                            energy_kwh=untracked_kwh,
                            purchase_price=0.0,
                            sale_price=sale,
                            profit=untracked_revenue,
                            solar_kwh=0.0,
                            grid_kwh=untracked_kwh,
                            commit=False,
                        )
                        _LOGGER.debug(
                            "Untracked discharge %.4f kWh at €%.4f/kWh: "
                            "gross €%.4f (no FIFO batch)",
                            untracked_kwh,
                            sale,
                            untracked_revenue,
                        )

        if persist_counters or last_import is None or last_export is None:
            await self._db.set_state(
                STATE_LAST_IMPORT_WH, str(import_wh), commit=False
            )
            await self._db.set_state(
                STATE_LAST_EXPORT_WH, str(export_wh), commit=False
            )

        p1_totals = await update_p1_accounting(
            self._db,
            self._pricing,
            p1_import_w=p1_import_w,
            p1_export_w=p1_export_w,
            p1_import_register_wh=p1_import_register_wh,
            p1_export_register_wh=p1_export_register_wh,
            now=now,
            since_today=_start_of_day(now),
        )

        await self._db.commit()

        activity = charge_kwh > 1e-9 or discharge_kwh > 1e-9
        if self._stats_cache is None:
            self._stats_cache = _empty_stats()
        if activity:
            self._apply_activity_to_cache(
                charge_solar_kwh=charge_solar_kwh,
                charge_grid_kwh=charge_grid_kwh,
                discharge_kwh=discharge_kwh,
                last_profit=last_profit,
                last_discharge_revenue=last_discharge_revenue,
            )
        stats = self._stats_cache
        assert stats is not None

        stored = self._inventory.stored_kwh
        avg_cost = self._inventory.average_cost
        imp = import_price or 0.0
        exp = export_price or 0.0
        energy_value = stored * imp
        unrealized = stored * (exp - avg_cost) if stored > 0 else 0.0
        if_sold_now = stored * exp

        current_sale = discharge_sale_price(
            power_w=power_w,
            p1_export_w=p1_export,
            import_price=imp,
            export_price=exp,
        )
        live_discharge_eur_h = (
            (power_w / 1000.0) * current_sale if power_w > 0 else 0.0
        )
        efficiency = _roundtrip_efficiency(
            stats.charged_total_kwh, stats.discharged_total_kwh
        )

        return EconomicsSnapshot(
            stored_kwh=stored,
            average_cost=avg_cost,
            energy_value=energy_value,
            unrealized_profit=unrealized,
            profit_today=stats.profit_today,
            profit_week=stats.profit_week,
            profit_month=stats.profit_month,
            profit_year=stats.profit_year,
            profit_total=stats.profit_total,
            charged_total_kwh=stats.charged_total_kwh,
            charged_solar_kwh=stats.charged_solar_kwh,
            charged_grid_kwh=stats.charged_grid_kwh,
            discharged_total_kwh=stats.discharged_total_kwh,
            roundtrip_efficiency=efficiency,
            solar_ratio=self._inventory.solar_ratio,
            grid_ratio=self._inventory.grid_ratio,
            power_w=power_w,
            pv_power_w=pv_power_w,
            state_of_charge=state_of_charge,
            last_charge_kwh=charge_kwh,
            last_charge_solar_kwh=charge_solar_kwh,
            last_charge_grid_kwh=charge_grid_kwh,
            last_discharge_kwh=discharge_kwh,
            last_profit=last_profit,
            last_discharge_revenue=last_discharge_revenue,
            live_discharge_eur_h=live_discharge_eur_h,
            export_revenue_today=stats.export_revenue_today,
            import_price=imp,
            export_price=exp,
            if_sold_now=if_sold_now,
            p1_import_w=p1_import_w,
            p1_export_w=p1_export_w,
            p1_import_kwh_today=p1_totals.import_kwh_today,
            p1_export_kwh_today=p1_totals.export_kwh_today,
            p1_import_spot_eur_today=p1_totals.import_spot_eur_today,
            p1_import_fee_eur_today=p1_totals.import_fee_eur_today,
            p1_import_tax_eur_today=p1_totals.import_tax_eur_today,
            p1_import_cost_today=p1_totals.import_cost_today,
            p1_export_spot_eur_today=p1_totals.export_spot_eur_today,
            p1_export_fee_eur_today=p1_totals.export_fee_eur_today,
            p1_export_sales_fee_eur_today=p1_totals.export_sales_fee_eur_today,
            p1_export_tax_eur_today=p1_totals.export_tax_eur_today,
            p1_export_revenue_today=p1_totals.export_revenue_today,
            p1_net_today=p1_totals.net_today,
            p1_import_cost_live_eur_h=p1_totals.import_cost_live_eur_h,
            p1_export_revenue_live_eur_h=p1_totals.export_revenue_live_eur_h,
            p1_import_kwh_month=p1_totals.import_kwh_month,
            p1_export_kwh_month=p1_totals.export_kwh_month,
            p1_import_spot_eur_month=p1_totals.import_spot_eur_month,
            p1_import_fee_eur_month=p1_totals.import_fee_eur_month,
            p1_import_tax_eur_month=p1_totals.import_tax_eur_month,
            p1_import_cost_month=p1_totals.import_cost_month,
            p1_export_spot_eur_month=p1_totals.export_spot_eur_month,
            p1_export_fee_eur_month=p1_totals.export_fee_eur_month,
            p1_export_sales_fee_eur_month=p1_totals.export_sales_fee_eur_month,
            p1_export_tax_eur_month=p1_totals.export_tax_eur_month,
            p1_export_revenue_month=p1_totals.export_revenue_month,
            p1_net_month=p1_totals.net_month,
        )

