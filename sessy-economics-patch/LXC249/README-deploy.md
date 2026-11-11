# Waarom `easee-domoticz\sessy-economics-patch\LXC249`?

De **Cloud Agent** draait alleen in de git-repo die aan Cursor gekoppeld is (`easee-domoticz`). Die VM heeft **geen toegang** tot `C:\Users\Richard\Projects\ha-sessy-economics`.

Daarom ligt hier een **spiegel** van de LXC-map: dezelfde mappen (`vendor/`, `sessy_economics_engine/`, `sessy_factuur_web/`), bedoeld om naar jouw echte project te kopiëren.

**Jouw canonieke map:** `C:\Users\Richard\Projects\ha-sessy-economics\LXC249`  
**Upload op de server:** `/opt/sessy-economics-engine`

## Eerst: nieuwste patch ophalen (anders ontbreekt het .ps1-script)

```powershell
cd C:\Users\Richard\Projects\easee-domoticz
git fetch origin cursor/sessy-p1-tibber-match-368d
git checkout cursor/sessy-p1-tibber-match-368d
git pull
```

De patch bevat **alleen gewijzigde** bestanden, geen volledige `vendor/`. Kopieer die **over** je bestaande `ha-sessy-economics\LXC249` (database, fifo, enz. blijven staan).

```powershell
cd C:\Users\Richard\Projects\easee-domoticz\sessy-economics-patch\LXC249
.\sync-naar-ha-sessy-economics.cmd
```

Of handmatig één bestand:

```powershell
Copy-Item -Force `
  C:\Users\Richard\Projects\easee-domoticz\sessy-economics-patch\LXC249\vendor\sessy_economics\economics.py `
  C:\Users\Richard\Projects\ha-sessy-economics\LXC249\vendor\sessy_economics\economics.py
```

**Rechtstreeks op LXC** (als GitHub bereikbaar is):

```bash
curl -fsSL -o /opt/sessy-economics-engine/vendor/sessy_economics/economics.py \
  'https://raw.githubusercontent.com/rleunk/easee-domoticz/cursor/sessy-p1-tibber-match-368d/sessy-economics-patch/LXC249/vendor/sessy_economics/economics.py'
head -3 /opt/sessy-economics-engine/vendor/sessy_economics/economics.py
```

## LXC: engine herstellen (kapotte `economics.py`)

Op de server moet regel 1 van `economics.py` een **docstring** zijn, niet `p1_import_cost_month`.

1. WinSCP: upload `vendor/sessy_economics/economics.py` naar `/opt/sessy-economics-engine/vendor/sessy_economics/`
2. Controle:

   ```bash
   head -3 /opt/sessy-economics-engine/vendor/sessy_economics/economics.py
   ```

3. **Controleer dat `vendor/` niet leeg is** (build-context ~1 kB = bijna zeker kapot):

   ```bash
   find /opt/sessy-economics-engine/vendor -name '*.py' | wc -l
   ```

   Verwacht **meer dan ~15** `.py`-bestanden. Zo niet: upload de **hele** map  
   `ha-sessy-economics\LXC249\vendor` via WinSCP, en daarna opnieuw stap 1 (economics.py).

4. **Rebuild zonder cache**:

   ```bash
   cd /opt/sessy-economics-engine
   docker compose build --no-cache sessy-economics-engine
   docker compose up -d sessy-economics-engine
   docker compose logs --tail=20 sessy-economics-engine
   ```

Gefixte file ook op GitHub: branch `cursor/sessy-p1-tibber-match-368d`, pad `sessy-economics-patch/LXC249/vendor/sessy_economics/economics.py`.

## Factuur-web: `400 Bad Request` bij Bevestigen

Meestal twee oorzaken:

1. **Stap 3 toont `2026,0` bij €-velden** — oude PDF-parser pakte het **jaar** i.p.v. het bedrag. HA weigert `input_number` buiten min/max (bv. 2026 > 100).
2. **Helpers ontbreken** in HA — package `helpers_factuur.yaml` op .48/.49 moet geladen zijn.

**Parser + HA-client op LXC:**

```bash
BR=cursor/sessy-p1-tibber-match-368d
BASE=https://raw.githubusercontent.com/rleunk/easee-domoticz/$BR/sessy-economics-patch/LXC249
curl -fsSL -o /opt/sessy-economics-engine/sessy_factuur_web/pdf_parser.py \
  "$BASE/sessy_factuur_web/pdf_parser.py"
curl -fsSL -o /opt/sessy-economics-engine/sessy_factuur_web/ha_client.py \
  "$BASE/sessy_factuur_web/ha_client.py"
docker compose build --no-cache sessy-factuur-web
docker compose up -d sessy-factuur-web
```

Daarna **PDF opnieuw uploaden** (of Stap 3 handmatig: Grid Rewards **−0,74**, systeem **33,4**, levering **4,95**, vermindering **−44,15**, ref vast **−5,8**).

Oktober 2026 ref-waarden staan in `tests/test_pdf_1475464.py`.
