# Troubleshooting Gids

## Veelvoorkomende Problemen

### Plugin laadt niet

**Symptoom**: *Easee Domoticz plugin* type niet beschikbaar in Hardware menu

**Oorzaken**:
- Plugin directory verkeerd geplaatst
- Python `requests` library niet geïnstalleerd
- Permissieproblemen
- Domoticz niet herstart

**Oplossing**:

```bash
# 1. Check locatie
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py

# 2. Install requests
sudo apt install -y python3-requests

# 3. Restart
sudo systemctl restart domoticz

# 4. Check logs
sudo journalctl -u domoticz -f | grep Easee
```

### Login mislukt

**Symptoom**: *Login mislukt, HTTP 401* in logs

**Oorzaken**:
- Verkeerd username/wachtwoord
- Easee account vergrendeld
- API rate limit bereikt

**Oplossing**:
1. Controleer credentials in Domoticz (**Setup → Hardware**)
2. Test of je kunt inloggen in de Easee-app
3. Zet **Debug logging** (Mode6) aan voor meer details
4. Wacht 5–10 minuten en probeer opnieuw (rate limit)

### Geen devices gemaakt

**Symptoom**: Hardware actief maar geen devices verschijnen

**Oorzaken**:
- Geen laadpalen aan account gekoppeld
- Site filter (Mode5) elimineert alle palen
- Initiële sync nog bezig

**Oplossing**:
1. Controleer Easee-app — palen zichtbaar en gekoppeld?
2. Verwijder site filter (Mode5) tijdelijk
3. Wacht 1–2 minuten na eerste start
4. Bekijk log: `sudo journalctl -u domoticz -f | grep -i "charger\|Discovery"`
5. Refresh Domoticz UI (F5)

### Custom iconen ontbreken (na reinstall of upgrade)

**Symptoom**: Tegels tonen standaard Domoticz-iconen (generiek Text-icoon, gele bliksem op Energy-tegels)

**Oorzaken**:
- `Easee_icons_v2.zip` ontbreekt in de pluginmap of automatisch laden mislukte
- v10.9.2-regressie: `refresh_images_dict()` zonder argument deed niets → `image_ids` leeg (opgelost in v10.9.3)
- Domoticz `Images`-dict niet ververst na zip-upload
- `Device.Update(Image=…)` zonder `UpdateProperties` op nieuwere Domoticz-builds
- **Energy-tegels** (*Laden*, *Totaal Laden*): sommige Domoticz-versies tonen altijd het standaard bliksem-icoon ondanks custom Image — bekende Domoticz-beperking

**Oplossing** (v10.9.5+):
1. **Verwijder eerst oude Easee custom icons** via **Instellingen → Meer opties → Aangepaste pictogrammen** (short-name bases uit v10.9.4 kunnen conflicteren)
2. Controleer of `Easee_icons_v2.zip` en map `icons/` (12 mini-zips) in de pluginmap staan
3. `git pull` naar v10.9.5+ en herstart het hardware-item
4. Zoek in het log op INFO-regels:
   - `Easee Images-keys (12): …EaseeCloudAutoDiscoveryV1000Easee…` — volledige lijst, geen sample
   - `image_ids: 12/12 sets` en `image_ids mappings: EaseeCharger=…, …`
   - Bij 1/12 sets (v10.9.4-bug): plugin-key-prefix ontbrak in zip — upgrade naar v10.9.5
5. Als automatisch laden mislukt: upload `Easee_icons_v2.zip` handmatig via **Aangepaste pictogrammen**, herstart hardware-item

**Oplossing** (v10.9.3–v10.9.4):
1. Controleer of `Easee_icons_v2.zip` in de pluginmap staat (`/home/root/domoticz/plugins/Easee-Domoticz-plugin/`)
2. Herstart het hardware-item (niet alleen Domoticz)
3. Zoek in het log op INFO-regels:
   - `Images dict: N key(s), M met "Easee"` — als M=0: zip handmatig uploaden
   - `Zip Easee_icons_v2.zip: aanwezig, X bytes`
   - `Image().Create() zip: geslaagd` of `mislukt`
   - `image_ids: 12/12 mapping(s)` — bij 0/12: ERROR met upload-instructie
   - `{tegel}: icoon gezet -> Easee…` of `overgeslagen` / `mislukt` per tegel
4. Als automatisch laden mislukt: upload eenmalig via **Setup → Instellingen → Meer opties → Aangepaste pictogrammen**
5. Status-tegel toont `⚠️ Upload Easee_icons_v2.zip` zolang iconen ontbreken
6. Na upgrade: wacht 3 heartbeats (~90s) — iconen worden opnieuw toegepast

Zie [INSTALL.md — Custom iconen](../INSTALL.md#custom-iconen-handmatig-uploaden).

### Meterkast - Import blijft bestaan (legacy Energy)

**Symptoom**: Tegel heet nog *Import* en toont `Energy 1581W` i.p.v. Text *Vermogen* met terug/netto

**Oplossing** (v10.9.2+): herstart hardware-item — plugin verwijdert legacy Energy *Import* en maakt Text *Vermogen* opnieuw aan. Controleer log op `legacy Import Energy → Text Vermogen`.

### Geen Equalizer gevonden

1. Zet **Debug logging** op *Debug* (Mode6)
2. Herstart het hardware-item en bekijk het log
3. Vul handmatig **Equalizer ID** in bij het IP-veld
4. Controleer of de Equalizer zichtbaar is in de Easee-app

Zonder Equalizer werkt de plugin volledig; Status toont `Geen EQ`.

### Tibber / kosten-tegels

**Symptoom**: Geen kosten- of tarief-tegels, of *0 €*

**Oplossing**:
- Zonder Tibber-token: kosten-tegels worden niet aangemaakt (verwacht)
- Met Tibber: controleer token op [developer.tibber.com](https://developer.tibber.com/settings/access-token)
- Kosten-tile toont *0 €* na upgrade: verwijder **Kosten (Sessie/Dag)**-tile en herstart hardware-item

### Devices dubbel na herstart

De plugin wacht bij opstarten tot Domoticz de Devices-lijst heeft geladen (minimaal 3 seconden, daarna readiness-check op bestaande Easee-devices of een stabiele device-count). Polling start pas na deze initiële sync. Als het toch gebeurt:

1. Stop het hardware-item
2. Verwijder dubbele devices handmatig
3. Start het hardware-item opnieuw

## Debug Mode

1. Ga naar **Setup → Hardware**
2. Klik op je Easee hardware-item
3. Zet **Debug logging** (Mode6) op *Debug*
4. Klik **Update**

### Logs bekijken

```bash
# Real-time
sudo journalctl -u domoticz -f | grep "Easee v"

# Laatste 100 regels
sudo journalctl -u domoticz -n 200 | grep Easee
```

## Performance

- Verhoog poll interval (Mode1) naar 60–120 sec bij hoog CPU-gebruik
- Zet Debug logging op *Normal* als je niet troubleshoott

## Reset state

```bash
sudo systemctl stop domoticz
rm /home/root/domoticz/plugins/Easee-Domoticz-plugin/easee_state.json
# Legacy na upgrade: easee_v9_0_state.json (wordt automatisch gemigreerd)
sudo systemctl start domoticz
```

## Support

- **GitHub Issues**: https://github.com/rleunk/easee-domoticz/issues
- **Installatie**: [INSTALL.md](../INSTALL.md)
- **Domoticz Forum**: https://www.domoticz.com/forum/

Bij een issue: pluginversie (bijv. **v10.9.2**), Domoticz-versie en relevante logregels (zonder wachtwoorden/tokens).
