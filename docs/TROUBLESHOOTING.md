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

### Custom iconen ontbreken

**Symptoom**: Tegels tonen standaard Domoticz-iconen

**Oplossing**:
1. Controleer of `Easee_icons_v2.zip` in de pluginmap staat
2. Herstart het hardware-item
3. Als automatisch laden mislukt: upload eenmalig via **Setup → Instellingen → Meer opties → Aangepaste pictogrammen**
   - Pad: `/home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons_v2.zip`

Zie [INSTALL.md — Custom iconen](../INSTALL.md#custom-iconen-handmatig-uploaden).

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
sudo journalctl -u domoticz -f | grep "Easee v10.5.18"

# Laatste 100 regels
sudo journalctl -u domoticz -n 200 | grep Easee
```

## Performance

- Verhoog poll interval (Mode1) naar 60–120 sec bij hoog CPU-gebruik
- Zet Debug logging op *Normal* als je niet troubleshoott

## Reset state

```bash
sudo systemctl stop domoticz
rm /home/root/domoticz/plugins/Easee-Domoticz-plugin/easee_v9_0_state.json
sudo systemctl start domoticz
```

## Support

- **GitHub Issues**: https://github.com/rleunk/easee-domoticz/issues
- **Installatie**: [INSTALL.md](../INSTALL.md)
- **Domoticz Forum**: https://www.domoticz.com/forum/

Bij een issue: pluginversie (**v10.5.18**), Domoticz-versie en relevante logregels (zonder wachtwoorden/tokens).
