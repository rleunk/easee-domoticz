# Configuratie Gids

## Basis Parameters

### Username (Verplicht)
**Type**: Text  
**Default**: -  
**Omschrijving**: Je Easee account username of telefoonnummer  
**Voorbeeld**: `test@example.com` of `+31612345678`

### Password (Verplicht)
**Type**: Password  
**Default**: -  
**Omschrijving**: Je Easee account wachtwoord  
**Opmerking**: Wordt veilig opgeslagen in Domoticz

## Geavanceerde Instellingen

### Poll Interval (Mode1)
**Type**: Integer  
**Default**: 30  
**Range**: 10 - 3600 seconden  
**Omschrijving**: Hoe vaak de plugin Easee API raadpleegt  
**Aanbeveling**:
- 30 sec = normaal gebruik (default)
- 60 sec = lager CPU gebruik
- 10 sec = realtime updates (meer CPU)

### Device Prefix (Mode4)
**Type**: Text  
**Default**: Easee  
**Omschrijving**: Prefix voor alle aangemaakt devices  
**Voorbeeld**: 
- Easee → "Easee - Status", "Easee - Totaal Laden"
- EV → "EV - Status", "EV - Totaal Laden"

### Site Filter (Mode5)
**Type**: Text  
**Default**: (empty)  
**Omschrijving**: Optionele filter op sitenaam/laadpaalnaam  
**Voorbeeld**:
- Leeg = alle laadpalen
- "Thuis" = alleen laadpalen met "Thuis" in de naam
- "Kantoor" = alleen kantoor laadpalen

### Debug Logging (Mode6)
**Type**: Select  
**Options**: Normal / Debug  
**Default**: Normal  
**Omschrijving**: Verbositeit van logging  
**Debug**: Extra gedetailleerde logs voor troubleshooting

## Aangepaste laadpaalnamen (optioneel)

### Naam laadpaal 1 (Mode2)
**Type**: Text (Mode-veld)  
**Default**: (empty)  
**Omschrijving**: Eigen naam voor de eerste gevonden laadpaal  
**Voorbeeld**: `Charge Lite Links`

### Naam laadpaal 2 (Mode3)
**Type**: Text (Mode-veld)  
**Default**: (empty)  
**Voorbeeld**: `Charge Lite Rechts`

**Belangrijk:** Gebruik **geen** Address/Port/SerialPort voor namen — Domoticz behandelt Port als getal (standaard `0`) en SerialPort als USB-poort.

Als Mode2/Mode3 leeg zijn, gebruikt de plugin de Easee-naam of `Laadpaal 1` / `Laadpaal 2`.

## Equalizer (optioneel, stap 1)

### Naam Equalizer (Address)
**Type**: Text (Address-veld)  
**Default**: (empty)  
**Voorbeeld**: `Meterkast`

### Equalizer ID handmatig (IP)
**Type**: Text (IP-veld)  
**Default**: (empty)  
**Gebruik**: Alleen als auto-discovery niets vindt. Vul de Equalizer ID/serienummer in uit de Easee app.

De plugin zoekt de Equalizer via:
1. `/accounts/products` → `equalizers` (primair, zoals Home Assistant/pyeasee)
2. `/sites/{id}?detailed=true` → `equalizers`
3. `/sites` → ingebouwde `equalizers`
4. `/sites/{id}/circuits` → `equalizerId`
5. `/equalizers` lijst
6. Handmatige ID (IP-veld)

Als geen Equalizer wordt gevonden, verschijnen geen extra tegels en toont Status `Geen EQ`.

### Equalizer Status-tegel (v10.2.8+)

| Regel | API-bron | Betekenis |
|-------|----------|-----------|
| Hoofdzekering | `site.ratedCurrent` | Zekering in meterkast (bijv. 25 A) |
| eMobility limiet | `site.state.maxAllocatedCurrent` | Max voor laadpaal (site wint) |
| Hoofdzekering limiet | circuit settings, siteStructure, equalizer-circuit | Ingestelde max in Easee (bijv. 24 A) |
| Actuele stroom | obs. 31–33 L1/L2/L3, of berekend uit vermogen | Echt verbruik nu (~2 A bij 802 W) |
| Huisvermogen | obs. 40 ActivePowerImport | Watt |

**Limiet ≠ actueel verbruik:** 24 A is een ingestelde grens; 802 W is ~2 A werkelijk gebruik (3-fase).

Zet **Debug logging** aan (Mode6) voor fuse-probe details en siteStructure numerics in het Domoticz-log.

Obs. 44 (MaxPowerImport) is **kW** en wordt niet gebruikt voor hoofdzekering limiet.

## Tibber Integration (Optioneel)

### Tibber Token (Mode7)
**Type**: Password  
**Default**: (empty)  
**Omschrijving**: Je Tibber Personal Access Token  
**Voordelen** (als ingesteld):
- ✅ Realtime stroomtarieven
- ✅ Automatische kostenberekening
- ✅ Goedkoopste laadwindows
- ✅ Prijs emoji indicators

### Tibber Token Ophalen (Mode8)
**Type**: Info link  
**URL**: https://developer.tibber.com/settings/access-token  
**Instructies**:
1. Ga naar link
2. Log in met je Tibber account
3. Klik "Create Personal Access Token"
4. Kopieer token
5. Plak in Mode7

## Device Naming

Devices krijgen automatisch deze namen:

### Core Devices
```
[PREFIX] - Status
[PREFIX] - Totaal Laden
[PREFIX] - Totaal kWh
[PREFIX] - LoadBal
[PREFIX] - Kosten & Samenvatting (Tibber)
[PREFIX] - Beste laden (Tibber)
```

### Per Equalizer (indien gevonden)
```
[PREFIX] - [NAAM] - Status
[PREFIX] - [NAAM] - Vermogen
```

### Per Laadpaal
```
[PREFIX] - [NAAM] - Laden
[PREFIX] - [NAAM] - Totaal & Sessie
[PREFIX] - [NAAM] - Status
[PREFIX] - [NAAM] - Kosten (Sessie/Dag) (Tibber)
```

## State Persistence

De plugin bewaart automatisch:
- `easee_v9_0_state.json` - Laadsessies, kosten, prijscache

Bestanden worden opgeslagen in de plugin directory en hersteld bij restart.

## Best Practices

### Performance
- **Poll interval**: 30-60 sec aanbevolen
- **Meer chargers** = eventueel hogere interval
- **CPU load**: Check met `top` command

### Beveiliging
- 🔒 Wachtwoorden worden encrypted in Domoticz
- 🔒 Geen credentials in logs (Debug modus)
- 🔄 Tokens worden automatisch vernieuwd

### Monitoring
- Controleer logs regelmatig
- Set `Debug` mode aan als problemen
- Check Domoticz hardware status

## Tips & Tricks

### Meerdere Locaties
```bash
# Instance 1: Thuis
Prefix: "Thuis", Filter: "Thuis"

# Instance 2: Kantoor  
Prefix: "Kantoor", Filter: "Kantoor"
```

### Laagste CPU
```
Poll Interval: 120 sec
Debug: Normal
```

### Meeste Details
```
Poll Interval: 10 sec
Debug: Debug
Tibber: Enabled
```
