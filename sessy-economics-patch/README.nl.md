# Sessy Economics — Tibber-factuur fix (P1-registers + PDF)

## Probleem

1. **P1-maand kWh** in engine/factuur-web kwamen uit **integratie van `power_consumed` / `power_produced` (W)**. Dat wijkt af van **DSMR-tellerstanden** (zelfde bron als Tibber) — bij jou o.a. ~692 vs 581 kWh import en ~194 vs 83 kWh export (okt 2026).
2. **PDF-parser** zocht kWh op de subtotaalregel; bij Tibber staat kWh op **Productie** / **Stroomverbruik** (`82,76 kWh à …`). Daardoor werd **export kWh = 0** in Vergelijk.

## Oplossing

- **kWh**: delta op `power_consumed_tariff1+2` en `power_produced_tariff1+2` (Wh) uit `/api/v2/p1/details`.
- **€**: ongewijzigd Tibber-split per interval, maar over **register-kWh** i.p.v. vermogensintegratie.
- **PDF**: correcte extractie voor factuur 1475464 en vergelijkbare layout.

## Lokaal op je PC (`C:\Users\Richard\Projects\ha-sessy-economics\LXC249`)

Vanaf **easee-domoticz** (branch `cursor/sessy-p1-tibber-match-368d`):

```powershell
cd C:\Users\Richard\Projects\easee-domoticz
git fetch
git checkout cursor/sessy-p1-tibber-match-368d
git pull

# Optie A — ExecutionPolicy omzeilen (aanbevolen):
powershell -NoProfile -ExecutionPolicy Bypass -File .\sessy-economics-patch\apply-to-local-LXC249.ps1

# Optie B — dubbelklik:
#   sessy-economics-patch\apply-to-local-LXC249.cmd
```

Dat overschrijft de gewijzigde bestanden in je **bestaande** `ha-sessy-economics\LXC249` (config/docker blijven staan).

**Cursor lokaal:** daarna map `C:\Users\Richard\Projects\ha-sessy-economics` openen — daar staat de code weer zoals eerder.

## Deploy op LXC `.249` (engine + factuur-web)

Kopieer vanuit `ha-sessy-economics\LXC249` naar de LXC (WinSCP), of git pull op de server als je dat daar ook gebruikt:

| Patch-bestand | Naar |
|---------------|------|
| `LXC249/vendor/sessy_economics/p1_registers.py` | **nieuw** |
| `LXC249/vendor/sessy_economics/api.py` | overschrijven |
| `LXC249/vendor/sessy_economics/p1_accounting.py` | overschrijven |
| `LXC249/vendor/sessy_economics/pricing.py` | overschrijven |
| `LXC249/vendor/sessy_economics/economics.py` | overschrijven |
| `LXC249/sessy_economics_engine/runner.py` | overschrijven |
| `LXC249/sessy_factuur_web/pdf_parser.py` | overschrijven |
| `LXC249/sessy_factuur_web/p1_month.py` | overschrijven |

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
