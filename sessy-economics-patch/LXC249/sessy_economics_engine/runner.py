"""Async poll loop — mirrors HA coordinator without Home Assistant."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from sessy_economics.api import SessyApi, SessyApiError
from sessy_economics.const import PRICE_MODE_GROSS
from sessy_economics.database import SessyEconomicsDatabase
from sessy_economics.dynamic_plan import build_dynamic_plan
from sessy_economics.economics import (
    EconomicsEngine,
    EconomicsSnapshot,
    STATE_LAST_EXPORT_WH,
    STATE_LAST_IMPORT_WH,
    STATE_LAST_POLL_TS,
)
from sessy_economics.pricing import EconomicsConfig, PriceCache, PriceContext

from .config import EngineConfig
from .mqtt_client import MqttBridge

_LOGGER = logging.getLogger(__name__)
_UPDATE_TIMEOUT_S = 25.0


class EngineRunner:
    """Poll Sessy, run FIFO accounting, publish MQTT."""

    def __init__(self, config: EngineConfig) -> None:
        self._config = config
        self._price_cache = PriceCache(
            static_import_eur_kwh=config.prices.import_eur_kwh,
            static_spot_eur_kwh=config.prices.spot_eur_kwh,
            static_export_eur_kwh=config.prices.export_eur_kwh,
        )
        self._db = SessyEconomicsDatabase(config.database_path)
        eco_cfg = EconomicsConfig.from_entry_data(config.economics_entry_data())
        self._engine = EconomicsEngine(self._db, eco_cfg, self._price_cache)
        self._mqtt = MqttBridge(config, self._price_cache)
        self._session: aiohttp.ClientSession | None = None
        self._api: SessyApi | None = None
        self._p1_api: SessyApi | None = None
        self._last_snapshot: EconomicsSnapshot | None = None
        self._energy_from_power = False
        self._running = False

    async def start(self) -> None:
        self._session = aiohttp.ClientSession()
        sessy = self._config.sessy
        self._api = SessyApi(
            sessy.host, self._session, sessy.username, sessy.password
        )
        p1_host = (sessy.p1_host or sessy.host).strip()
        p1_user, p1_pass = sessy.p1_credentials
        self._p1_api = (
            self._api
            if p1_host == sessy.host
            else SessyApi(p1_host, self._session, p1_user, p1_pass)
        )
        await self._db.async_initialize()
        await self._engine.async_setup()
        await self._engine.load_stats_cache()
        self._mqtt.start()
        await self._wait_mqtt_ready()
        self._running = True
        _LOGGER.info(
            "Engine started — Sessy %s, poll every %ss",
            sessy.host,
            self._config.poll_interval_seconds,
        )

    async def stop(self) -> None:
        self._running = False
        self._mqtt.stop()
        await self._db.async_close()
        if self._session:
            await self._session.close()
        _LOGGER.info("Engine stopped")

    async def run_forever(self) -> None:
        interval = max(10, self._config.poll_interval_seconds)
        while self._running:
            started = time.monotonic()
            try:
                snapshot = await asyncio.wait_for(
                    self._poll_economics(), timeout=_UPDATE_TIMEOUT_S
                )
                self._last_snapshot = snapshot
                self._mqtt.publish_snapshot(snapshot)
            except TimeoutError:
                _LOGGER.warning(
                    "Poll timed out after %.0fs; keeping last snapshot",
                    _UPDATE_TIMEOUT_S,
                )
            except Exception:
                _LOGGER.exception("Poll failed")
                try:
                    await self._db.rollback()
                except Exception:
                    _LOGGER.debug("DB rollback after poll failure failed", exc_info=True)
            try:
                await self._fetch_and_publish_plan()
            except Exception:
                _LOGGER.debug("Dynamic plan publish failed", exc_info=True)
            elapsed = time.monotonic() - started
            await asyncio.sleep(max(0.0, interval - elapsed))

    async def _wait_mqtt_ready(self, timeout_s: float = 120.0) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._mqtt.is_connected:
                _LOGGER.info("MQTT ready")
                return
            await asyncio.sleep(2.0)
        _LOGGER.warning(
            "MQTT not connected after %.0fs — polling anyway", timeout_s
        )

    async def _integrate_power_wh(self, power_w: int) -> tuple[float, float]:
        now = time.time()
        last_ts_raw = await self._db.get_state(STATE_LAST_POLL_TS)
        last_import_raw = await self._db.get_state(STATE_LAST_IMPORT_WH)
        last_export_raw = await self._db.get_state(STATE_LAST_EXPORT_WH)

        import_wh = float(last_import_raw) if last_import_raw else 0.0
        export_wh = float(last_export_raw) if last_export_raw else 0.0

        if last_ts_raw:
            dt_s = max(0.0, now - float(last_ts_raw))
            wh = abs(power_w) * dt_s / 3600.0
            if power_w < 0:
                import_wh += wh
            elif power_w > 0:
                export_wh += wh

        await self._db.set_state(STATE_LAST_POLL_TS, str(now), commit=False)
        return import_wh, export_wh

    async def _fetch_sessy_context(self) -> PriceContext:
        assert self._api is not None
        assert self._p1_api is not None
        ctx = PriceContext()
        cfg = self._engine.pricing.config

        if cfg.price_mode != PRICE_MODE_GROSS:
            try:
                schedule = await self._api.dynamic_schedule()
                ctx.sessy_epex_eur_kwh = SessyApi.current_epex_eur_kwh(schedule)
            except SessyApiError as err:
                _LOGGER.debug("Sessy EPEX schedule unavailable: %s", err)

        if cfg.use_sessy_p1_api:
            try:
                p1 = await self._p1_api.p1_details()
                ctx.p1_import_w = SessyApi.p1_import_w(p1)
                ctx.p1_export_w = SessyApi.p1_export_w(p1)
                ctx.p1_import_register_wh = SessyApi.p1_import_register_wh(p1)
                ctx.p1_export_register_wh = SessyApi.p1_export_register_wh(p1)
            except SessyApiError as err:
                _LOGGER.debug("Sessy P1 API unavailable: %s", err)

        return ctx

    async def _fetch_and_publish_plan(self) -> None:
        assert self._api is not None
        try:
            schedule = await self._api.dynamic_schedule()
        except SessyApiError as err:
            _LOGGER.warning("Dynamic plan unavailable: %s", err)
            return
        plan = build_dynamic_plan(schedule)
        if not plan.get("slot_count"):
            _LOGGER.warning(
                "Dynamic plan empty (check Sessy eco/dynamic mode and API auth)"
            )
            return
        self._mqtt.publish_dynamic_plan(plan)

    async def _poll_economics(self) -> EconomicsSnapshot:
        assert self._api is not None
        try:
            power = await self._api.power_status()
        except SessyApiError as err:
            if self._last_snapshot is not None:
                _LOGGER.warning(
                    "Sessy power/status unavailable (%s); skipping economics tick",
                    err,
                )
                return self._last_snapshot
            raise RuntimeError(str(err)) from err

        sessy = power.get("sessy") or {}
        power_w = int(sessy.get("power") or 0)

        self._energy_from_power = False
        try:
            energy = await self._api.energy_status()
            sessy_energy = energy.get("sessy_energy") or {}
            import_wh = float(sessy_energy.get("import_wh") or 0.0)
            export_wh = float(sessy_energy.get("export_wh") or 0.0)
        except SessyApiError as err:
            if "401" not in str(err):
                raise RuntimeError(str(err)) from err
            self._energy_from_power = True
            _LOGGER.info(
                "Sessy /energy/status requires auth; estimating energy from power"
            )
            import_wh, export_wh = await self._integrate_power_wh(power_w)

        ctx = await self._fetch_sessy_context()
        self._engine.pricing.set_context(ctx)
        soc = float(sessy.get("state_of_charge") or 0.0)
        pv_power_w = SessyApi.pv_power_w(power)

        return await self._engine.process(
            import_wh=import_wh,
            export_wh=export_wh,
            power_w=power_w,
            pv_power_w=pv_power_w,
            state_of_charge=soc,
            p1_import_w=ctx.p1_import_w,
            p1_export_w=ctx.p1_export_w,
            p1_import_register_wh=ctx.p1_import_register_wh,
            p1_export_register_wh=ctx.p1_export_register_wh,
        )

    def diagnostics(self) -> dict[str, Any]:
        inv = self._engine.inventory
        pricing = self._engine.pricing
        ctx = pricing._context  # noqa: SLF001
        return {
            "stored_kwh": inv.stored_kwh,
            "import_price": pricing.import_price(),
            "export_price": pricing.export_price(),
            "sessy_epex_price": ctx.sessy_epex_eur_kwh,
            "p1_import_w": ctx.p1_import_w,
            "p1_export_w": ctx.p1_export_w,
            "p1_import_register_wh": ctx.p1_import_register_wh,
            "p1_export_register_wh": ctx.p1_export_register_wh,
            "energy_from_power": self._energy_from_power,
            "mqtt_import": self._price_cache.import_eur_kwh,
            "mqtt_spot": self._price_cache.spot_eur_kwh,
        }
