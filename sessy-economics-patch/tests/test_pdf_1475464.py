from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "LXC249" / "sessy_factuur_web"))

from pdf_parser import parse_tibber_pdf  # noqa: E402

PDF = Path(
    "/home/ubuntu/.cursor/projects/agent-repos-easee-domoticz/uploads/Factuur_1475464_5bc8.pdf"
)


def test_tibber_1475464_values():
    assert PDF.is_file(), f"missing fixture {PDF}"
    pr = parse_tibber_pdf(PDF.read_bytes())
    assert pr.factuur_maand == "2026-10"
    assert pr.grid_rewards == -0.74
    assert pr.ref_vast_excl == -5.8
    assert pr.systeembeheer == 33.4
    assert pr.ref_import_excl == 144.83
    assert pr.ref_export_credit_excl == -25.69
    assert pr.ref_import_kwh == 581.41
    assert pr.ref_export_kwh == 82.76
    assert pr.ref_totaal_incl_btw == 136.25
