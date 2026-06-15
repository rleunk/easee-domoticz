# Troubleshooting Gids

## Veelvoorkomende Problemen

### Plugin laadt niet

**Symptoom**: "Easee" type niet beschikbaar in Hardware menu

**Oorzaken**:
- ❌ Plugin directory verkeerd geplaatst
- ❌ Python requests library niet geïnstalleerd
- ❌ Permissie problemen
- ❌ Domoticz niet gerestart

**Oplossing**:
```bash
# 1. Check locatie
ls -la /home/domoticz/userdata/plugins/Easee/

# 2. Install requests
sudo apt-get install python3-requests

# 3. Fix permissions
chown -R domoticz:domoticz /home/domoticz/userdata/plugins/Easee/

# 4. Restart
sudo systemctl restart domoticz

# 5. Check logs
sudo tail -f /home/domoticz/domoticz.log | grep Easee
```

### Login mislukt

**Symptoom**: "Login mislukt, HTTP 401" in logs

**Oorzaken**:
- ❌ Verkeerd username/wachtwoord
- ❌ Easee account vergrendeld
- ❌ API rate limit bereikt

**Oplossing**:
```bash
# 1. Controleer credentials in Domoticz UI
# 2. Test direct
curl -X POST https://api.easee.com/api/accounts/login \
  -H "Content-Type: application/json" \
  -d '{"userName":"test@example.com","password":"pass"}'

# 3. Controleer Easee account status
#    Login op https://easee.com

# 4. Wait 5-10 minutes en retry (rate limit)
```

### Geen devices gemaakt

**Symptoom**: Hardware actief maar geen devices verschijnen

**Oorzaken**:
- ❌ Geen laadpalen aan account gekoppeld
- ❌ Site filter elimineert alle palen
- ❌ Initiële sync nog aan het lopen

**Oplossing**:
```bash
# 1. Check Easee app/website
#    - Zeker dat palen zichtbaar zijn?
#    - Palen correct gekoppeld?

# 2. Verwijder site filter (Mode5)

# 3. Controleer logs
sudo tail -f /home/domoticz/domoticz.log | grep "Discovery\|charger"

# 4. Wacht 1-2 minuten voor initiële sync

# 5. Refresh Domoticz UI (F5)
```

### Verkeerde waarden

**Symptoom**: Devices tonen rare getallen, niet-realistisch vermogen

**Oorzaken**:
- ❌ Easee API teruggave onverwacht format
- ❌ Data conversie fout
- ❌ Verbindingsprobleem

**Oplossing**:
```bash
# 1. Enable Debug modus
#    Mode6 = "Debug"

# 2. Controleer logs voor stack traces
sudo tail -f /home/domoticz/domoticz.log | grep "Easee v10.1.0"

# 3. Controleer API response
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.easee.com/api/chargers

# 4. Report issue op GitHub met logs
```

## Performance Issues

### Hoog CPU gebruik

**Symptoom**: Domoticz neemt veel CPU in

**Oplossing**:
```bash
# 1. Verhoog poll interval
#    Mode1 van 30 naar 60-120 seconden

# 2. Disable Debug modus
#    Mode6 = "Normal"

# 3. Monitor
top -p $(pidof domoticz)
```

### Slow/Laggy Domoticz

**Symptoom**: UI traag, pages laden langzaam

**Oplossing**:
```bash
# 1. Check disk space
df -h /home/domoticz/

# 2. Cleanup old logs
# rm /home/domoticz/domoticz.log.* (keep 1-2)

# 3. Verify database
# cd /home/domoticz && sqlite3 domoticz.db "VACUUM;"

# 4. Increase poll interval
```

## Tibber Issues

### Tibber token werkt niet

**Symptoom**: "Tibber query http 401" of prijs data verschijnt niet

**Oplossing**:
```bash
# 1. Controleer token
#    - Nog geldig?
#    - Goede scope (read)?

# 2. Test direct
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"{ viewer { homes { id } } }"}' \
  https://api.tibber.com/v1-beta/gql

# 3. Token regenerate op https://developer.tibber.com

# 4. Update in Domoticz (Mode7)
```

### Tibber disabled

**Symptoom**: "Tibber actief" staat altijd uit

**Oplossing**:
- Zet token in Mode7
- Restart plugin (via hardware)
- Wacht 1-2 poll cycles

## Debug Mode

### Enable Debug Logging

1. Ga naar Setup → Hardware
2. Klik op "Easee AutoDiscovery v10.1.0"
3. Zet Mode6 = "Debug"
4. Klik Update

### Bekijk Logs

```bash
# Real-time logs
sudo tail -f /home/domoticz/domoticz.log | grep "Easee"

# Search specific error
sudo grep "Easee v10.1.0.*error" /home/domoticz/domoticz.log

# Last 100 lines
sudo tail -100 /home/domoticz/domoticz.log | grep "Easee"
```

## Advanced Debugging

### Test API Manually

```bash
# 1. Get access token
TOKEN=$(curl -s -X POST https://api.easee.com/api/accounts/login \
  -H "Content-Type: application/json" \
  -d '{"userName":"user@example.com","password":"pass"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['accessToken'])")

# 2. Get chargers
curl -H "Authorization: Bearer $TOKEN" \
  https://api.easee.com/api/chargers | python3 -m json.tool

# 3. Get charger state
curl -H "Authorization: Bearer $TOKEN" \
  https://api.easee.com/api/chargers/CHARGER_ID/state | python3 -m json.tool
```

### Reset State

Wil je alles reset?

```bash
# 1. Stop Domoticz
sudo systemctl stop domoticz

# 2. Verwijder state file
rm /home/domoticz/userdata/plugins/Easee/easee_v9_0_state.json

# 3. Optioneel: verwijder devices en start opnieuw
# In Domoticz UI: Hardware → Edit → Delete

# 4. Start opnieuw
sudo systemctl start domoticz

# 5. Re-add hardware
```

## Contacteer Support

Heb je nog steeds probleem? Open een issue:

- 🐛 **GitHub Issues**: https://github.com/rleunk/easee-domoticz/issues
- 💬 **Domoticz Forum**: https://www.domoticz.com/forum/
- 📧 **Easee Support**: https://easee.com/support

Include:
- Plugin versie (v10.1.0)
- Domoticz versie (`cat /home/domoticz/Version.txt`)
- Relevante logs (met sensieve data verwijderd)
- Stappen om te reproduceren
