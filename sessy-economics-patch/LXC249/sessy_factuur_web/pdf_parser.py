from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime

import pdfplumber

DUTCH_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}


@dataclass
class ParseResult:
    factuur_maand: str = ""
    factuur_periode: str = ""
    ref_import_excl: float | None = None
    ref_export_credit_excl: float | None = None
    ref_import_kwh: float | None = None
    ref_export_kwh: float | None = None
    grid_rewards: float | None = None
    ref_grid_rewards_excl: float | None = None
    systeembeheer: float | None = None
    levering: float | None = None
    vermindering_eb: float | None = None
    ref_vast_excl: float | None = None
    ref_totaal_incl_btw: float | None = None
    invoice_number: str = ""
    warnings: list[str] = field(default_factory=list)
    raw_text_preview: str = ""


def _parse_eur(s: str) -> float | None:
    s = s.strip().replace("\u2212", "-").replace("−", "-")
    s = re.sub(r"[^\d,.\-]", "", s)
    if not s or s in ("-", "-"):
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def _parse_kwh(s: str) -> float | None:
    s = re.sub(r"[^\d,.\-]", "", s.strip())
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def _detect_month(text: str) -> tuple[str, str]:
    low = text.lower()
    month_names = "|".join(re.escape(n) for n in DUTCH_MONTHS)
    # Billing period (not factuurdatum): "Stroomverbruik oktober 2026" / "Variabele kosten oktober 2026"
    m = re.search(
        rf"(?:stroomverbruik|variabele\s+kosten)\s+({month_names})\s+(20\d{{2}})\b",
        low,
    )
    if m:
        name = m.group(1)
        year = int(m.group(2))
        return f"{year:04d}-{DUTCH_MONTHS[name]:02d}", f"{name.capitalize()} {year}"
    for name, num in DUTCH_MONTHS.items():
        m = re.search(rf"\b{re.escape(name)}\s+(20\d{{2}})\b", low)
        if m:
            year = int(m.group(1))
            return f"{year:04d}-{num:02d}", f"{name.capitalize()} {year}"
    return "", ""


def _section_after(text: str, pattern: str, size: int = 1200) -> str:
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return text[m.start() : m.start() + size]


def _subtotal_excl_eur(chunk: str) -> float | None:
    """Tibber: 'Subtotaal excl. btw' then amount on next line."""
    m = re.search(
        r"Subtotaal\s+excl\.?\s*btw\s*(?:\n|\r\n?)\s*€?\s*([\-\d.,]+)",
        chunk,
        re.IGNORECASE,
    )
    if m:
        return _parse_eur(m.group(1))
    m = re.search(
        r"Subtotaal\s+excl\.?\s*btw[^\d\-−]*([\-\d.,]+)\s*€",
        chunk,
        re.IGNORECASE,
    )
    if m:
        return _parse_eur(m.group(1))
    return None


def _first_kwh_in_section(chunk: str) -> float | None:
    m = re.search(r"([\d.,]+)\s*kWh\s*à", chunk, re.IGNORECASE)
    if m:
        return _parse_kwh(m.group(1))
    return None


def _find_amount_near(text: str, label: str) -> float | None:
    """Tibber layout: 'Label <maand> <jaar> € <bedrag>' — never capture the year as €."""
    m = re.search(
        rf"{re.escape(label)}[^€]*€\s*([\-\d.,]+)",
        text,
        re.IGNORECASE,
    )
    if m:
        val = _parse_eur(m.group(1))
        if val is not None and abs(val) >= 1900:
            return None
        return val
    return None


