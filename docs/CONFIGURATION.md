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

### Device Prefix (hardwarenaam)

De **hardwarenaam** die je in Domoticz invult (bijv. `Easee`) wordt automatisch als prefix op alle tegels gezet. Je hoeft hiervoor geen apart veld in te vullen.

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

### Extra laadpaalnamen (Mode4)
**Type**: Text (Mode-veld)  
**Default**: (empty)  
**Omschrijving**: Komma-gescheiden namen vanaf de **derde** laadpaal  
**Voorbeeld**: `Carport, Werf` → lader 3 = Carport, lader 4 = Werf

**Belangrijk:** Gebruik **geen** Address/Port/SerialPort voor namen — Domoticz behandelt Port als getal (standaard `0`) en SerialPort als USB-poort.

Als Mode2/Mode3/Mode4 leeg zijn, gebruikt de plugin de Easee-appnaam of `Laadpaal 1` / `Laadpaal 2` / …

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

### Equalizer Status-tegel (v10.3.0+)

| Regel | API-bron | Betekenis |
|-------|----------|-----------|
| Hoofdzekering | `site.ratedCurrent` | Zekering in meterkast (bijv. 25 A) |
| eMobility limiet | `site.state.maxAllocatedCurrent` | Max voor laadpaal (site wint) |
| Hoofdzekering limiet | fuse/limit API-velden (siteStructure, site.state, circuits, cloud-loadbalancing) | **Ingestelde limiet** in Easee Control (bijv. 22 A) — **nooit** MaxPowerImport |
| Max import | obs. 44 MaxPowerImport | Informatief: max vermogen aansluiting (bijv. 17,2 kW ≈ 25 A) — **verandert niet** bij limiet 22→24 A |
| L1/L2/L3 | obs. 31–33 | Fase-stromen; ontbrekend = `—`, nul = `0.0` |
| Actuele stroom | fallback berekend uit vermogen | Alleen als geen fase-observations |
| Huisvermogen | obs. 40 ActivePowerImport | Watt |

**Drie verschillende begrippen:**
- **Hoofdzekering (25 A)** = fysieke zekeringgrootte
- **Hoofdzekering limiet (22 A)** = wat jij instelt (gele lijn in Easee Energy)
- **Max import (17,2 kW)** = technisch max vermogen — **niet** hetzelfde als limiet

Als limiet **onbekend** is, controleer het Domoticz-log op `siteStructure amp-range 15-30` (1× per site, geen debug nodig). Wijzig je limiet in Easee en vergelijk welke waarde verandert.

Zet **Debug logging** aan (Mode6) voor uitgebreide fuse-probe details.

### Equalizer Vermogen-tegel (v10.6.5+)

| Weergave | Bron | Betekenis |
|----------|------|-----------|
| Vermogen (W) | observation 40 ActivePowerImport | Actueel importvermogen |
| **Vandaag** kWh | observation 45 CumulativeActivePowerImport | Cumulatieve teller (Wh); Domoticz berekent dagtotaal sinds middernacht |
| Fallback | `power_integrated_kwh` in `easee_state.json` | Als observation 45 ontbreekt: geïntegreerd vermogen over tijd |

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
[PREFIX] - [NAAM] - Vermogen   ← actueel vermogen (W) + Vandaag kWh (obs. 45, v10.6.5+)
```

### Per Laadpaal
```
[PREFIX] - [NAAM] - Laden
[PREFIX] - [NAAM] - Totaal & Sessie
[PREFIX] - [NAAM] - Status
[PREFIX] - [NAAM] - Kosten (Sessie/Dag) (Tibber)
```

## State Persistence

De plugin bewaart automatisch in **`easee_state.json`** (pluginmap):
- Laadsessies, kosten, prijscache
- Equalizer vermogensintegratie (fallback als observation 45 ontbreekt)

Bij upgrade van oudere versies wordt `easee_v9_0_state.json` automatisch hernoemd. Opslaan is atomisch (`.tmp` + `os.replace`, sinds v10.6.1).

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
