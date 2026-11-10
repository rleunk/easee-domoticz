"""DSMR cumulative import/export registers from Sessy P1 API (/api/v2/p1/details)."""

from __future__ import annotations

STATE_P1_LAST_IMPORT_REGISTER_WH = "p1_last_import_register_wh"
STATE_P1_LAST_EXPORT_REGISTER_WH = "p1_last_export_register_wh"


def delivered_wh(p1_details: dict) -> int | None:
    """Cumulative grid import (delivered) in Wh — tariff 1 + 2."""
    keys = ("power_consumed_tariff1", "power_consumed_tariff2")
    if not all(k in p1_details for k in keys):
        return None
    return int(p1_details.get(keys[0]) or 0) + int(p1_details.get(keys[1]) or 0)


def returned_wh(p1_details: dict) -> int | None:
    """Cumulative grid export (returned) in Wh — tariff 1 + 2."""
    keys = ("power_produced_tariff1", "power_produced_tariff2")
    if not all(k in p1_details for k in keys):
        return None
    return int(p1_details.get(keys[0]) or 0) + int(p1_details.get(keys[1]) or 0)


def delta_kwh(current_wh: int, last_wh: float) -> float:
    """Positive delta in kWh; treat meter reset as fresh cumulative."""
    if current_wh >= last_wh:
        return (current_wh - last_wh) / 1000.0
    return current_wh / 1000.0