def parse_tibber_pdf(pdf_bytes: bytes) -> ParseResult:
    out = ParseResult()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    text = "\n".join(pages)
    out.raw_text_preview = text[:4000]

    out.factuur_maand, out.factuur_periode = _detect_month(text)
    if not out.factuur_maand:
        out.warnings.append("Kon factuurmaand (YYYY-MM) niet uit PDF halen — handmatig invullen.")

    inv = re.search(r"Factuurnummer\s*[:\s]*(\d+)", text, re.I)
    if inv:
        out.invoice_number = inv.group(1)

    var_chunk = _section_after(text, r"Variabele\s+kosten")
    imp_eur = _subtotal_excl_eur(var_chunk)
    if imp_eur is None:
        m = re.search(
            r"Variabele\s+kosten[^€]*€\s*([\-\d.,]+)",
            text,
            re.IGNORECASE,
        )
        if m:
            imp_eur = _parse_eur(m.group(1))
    stroom_chunk = _section_after(text, r"Stroomverbruik\s")
    imp_kwh = _first_kwh_in_section(stroom_chunk)

    terug_chunk = _section_after(text, r"Teruglevering\s*\(productie\)")
    exp_eur = _subtotal_excl_eur(terug_chunk)
    if exp_eur is None:
        m = re.search(
            r"Teruglevering\s*\(productie\)[^€]*€\s*([\-\d.,]+)",
            text,
            re.IGNORECASE,
        )
        if m:
            exp_eur = _parse_eur(m.group(1))
    prod_chunk = _section_after(text, r"Productie\s+oktober|Productie\s+\w+\s+20\d{2}")
    exp_kwh = _first_kwh_in_section(prod_chunk)

    if imp_eur is not None:
        out.ref_import_excl = imp_eur
    if imp_kwh is not None:
        out.ref_import_kwh = imp_kwh
    if exp_eur is not None:
        out.ref_export_credit_excl = exp_eur
    if exp_kwh is not None:
        out.ref_export_kwh = exp_kwh

    out.grid_rewards = _find_amount_near(text, "Grid Rewards")
    out.systeembeheer = _find_amount_near(text, "Systeembeheerkosten")
    out.levering = _find_amount_near(text, "Vaste leveringskosten")
    out.vermindering_eb = _find_amount_near(text, "Vermindering energiebelasting")

    vast_sub = _subtotal_excl_eur(_section_after(text, r"Vaste\s+leveringskosten"))
    if vast_sub is None:
        m = re.search(
            r"Vaste\s+kosten[^€]*€\s*([\-\d.,]+)",
            text,
            re.IGNORECASE,
        )
        if m:
            vast_sub = _parse_eur(m.group(1))
    if vast_sub is not None:
        out.ref_vast_excl = vast_sub

    tot = re.search(
        r"Totaal\s+incl\.?\s*btw\s*(?:\n|\r\n?)\s*€?\s*([\d.,]+)",
        text,
        re.I,
    )
    if not tot:
        tot = re.search(r"Totaal\s+incl\.?\s*btw[^\d]*([\d.,]+)\s*€", text, re.I)
    if tot:
        out.ref_totaal_incl_btw = _parse_eur(tot.group(1))

    if out.grid_rewards is not None and out.ref_grid_rewards_excl is None:
        out.ref_grid_rewards_excl = out.grid_rewards

    missing = [
        name
        for name, val in (
            ("import €", out.ref_import_excl),
            ("export €", out.ref_export_credit_excl),
            ("import kWh", out.ref_import_kwh),
            ("export kWh", out.ref_export_kwh),
            ("totaal incl BTW", out.ref_totaal_incl_btw),
        )
        if val is None
    ]
    if missing:
        out.warnings.append(
            "Niet automatisch gevonden: " + ", ".join(missing) + " — controleer PDF naast velden."
        )

    return out


def parse_result_to_form_defaults(pr: ParseResult) -> dict[str, str | float]:
    def f(v: float | None) -> float:
        return float(v) if v is not None else 0.0

    return {
        "factuur_maand": pr.factuur_maand,
        "factuur_periode": pr.factuur_periode,
        "grid_rewards": f(pr.grid_rewards),
        "systeembeheer": f(pr.systeembeheer),
        "levering": f(pr.levering),
        "vermindering_eb": f(pr.vermindering_eb),
        "ref_import_excl": f(pr.ref_import_excl),
        "ref_export_credit_excl": f(pr.ref_export_credit_excl),
        "ref_grid_rewards_excl": f(pr.ref_grid_rewards_excl or pr.grid_rewards),
        "ref_vast_excl": f(pr.ref_vast_excl),
        "ref_totaal_incl_btw": f(pr.ref_totaal_incl_btw),
        "ref_import_kwh": f(pr.ref_import_kwh),
        "ref_export_kwh": f(pr.ref_export_kwh),
    }


def current_yyyy_mm() -> str:
    return datetime.now().strftime("%Y-%m")
