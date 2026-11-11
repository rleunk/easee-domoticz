# Waarom `easee-domoticz\sessy-economics-patch\LXC249`?

De **Cloud Agent** draait alleen in de git-repo die aan Cursor gekoppeld is (`easee-domoticz`). Die VM heeft **geen toegang** tot `C:\Users\Richard\Projects\ha-sessy-economics`.

Daarom ligt hier een **spiegel** van de LXC-map: dezelfde mappen (`vendor/`, `sessy_economics_engine/`, `sessy_factuur_web/`), bedoeld om naar jouw echte project te kopiëren.

**Jouw canonieke map:** `C:\Users\Richard\Projects\ha-sessy-economics\LXC249`  
**Upload op de server:** `/opt/sessy-economics-engine`

## Windows: patch → ha-sessy-economics

```powershell
cd C:\Users\Richard\Projects\easee-domoticz\sessy-economics-patch\LXC249
powershell -ExecutionPolicy Bypass -File .\sync-naar-ha-sessy-economics.ps1
```

## LXC: engine herstellen (kapotte `economics.py`)

Op de server moet regel 1 van `economics.py` een **docstring** zijn, niet `p1_import_cost_month`.

1. WinSCP: upload `vendor/sessy_economics/economics.py` naar `/opt/sessy-economics-engine/vendor/sessy_economics/`
2. Controle:

   ```bash
   head -3 /opt/sessy-economics-engine/vendor/sessy_economics/economics.py
   ```

3. **Rebuild zonder cache** (anders blijft Docker de oude laag gebruiken):

   ```bash
   cd /opt/sessy-economics-engine
   docker compose build --no-cache sessy-economics-engine
   docker compose up -d sessy-economics-engine
   docker compose logs --tail=20 sessy-economics-engine
   ```

Gefixte file ook op GitHub: branch `cursor/sessy-p1-tibber-match-368d`, pad `sessy-economics-patch/LXC249/vendor/sessy_economics/economics.py`.
