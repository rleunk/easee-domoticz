# Installatie Gids

## Vereisten

- ✅ Domoticz 2020.2 of hoger
- ✅ Python 3.7 of hoger
- ✅ Python `requests` library
- ✅ Easee account met laadpaal(en)
- ⚠️ Optioneel: Tibber account voor stroomtarieven

## Stap 1: Controleer Python & requests

```bash
# Check Python versie
python3 --version

# Installeer requests (als nodig)
sudo apt-get install python3-requests

# Of via pip
pip3 install requests
```

## Stap 2: Clone / Download Plugin

### Via Git
```bash
cd /home/domoticz/userdata/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee
```

### Of handmatig
1. Download ZIP van GitHub
2. Pak uit in `/home/domoticz/userdata/plugins/Easee/`

## Stap 3: Zet Permissies

```bash
chmod +x /home/domoticz/userdata/plugins/Easee/plugin.py
chown -R domoticz:domoticz /home/domoticz/userdata/plugins/Easee/
```

## Stap 4: Restart Domoticz

```bash
# Via systemctl
sudo systemctl restart domoticz

# Of handmatig
sudo service domoticz restart
```

## Stap 5: Voeg Plugin toe in UI

1. Open Domoticz web interface (`http://localhost:8080`)
2. Ga naar **Setup → Hardware**
3. Selecteer type: **"Easee AutoDiscovery Compact v9.0"**
4. Vul in:
   - **Username**: Jouw Easee username/telefoonnummer
   - **Password**: Jouw Easee wachtwoord
   - **Poll interval**: 30 (seconden)
   - **Device prefix**: Easee (of jouw voorkeur)
   - **Tibber token**: (optioneel) Jouw Tibber token
5. Klik **Create**

## Stap 6: Controleer Logs

Ga naar **Setup → Logs** en zoek naar Easee berichten:

```
[Easee v9.0] Plugin gestart
[Easee v9.0] Laadpaal X gevonden: naam
[Easee v9.0] State geladen
```

## Problemen?

Zie [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Update Procedure

```bash
cd /home/domoticz/userdata/plugins/Easee
git pull origin main
sudo systemctl restart domoticz
```
