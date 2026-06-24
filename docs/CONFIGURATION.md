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
- **60 sec = aanbevolen bij HTTP 429 rate limit** — minder API-druk; zie [TROUBLESHOOTING.md](TROUBLESHOOTING.md#http-429-rate-limit)
- 60 sec = lager CPU gebruik
- 10 sec = realtime updates (meer CPU, meer kans op 429)

**Instellen in Domoticz:** **Setup → Hardware** → klik je Easee hardware-item → **Poll interval (sec)** → wijzig naar `60` → **Save**.

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

| Mode6 | Wat je ziet in het log |
|-------|------------------------|
| **Normal** | Startup, Tibber actief/uit, `image_ids: 13/13`, migratie, WARNING/ERROR |
| **Debug** | Alles hierboven + `Poll voltooid`, kosten-tegel updates, siteStructure, per-tegel iconen |

Zet Debug alleen aan bij problemen — het log wordt dan veel langer.

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

### Equalizer Status-tegel (v10.9.0+)

Gegroepeerde weergave op één teksttegel:

```
✅ Equalizer online
⚖️ Load balancing: Uit
   Vrij: - / - / - A  |  Laad: - / - / -
🛡️ eMobility: 20 A | Hoofd: 25 A | Limiet: 24 A
⚡ Max import: 17.2 kW
📊 Stroom L1/L2/L3: 0.0 / 4.0 / 0.0 A
🔌 Spanning L1/L2/L3: 231 / 230 / 229 V
```

| Regel | API-bron | Betekenis |
|-------|----------|-----------|
| Verbinding | `online` state | Online/offline |
| Load balancing | LB state + obs. 230–232 | Aan/uit + vrij/laad per fase |
| Limieten | site fuse API | eMobility, hoofdzekering, ingestelde limiet |
| Max import | obs. 44 MaxPowerImport | Max vermogen aansluiting |
| Stroom L1/L2/L3 | obs. 31–33 | Fase-stromen |
| Spanning L1/L2/L3 | state / obs. 34–36 | Fase-spanning (V) |

**Huisvermogen staat niet op Status** — zie Vermogen-tegel.

### Equalizer tegels (v10.9.1+, huidige release v10.11.1)

| Tegel | Type | Icoon | Weergave |
|-------|------|-------|----------|
| Status | Text | `EaseeEqualizer` | Verbinding, LB-detail, limieten, stroom, spanning |
| Vermogen | Text | `EaseeEqualizer` | Import W, terug W, netto W, vandaag import/netto kWh |

Core **LoadBal**-schakelaar (site-wide) blijft ongewijzigd; icoon `EaseeLoadBal`.

Legacy: *Import*, *Terug & netto*, *Netto*, *Teruglevering*, *Spanning*, *Load balancing* (losse EQ-tegel) — **niet meer aangemaakt** sinds v10.9.1. Wees-tegels uit v10.8.0/v10.9.0 handmatig verwijderen als die nog bestaan.

## Verwachte tegels (referentie)

> **README-demo:** de gesanitiseerde screenshot in [README.md](../README.md) toont **11 actieve tegels + LoadBal** met **twee laadpalen** (*Lader 1*, *Lader 2*) plus globale en Equalizer-tegels — compacte v10.11-layout.

Bij **2 laadpalen + 1 Equalizer + Tibber** hoort de plugin **11 dashboard-tegels** (+ **LoadBal**-schakelaar = 12 devices totaal). Prefix `[PREFIX]` = jouw hardwarenaam, bijv. `Easee`:

| # | Tegel |
|---|-------|
| 1 | `[PREFIX] - Status` |
| 2 | `[PREFIX] - Totaal Laden` |
| 3 | `[PREFIX] - Totaal kWh` |
| 4 | `[PREFIX] - Beste laden` |
| 5 | `[PREFIX] - Dag overzicht` |
| 6 | `[PREFIX] - [EQ-naam] - Status` |
| 7 | `[PREFIX] - [EQ-naam] - Vermogen` |
| 8–9 | Laadpaal 1: `[PREFIX] - [Naam] - Laden`, `Status` |
| 10–11 | Laadpaal 2: idem |

Daarnaast: **`[PREFIX] - LoadBal`** (schakelaar, niet meegeteld in de 11 tegel-overzichten).

> **v10.11.0:** *Kosten & Samenvatting* + *Dagrapport* → **Dag overzicht**; per laadpaal *Totaal & Sessie* → **Laden** (Description), *Kosten (Sessie/Dag)* → **Status**. Oude tegels: `Used=0` (verborgen), niet auto-verwijderd.

**Geen Tibber?** Dan ontbreken #4–5 en sessie/dag-€ op Status.

### Tibber slim laden / Grid Rewards

**Niet via plugin.** Tibber API levert alleen energieprijzen (voor kosten-tegels). Tibber *slim laden*, *Grid Rewards* en vergelijkbare grid-programma's zijn alleen in de Tibber-app — geen publieke API. De plugin plant hier geen tegels of automatisering; gesloten tenzij Tibber API dit opent. Zie [ROADMAP.md](ROADMAP.md).

**Geen Equalizer?** Dan ontbreken tegels 7 en 8.

**Legacy-tegels die er níet horen:** *Import*, *Spanning*, *Terug & netto*, *Netto*, *Teruglevering*, losse *Load balancing* (EQ). Die komen uit v10.8.0 of v10.9.0 — verwijder ze handmatig in Domoticz als ze nog bestaan.

### Equalizer tegels (v10.9.0, vervangen door 2 tegels in v10.9.1)

| Tegel | Type | Bron | Weergave |
|-------|------|------|----------|
| Status | Text | state + site fuse API | Verbinding, LB-detail, limieten, stroom, spanning |
| Import | Energy | obs. 40 / 45 | Vermogen (W) + **Vandaag** kWh import |
| Terug & netto | Text | obs. 41/46 + berekend | Import W, terug W, netto W, vandaag/totaal netto kWh |

Legacy: *Vermogen* → *Import*; *Netto* of *Teruglevering* → *Terug & netto*.

### Equalizer Status-tegel (v10.3.0 – v10.8.x, vervangen door gegroepeerde Status in v10.9.0)

| Regel | API-bron | Betekenis |
|-------|----------|-----------|
| Hoofdzekering | `site.ratedCurrent` | Zekering in meterkast (bijv. 25 A) |
| eMobility limiet | `site.state.maxAllocatedCurrent` | Max voor laadpaal (site wint) |
| Hoofdzekering limiet | fuse/limit API-velden (siteStructure, site.state, circuits, cloud-loadbalancing) | **Ingestelde limiet** in Easee Control (bijv. 22 A) — **nooit** MaxPowerImport |
| Max import | obs. 44 MaxPowerImport | Informatief: max vermogen aansluiting (bijv. 17,2 kW ≈ 25 A) — **verandert niet** bij limiet 22→24 A |
| L1/L2/L3 | obs. 31–33 | Fase-stromen; ontbrekend = `—`, nul = `0.0` |
| Actuele stroom | fallback berekend uit vermogen | Alleen als geen fase-observations |

**Huisvermogen staat niet meer op Status** (sinds v10.8.0) — zie Vermogen-tegel.

**Drie verschillende begrippen:**
- **Hoofdzekering (25 A)** = fysieke zekeringgrootte
- **Hoofdzekering limiet (22 A)** = wat jij instelt (gele lijn in Easee Energy)
- **Max import (17,2 kW)** = technisch max vermogen — **niet** hetzelfde als limiet

Als limiet **onbekend** is, zet **Debug logging** (Mode6) aan en zoek op `siteStructure amp-range 15-30` (1× per site, alleen zichtbaar in Debug-modus sinds v10.9.29). Wijzig je limiet in Easee en vergelijk welke waarde verandert.

Zet **Debug logging** aan (Mode6) voor uitgebreide fuse-probe details.

### Equalizer tegels Proposal C (v10.8.0, vervangen door 3 tegels in v10.9.0)

| Tegel | Type | Bron | Weergave |
|-------|------|------|----------|
| Status | Text | state + site fuse API | Online, LB, limieten, L1/L2/L3 stroom (A) |
| Import | Energy | obs. 40 / 45 | Vermogen (W) + **Vandaag** kWh import |
| Teruglevering | Energy | obs. 41 / 46 | Vermogen (W) + **Vandaag** kWh export |
| Netto | Text | berekend | Netto W (import − export), totaal netto kWh |
| Spanning | Text | state / obs. 34–36 | L1/L2/L3 spanning (V) |
| Load balancing | Text | state / obs. 230–232 | Vrij L1/L2/L3 (A), gelijkstroom L1/L2/L3 (A) |

Core **LoadBal**-schakelaar (site-wide) blijft ongewijzigd.

Legacy: bestaande **Vermogen**-tegel wordt automatisch **Import** (zelfde DeviceID via legacy lookup).

### Equalizer Import-tegel (v10.6.5 – v10.7.x, vervangen door Import in v10.8.0)

| Weergave | Bron | Betekenis |
|----------|------|-----------|
| Vermogen (W) | observation 40 ActivePowerImport | Actueel importvermogen |
| **Vandaag** kWh | observation 45 CumulativeActivePowerImport | Cumulatieve teller (Wh); Domoticz berekent dagtotaal sinds middernacht |
| Fallback | `power_integrated_kwh` in `easee_state.json` | Als observation 45 ontbreekt: geïntegreerd vermogen over tijd |

## Tibber Integration (vereist voor kosten-tegels)

### Tibber Token (Mode7)
**Type**: Password  
**Default**: (empty)  
**Omschrijving**: Je Tibber Personal Access Token — **verplicht voor kosten-tegels**  
**Zonder token**: *Dag overzicht* en sessie/dag-€ op laadpaal-**Status** worden niet bijgewerkt  

**Token-backup (v10.9.30+)**  
Domoticz wist wachtwoordvelden soms bij *Opslaan* op de hardwarepagina (veld lijkt leeg, token verdwijnt uit Mode7). De plugin bewaart een kopie in `easee_state.json` (`tibber_token_backup`) zodra je het token één keer invult. Bij herstart of plugin-update: als Mode7 leeg is maar de backup bestaat, gebruikt de plugin die automatisch — je hoeft het token niet opnieuw in te vullen. In het log: `Tibber actief — token hersteld uit state-backup`. Het token wordt **nooit** gelogd. Nieuw token invullen in Mode7 overschrijft de backup. Tibber uitzetten: verwijder het hardware-item of wis `tibber_token_backup` uit `easee_state.json` op de server.

**Voordelen** (als ingesteld):
- ✅ Realtime stroomtarieven
- ✅ Automatische kostenberekening
- ✅ Goedkoopste laadwindows
- ✅ Prijs emoji indicators

### Tibber Token Ophalen (Mode8)
**Type**: Info link  
**URL**: https://developer.tibber.com/settings/access-token  

### Beste laden venster (Extra)
**Type**: Text  
**Default**: `3`  
**Omschrijving**: Aantal uren voor het goedkoopste laadvenster op de *Beste laden*-tegel (1–12). Gebruikt Tibber kwartierprijzen indien beschikbaar.

**Instructies Mode8**:
1. Ga naar link
2. Log in met je Tibber account
3. Klik "Create Personal Access Token"
4. Kopieer token
5. Plak in Mode7

### Beste laden venster (Extra)
**Type**: Text  
**Default**: `3`  
**Omschrijving**: Aantal uren voor het sliding-window van de *Beste laden*-tegel (1–12). Bij kwartierprijzen gebruikt de plugin 4× zoveel slots per uur.

## Device Naming

Devices krijgen automatisch deze namen:

### Core Devices
```
[PREFIX] - Status
[PREFIX] - Totaal Laden
[PREFIX] - Totaal kWh
[PREFIX] - LoadBal
[PREFIX] - Beste laden (Tibber)
[PREFIX] - Dag overzicht (Tibber)
```

Legacy (v10.10.x, niet meer bijgewerkt sinds v10.11): *Kosten & Samenvatting*, *Dagrapport*.

### Per Equalizer (indien gevonden)
```
[PREFIX] - [NAAM] - Status
[PREFIX] - [NAAM] - Vermogen        ← import/terug/netto (v10.9.1+; legacy: Import, Terug & netto, Netto, Teruglevering)
```

### Per Laadpaal
```
[PREFIX] - [NAAM] - Laden          ← sessie/vandaag/totaal kWh in Description (v10.11+)
[PREFIX] - [NAAM] - Status         ← incl. sessie/dag € bij Tibber (v10.11+)
```

Legacy (v10.10.x): *Totaal & Sessie*, *Kosten (Sessie/Dag)* — verborgen (`Used=0`) na upgrade.

## Custom iconen (v10.11.1)

13 sets in `Easee_icons_v2.zip`. Belangrijkste mapping:

| Tegel | Iconenset |
|-------|-----------|
| **[PREFIX] - Status** (globaal) | `EaseeStatusGlobal` — combo laadpaal + EQ-puck + **i** |
| **[PREFIX] - [Naam] - Status** (laadpaal) | `EaseeStatus` — laadpaal-only + **i** |
| **[PREFIX] - [Naam] - Laden** | `EaseeCharger` |
| **[PREFIX] - [Naam] - Status** | `EaseeStatus` |
| **[PREFIX] - Dag overzicht** | `EaseeOverview` |
| **[PREFIX] - [EQ] - Status / Vermogen** | `EaseeEqualizer` |
| **LoadBal** | `EaseeLoadBal` |
| **Totaal Laden / kWh** | `EaseePower` *(Energy-tegel kan standaard bliksem tonen — Domoticz-beperking)* |

Auto-load bij start; anders handmatige upload — zie [INSTALL.md](../INSTALL.md#custom-iconen-handmatig-uploaden).

## State Persistence

De plugin bewaart automatisch in **`easee_state.json`** (pluginmap):
- Laadsessies, kosten, prijscache
- Equalizer import/export energie-integratie (fallback als observation 45/46 ontbreekt)

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
