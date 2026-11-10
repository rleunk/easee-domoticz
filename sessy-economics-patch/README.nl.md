# Sessy Economics — Tibber-factuur fix (P1-registers + PDF)

## Probleem

1. **P1-maand kWh** in engine/factuur-web kwamen uit **integratie van `power_consumed` / `power_produced` (W)**. Dat wijkt af van **DSMR-tellerstanden** (zelfde bron als Tibber) — bij jou o.a. ~692 vs 581 kWh import en ~194 vs 83 kWh export (okt 2026).
2. **PDF-parser** zocht kWh op de subtotaalregel; bij Tibber staat kWh op **Productie** / **Stroomverbruik** (`82,76 kWh à …`). Daardoor werd **export kWh = 0** in Vergelijk.

## Oplossing

- **kWh**: delta op `power_consumed_tariff1+2` en `power_produced_tariff1+2` (Wh) uit `/api/v2/p1/details`.
- **€**: ongewijzigd Tibber-split per interval, maar over **register-kWh** i.p.v. vermogensintegratie.
- **PDF**: correcte extractie voor factuur 1475464 en vergelijkbare layout.

## Deploy op LXC `.249` (engine + factuur-web)

Kopieer vanuit deze map naar jouw live `ha-sessy-economics/LXC249/` (WinSCP):

| Patch-bestand | Naar |
|---------------|------|
| `LXC249/vendor/sessy_economics/p1_registers.py` | **nieuw** |
| `LXC249/vendor/sessy_economics/api.py` | overschrijven |
| `LXC249/vendor/sessy_economics/p1_accounting.py` | overschrijven |
| `LXC249/sessy_economics_engine/runner.py` | overschrijven |
| `LXC249/sessy_factuur_web/pdf_parser.py` | overschrijven |
| `LXC249/sessy_factuur_web/p1_month.py` | overschrijven |

### Handmatige 2 regels in bestaande bestanden

**`vendor/sessy_economics/pricing.py`** — in `@dataclass class PriceContext`:

```python
    p1_import_register_wh: int | None = None
    p1_export_register_wh: int | None = None
```

**`vendor/sessy_economics/economics.py`**:

1. In `async def process(...)` voeg parameters toe:  
   `p1_import_register_wh: int | None = None`, `p1_export_register_wh: int | None = None`
2. Bij `update_p1_accounting(...)`:

```python
        p1_import_register_wh=p1_import_register_wh,
        p1_export_register_wh=p1_export_register_wh,
```

(Zelfde wijziging in HA `custom_components/sessy_economics/` als je daar nog een kopie draait.)

### Engine herstarten

```bash
cd /opt/sessy-economics-engine   # of jouw LXC249 pad
docker compose up -d --build
docker compose restart sessy-factuur-web
```

### Oktober 2026 in de DB

De **oude** `p1_daily`-regels voor `2026-10` blijven fout tot je ze vervangt. Na deploy:

1. Upload **Factuur_1475464.pdf** opnieuw (Stap 4 moet **82,76** export kWh tonen).
2. Voor **gesloten oktober**: vergelijk kWh eerst via **Tibber-app** vs **HA Energy** (utility meter).  
   Optioneel: wis alleen oktober in `p1_daily` en herbereken niet (historische register-delta ontbreekt tenzij je register-log hebt). **Vanaf deploy** lopen nieuwe maanden wel gelijk met Tibber.

## Verwachting na fix

- **Lopende maand**: P1 kWh in dashboard ≈ Tibber-app (± kleine polling-delay).
- **Vergelijk**: PDF-kant correct (581 / 83 kWh); engine-kant volgt na verloop van tijd; oktober pas na handmatige correctie of nieuwe maand.
