"""Async client for the local Sessy Open API."""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .p1_registers import delivered_wh, returned_wh

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=5, connect=3)


class SessyApiError(Exception):
    """Raised when the Sessy API returns an error or is unreachable."""


class SessyApi:
    """Minimal Sessy API client for economics tracking."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        host = host.strip()
        if host.startswith("http://"):
            host = host[7:]
        if host.startswith("https://"):
            host = host[8:]
        self._base = f"http://{host.rstrip('/')}"
        self._session = session
        self._auth: aiohttp.BasicAuth | None = None
        if username and password:
            self._auth = aiohttp.BasicAuth(username, password)

    async def _get(self, path: str) -> dict[str, Any]:
        url = f"{self._base}{path}"
        auth_attempts: list[aiohttp.BasicAuth | None] = [self._auth] if self._auth else [None]
        if self._auth:
            auth_attempts.append(None)

        last_error: SessyApiError | None = None
        for auth in auth_attempts:
            try:
                async with self._session.get(
                    url, auth=auth, timeout=TIMEOUT
                ) as resp:
                    if resp.status == 401:
                        last_error = SessyApiError(f"{path} HTTP 401: unauthorized")
                        continue
                    if resp.status != 200:
                        text = await resp.text()
                        raise SessyApiError(
                            f"{path} HTTP {resp.status}: {text[:200]}"
                        )
                    data = await resp.json()
            except aiohttp.ClientError as err:
                raise SessyApiError(f"{path} request failed: {err}") from err

            if data.get("status") != "ok":
                raise SessyApiError(f"{path} returned non-ok status: {data!r}")
            return data

        raise last_error or SessyApiError(f"{path} HTTP 401: unauthorized")

    async def power_status(self) -> dict[str, Any]:
        return await self._get("/api/v1/power/status")

    async def energy_status(self) -> dict[str, Any]:
        return await self._get("/api/v1/energy/status")

    async def p1_details(self) -> dict[str, Any]:
        """P1 meter live data (power + DSMR cumulative registers)."""
        return await self._get("/api/v2/p1/details")

    async def dynamic_schedule(self) -> dict[str, Any]:
        return await self._get("/api/v2/dynamic/schedule")

    @staticmethod
    def pv_power_w(power_status: dict[str, Any]) -> int:
        total = 0
        for key in (
            "renewable_energy_phase1",
            "renewable_energy_phase2",
            "renewable_energy_phase3",
        ):
            phase = power_status.get(key) or {}
            total += int(phase.get("power") or 0)
        return max(0, total)

    @staticmethod
    def p1_import_w(p1_details: dict[str, Any]) -> int:
        return max(0, int(p1_details.get("power_consumed") or 0))

    @staticmethod
    def p1_export_w(p1_details: dict[str, Any]) -> int:
        return max(0, int(p1_details.get("power_produced") or 0))

    @staticmethod
    def p1_import_register_wh(p1_details: dict[str, Any]) -> int | None:
        return delivered_wh(p1_details)

    @staticmethod
    def p1_export_register_wh(p1_details: dict[str, Any]) -> int | None:
        return returned_wh(p1_details)

    @staticmethod
    def current_epex_eur_kwh(schedule: dict[str, Any]) -> float | None:
        now = int(time.time())
        prices = schedule.get("energy_prices") or []
        for slot in prices:
            start = int(slot.get("start_time") or 0)
            end = int(slot.get("end_time") or 0)
            if start <= now < end:
                raw = float(slot.get("price") or 0)
                return raw / 100_000.0
        return None
