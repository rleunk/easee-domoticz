from __future__ import annotations

import json
from dataclasses import dataclass

import aiohttp

from sessy_factuur_web.p1_month import P1MonthTotals


@dataclass
class FactuurFormValues:
    factuur_maand: str
    factuur_periode: str
    grid_rewards: float
    systeembeheer: float
    levering: float
    vermindering_eb: float
    ref_import_excl: float
    ref_export_credit_excl: float
    ref_grid_rewards_excl: float
    ref_vast_excl: float
    ref_totaal_incl_btw: float
    ref_import_kwh: float
    ref_export_kwh: float


def validate_factuur_numbers(form: FactuurFormValues) -> None:
    """Reject PDF-parser mistakes (year captured as €) before HA push."""
    checks: list[tuple[str, float]] = [
        ("Grid Rewards", form.grid_rewards),
        ("Systeembeheer", form.systeembeheer),
        ("Vaste levering", form.levering),
        ("Vermindering EB", form.vermindering_eb),
        ("Ref Grid Rewards excl", form.ref_grid_rewards_excl),
        ("Ref vaste excl", form.ref_vast_excl),
    ]
    for label, val in checks:
        if abs(val) >= 1900:
            raise ValueError(
                f"{label} = {val} lijkt een jaar, geen eurobedrag. "
                "Zet Stap 3 handmatig goed (of upload PDF opnieuw na parser-update)."
            )
    if form.ref_import_kwh > 5000 or form.ref_export_kwh > 5000:
        raise ValueError("Ref kWh onrealistisch hoog — controleer Stap 4.")


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _post_service(self, domain: str, service: str, payload: dict) -> None:
        url = f"{self._base}/api/services/{domain}/{service}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self._headers, json=payload) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise RuntimeError(f"{resp.status}: {body}")

    async def set_number(self, entity_id: str, value: float) -> None:
        try:
            await self._post_service(
                "input_number",
                "set_value",
                {"entity_id": entity_id, "value": float(value)},
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"HA set_value failed for {entity_id}={value}: {exc}"
            ) from exc

    async def set_text(self, entity_id: str, value: str) -> None:
        try:
            await self._post_service(
                "input_text",
                "set_value",
                {"entity_id": entity_id, "value": str(value)},
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"HA set_value failed for {entity_id}={value!r}: {exc}"
            ) from exc

    async def push_factuur_confirm(
        self,
        form: FactuurFormValues,
        p1: P1MonthTotals,
        sessy_winst_eur: float,
    ) -> None:
        validate_factuur_numbers(form)
        month = form.factuur_maand.strip()
        if month != p1.month:
            raise ValueError(
                f"Factuurmaand {month} komt niet overeen met P1-maand {p1.month}"
            )

        vast_totaal = round(
            form.systeembeheer + form.levering + form.vermindering_eb, 2
        )
        sub_p1 = p1.netto_eur
        sub_excl = round(p1.import_eur - p1.export_eur + form.grid_rewards + vast_totaal, 2)
        btw = round(sub_excl * 0.21, 2)
        totaal_incl = round(sub_excl + btw, 2)

        await self.set_text("input_text.tibber_factuur_maand", month)
        await self.set_text("input_text.factuur_snap_periode", month)
        if form.factuur_periode.strip():
            await self.set_text(
                "input_text.tibber_factuur_periode", form.factuur_periode.strip()
            )

        await self.set_number(
            "input_number.tibber_grid_rewards_maand", form.grid_rewards
        )
        await self.set_number(
            "input_number.tibber_systeembeheer_maand", form.systeembeheer
        )
        await self.set_number("input_number.tibber_levering_maand", form.levering)
        await self.set_number(
            "input_number.tibber_vermindering_eb_maand", form.vermindering_eb
        )

        await self.set_number(
            "input_number.tibber_ref_import_excl", form.ref_import_excl
        )
        await self.set_number(
            "input_number.tibber_ref_export_credit_excl", form.ref_export_credit_excl
        )
        await self.set_number(
            "input_number.tibber_ref_grid_rewards_excl", form.ref_grid_rewards_excl
        )
        await self.set_number("input_number.tibber_ref_vast_excl", form.ref_vast_excl)
        await self.set_number(
            "input_number.tibber_ref_totaal_incl_btw", form.ref_totaal_incl_btw
        )
        await self.set_number(
            "input_number.tibber_ref_import_kwh", form.ref_import_kwh
        )
        await self.set_number(
            "input_number.tibber_ref_export_kwh", form.ref_export_kwh
        )

        await self.set_number("input_number.factuur_snap_import_excl", p1.import_eur)
        await self.set_number("input_number.factuur_snap_export_excl", p1.export_eur)
        await self.set_number("input_number.factuur_snap_import_kwh", p1.import_kwh)
        await self.set_number("input_number.factuur_snap_export_kwh", p1.export_kwh)
        await self.set_number("input_number.factuur_snap_netto", p1.netto_eur)
        await self.set_number("input_number.factuur_snap_grid", form.grid_rewards)
        await self.set_number("input_number.factuur_snap_vast", vast_totaal)
        await self.set_number("input_number.factuur_snap_subtotaal_excl", sub_p1)
        await self.set_number("input_number.factuur_snap_btw", btw)
        await self.set_number("input_number.factuur_snap_totaal_incl", totaal_incl)

        await self.set_text("input_text.sessy_snap_winst_maand", month)
        await self.set_number("input_number.sessy_snap_winst_eur", sessy_winst_eur)
