"""Integrate P1 into kWh and € (Tibber-style split).

kWh: prefer DSMR register deltas (same basis as Tibber). Fallback: integrate W.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from .database import P1_DIRECTION_EXPORT, P1_DIRECTION_IMPORT, SessyEconomicsDatabase
from .p1_registers import (
    STATE_P1_LAST_EXPORT_REGISTER_WH,
    STATE_P1_LAST_IMPORT_REGISTER_WH,
    delta_kwh,
)
from .pricing import PriceResolver

_LOGGER = logging.getLogger(__name__)

STATE_P1_LAST_TS = "p1_last_poll_ts"
MAX_P1_GAP_S = 3600.0


@dataclass(frozen=True)
class P1Totals:
    """P1 energy and cost aggregates for dashboard / invoice-style view."""

    import_kwh_today: float
    export_kwh_today: float
    import_spot_eur_today: float
    import_fee_eur_today: float
    import_tax_eur_today: float
    import_cost_today: float
    export_spot_eur_today: float
    export_fee_eur_today: float
    export_sales_fee_eur_today: float
    export_tax_eur_today: float
    export_revenue_today: float
    net_today: float
    import_cost_live_eur_h: float
    export_revenue_live_eur_h: float
    import_kwh_month: float
    export_kwh_month: float
    import_spot_eur_month: float
    import_fee_eur_month: float
    import_tax_eur_month: float
    import_cost_month: float
    export_spot_eur_month: float
    export_fee_eur_month: float
    export_sales_fee_eur_month: float
    export_tax_eur_month: float
    export_revenue_month: float
    net_month: float


def _day_key(since_today: datetime) -> str:
    return since_today.astimezone().date().isoformat()


def _month_key(since_today: datetime) -> str:
    local = since_today.astimezone()
    return f"{local.year:04d}-{local.month:02d}"


async def _apply_import_delta(
    db: SessyEconomicsDatabase,
    pricing: PriceResolver,
    import_kwh: float,
) -> None:
    import_tariff = pricing.import_tariff()
    import_all_in = pricing.import_price() or 0.0
    if import_kwh <= 1e-9:
        return
    if import_tariff is not None:
        _, spot, fee, tax, total = import_tariff.apply_import(import_kwh)
        await db.add_p1_daily_delta(
            direction=P1_DIRECTION_IMPORT,
            energy_kwh=import_kwh,
            spot_eur=spot,
            purchase_fee_eur=fee,
            sales_fee_eur=0.0,
            energy_tax_eur=tax,
            total_eur=total,
        )
    elif import_all_in > 0:
        await db.add_p1_daily_delta(
            direction=P1_DIRECTION_IMPORT,
            energy_kwh=import_kwh,
            spot_eur=0.0,
            purchase_fee_eur=0.0,
            sales_fee_eur=0.0,
            energy_tax_eur=0.0,
            total_eur=import_kwh * import_all_in,
        )


async def _apply_export_delta(
    db: SessyEconomicsDatabase,
    pricing: PriceResolver,
    export_kwh: float,
) -> None:
    export_tariff = pricing.export_tariff()
    export_all_in = pricing.export_price() or 0.0
    if export_kwh <= 1e-9:
        return
    if export_tariff is not None:
        _, spot, fee, sales, tax, total = export_tariff.apply_export(export_kwh)
        await db.add_p1_daily_delta(
            direction=P1_DIRECTION_EXPORT,
            energy_kwh=export_kwh,
            spot_eur=spot,
            purchase_fee_eur=fee,
            sales_fee_eur=sales,
            energy_tax_eur=tax,
            total_eur=total,
        )
    elif export_all_in > 0:
        await db.add_p1_daily_delta(
            direction=P1_DIRECTION_EXPORT,
            energy_kwh=export_kwh,
            spot_eur=export_kwh * export_all_in,
            purchase_fee_eur=0.0,
            sales_fee_eur=0.0,
            energy_tax_eur=0.0,
            total_eur=export_kwh * export_all_in,
        )


async def _integrate_from_registers(
    db: SessyEconomicsDatabase,
    pricing: PriceResolver,
    *,
    import_register_wh: int,
    export_register_wh: int,
) -> None:
    last_imp_raw = await db.get_state(STATE_P1_LAST_IMPORT_REGISTER_WH)
    last_exp_raw = await db.get_state(STATE_P1_LAST_EXPORT_REGISTER_WH)
    if last_imp_raw is not None and last_exp_raw is not None:
        import_kwh = delta_kwh(import_register_wh, float(last_imp_raw))
        export_kwh = delta_kwh(export_register_wh, float(last_exp_raw))
        await _apply_import_delta(db, pricing, import_kwh)
        await _apply_export_delta(db, pricing, export_kwh)
    await db.set_state(
        STATE_P1_LAST_IMPORT_REGISTER_WH, str(import_register_wh), commit=False
    )
    await db.set_state(
        STATE_P1_LAST_EXPORT_REGISTER_WH, str(export_register_wh), commit=False
    )


async def _integrate_from_power(
    db: SessyEconomicsDatabase,
    pricing: PriceResolver,
    *,
    imp_w: int,
    exp_w: int,
    now_ts: float,
) -> None:
    last_ts_raw = await db.get_state(STATE_P1_LAST_TS)
    if not last_ts_raw:
        await db.set_state(STATE_P1_LAST_TS, str(now_ts), commit=False)
        return
    dt_s = min(MAX_P1_GAP_S, max(0.0, now_ts - float(last_ts_raw)))
    if dt_s <= 0:
        return
    import_kwh = (imp_w * dt_s) / 3_600_000.0
    export_kwh = (exp_w * dt_s) / 3_600_000.0
    await _apply_import_delta(db, pricing, import_kwh)
    await _apply_export_delta(db, pricing, export_kwh)
    await db.set_state(STATE_P1_LAST_TS, str(now_ts), commit=False)


async def update_p1_accounting(
    db: SessyEconomicsDatabase,
    pricing: PriceResolver,
    *,
    p1_import_w: int | None,
    p1_export_w: int | None,
    p1_import_register_wh: int | None = None,
    p1_export_register_wh: int | None = None,
    now: datetime,
    since_today: datetime,
) -> P1Totals:
    """Update P1 daily/monthly totals (Tibber-comparable kWh when registers present)."""
    imp_w = max(0, p1_import_w or 0)
    exp_w = max(0, p1_export_w or 0)
    import_all_in = pricing.import_price() or 0.0
    export_all_in = pricing.export_price() or 0.0

    day_key = _day_key(since_today)
    month_key = _month_key(since_today)
    try:
        await db.ensure_p1_day(day_key)
    except Exception as err:
        _LOGGER.warning("P1 day rollover skipped: %s", err)

    now_ts = now.timestamp()
    if (
        p1_import_register_wh is not None
        and p1_export_register_wh is not None
    ):
        try:
            await _integrate_from_registers(
                db,
                pricing,
                import_register_wh=p1_import_register_wh,
                export_register_wh=p1_export_register_wh,
            )
        except Exception as err:
            _LOGGER.warning("P1 register integration failed: %s", err)
    elif p1_import_w is not None or p1_export_w is not None:
        await _integrate_from_power(
            db, pricing, imp_w=imp_w, exp_w=exp_w, now_ts=now_ts
        )

    summary = await db.get_p1_summary(day_key, month_key)
    return P1Totals(
        import_kwh_today=summary["import_kwh_today"],
        export_kwh_today=summary["export_kwh_today"],
        import_spot_eur_today=summary["import_spot_eur_today"],
        import_fee_eur_today=summary["import_fee_eur_today"],
        import_tax_eur_today=summary["import_tax_eur_today"],
        import_cost_today=summary["import_cost_today"],
        export_spot_eur_today=summary["export_spot_eur_today"],
        export_fee_eur_today=summary["export_fee_eur_today"],
        export_sales_fee_eur_today=summary["export_sales_fee_eur_today"],
        export_tax_eur_today=summary["export_tax_eur_today"],
        export_revenue_today=summary["export_revenue_today"],
        net_today=summary["net_today"],
        import_cost_live_eur_h=(imp_w / 1000.0) * import_all_in,
        export_revenue_live_eur_h=(exp_w / 1000.0) * export_all_in,
        import_kwh_month=summary["import_kwh_month"],
        export_kwh_month=summary["export_kwh_month"],
        import_spot_eur_month=summary["import_spot_eur_month"],
        import_fee_eur_month=summary["import_fee_eur_month"],
        import_tax_eur_month=summary["import_tax_eur_month"],
        import_cost_month=summary["import_cost_month"],
        export_spot_eur_month=summary["export_spot_eur_month"],
        export_fee_eur_month=summary["export_fee_eur_month"],
        export_sales_fee_eur_month=summary["export_sales_fee_eur_month"],
        export_tax_eur_month=summary["export_tax_eur_month"],
        export_revenue_month=summary["export_revenue_month"],
        net_month=summary["net_month"],
    )
