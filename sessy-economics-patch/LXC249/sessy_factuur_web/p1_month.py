from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class P1Breakdown:
    direction: str
    kwh: float
    spot_eur: float
    purchase_fee_eur: float
    sales_fee_eur: float
    energy_tax_eur: float
    total_eur: float


@dataclass
class P1MonthTotals:
    month: str
    days: int
    import_eur: float
    export_eur: float
    import_kwh: float
    export_kwh: float
    netto_eur: float
    breakdown: list[P1Breakdown]


def _month_day_bounds(month: str) -> tuple[str, str]:
    """Inclusive start day, exclusive end day (ISO dates)."""
    year_s, month_s = month.split("-")
    year, mon = int(year_s), int(month_s)
    start = f"{month}-01"
    if mon == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year:04d}-{mon + 1:02d}-01"
    return start, end


def _query_month(conn: sqlite3.Connection, month: str) -> P1MonthTotals:
    day_start, day_end = _month_day_bounds(month)
    imp_eur, exp_eur, imp_kwh, exp_kwh, days = conn.execute(
        """
        SELECT
          COALESCE(ROUND((SELECT SUM(total_eur) FROM p1_daily
            WHERE day >= ? AND day < ? AND direction = 'import'), 2), 0),
          COALESCE(ROUND((SELECT SUM(total_eur) FROM p1_daily
            WHERE day >= ? AND day < ? AND direction = 'export'), 2), 0),
          COALESCE(ROUND((SELECT SUM(energy_kwh) FROM p1_daily
            WHERE day >= ? AND day < ? AND direction = 'import'), 3), 0),
          COALESCE(ROUND((SELECT SUM(energy_kwh) FROM p1_daily
            WHERE day >= ? AND day < ? AND direction = 'export'), 3), 0),
          (SELECT COUNT(DISTINCT day) FROM p1_daily
            WHERE day >= ? AND day < ?)
        """,
        (
            day_start,
            day_end,
            day_start,
            day_end,
            day_start,
            day_end,
            day_start,
            day_end,
            day_start,
            day_end,
        ),
    ).fetchone()

    breakdown_rows = conn.execute(
        """
        SELECT direction,
               ROUND(SUM(energy_kwh), 3),
               ROUND(SUM(spot_eur), 2),
               ROUND(SUM(purchase_fee_eur), 2),
               ROUND(SUM(sales_fee_eur), 2),
               ROUND(SUM(energy_tax_eur), 2),
               ROUND(SUM(total_eur), 2)
        FROM p1_daily
        WHERE day >= ? AND day < ?
        GROUP BY direction
        """,
        (day_start, day_end),
    ).fetchall()

    breakdown = [
        P1Breakdown(
            direction=row[0],
            kwh=float(row[1]),
            spot_eur=float(row[2]),
            purchase_fee_eur=float(row[3]),
            sales_fee_eur=float(row[4]),
            energy_tax_eur=float(row[5]),
            total_eur=float(row[6]),
        )
        for row in breakdown_rows
    ]

    return P1MonthTotals(
        month=month,
        days=int(days or 0),
        import_eur=float(imp_eur),
        export_eur=float(exp_eur),
        import_kwh=float(imp_kwh),
        export_kwh=float(exp_kwh),
        netto_eur=round(float(imp_eur) - float(exp_eur), 2),
        breakdown=breakdown,
    )


def load_p1_month(db_path: Path, month: str) -> P1MonthTotals:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return _query_month(conn, month)
    finally:
        conn.close()


def load_sessy_winst_month(db_path: Path, month: str) -> float:
    """FIFO arbitrage winst in calendar month (ISO timestamps in DB)."""
    year_s, month_s = month.split("-")
    year, mon = int(year_s), int(month_s)
    start = f"{month}-01T00:00:00"
    if mon == 12:
        end = f"{year + 1}-01-01T00:00:00"
    else:
        end = f"{year:04d}-{mon + 1:02d}-01T00:00:00"
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            """
            SELECT COALESCE(ROUND(SUM(profit), 2), 0)
            FROM realized_profit
            WHERE timestamp >= ? AND timestamp < ?
            """,
            (start, end),
        ).fetchone()
        return float(row[0] if row else 0.0)
    finally:
        conn.close()
