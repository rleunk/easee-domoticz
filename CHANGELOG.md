# Changelog

Alle opmerkelijke veranderingen in dit project worden gedocumenteerd in dit bestand.

## [10.2.7] - 2026-06-15

### 🐛 Hoofdzekering limiet 24 A — robuuste fuse-detectie
- **Alle fuse-kandidaten** worden nu verzameld uit alle bronnen vóór selectie (niet meer stoppen bij eerste probe)
- **siteStructure** (obs. 20): dubbel-gecodeerde JSON, alle `fuse`-keys (case-insensitive), ratedCurrent+fuse-paren
- **Nieuwe bronnen**: `/sites/{id}/circuits/{circuitId}/settings`, root-circuit fuse, alle circuitStates
- **Selectielogica**: root-circuit fuse → grootste waarde ≠ ratedCurrent → waarde onder hoofdzekering (24 vs 25)
- **Startup-log** (1×, normaal): siteStructure keys + gevonden fuse-kandidaten
- **Eerste poll-log** (1×): `Equalizer fuse: limit=24A src=...` voor support
- **eMobility limiet**: `site.state.maxAllocatedCurrent` wint altijd boven equalizer-waarden

## [10.2.6] - 2026-06-15

### 🐛 Hoofdzekering limiet — aparte bron
- **Hoofdzekering** (25 A) en **Hoofdzekering limiet** (24 A) gebruiken nu strikt verschillende API-velden
- Hoofdzekering: alleen `ratedCurrent` / `mainFuseSize`
- Hoofdzekering limiet: alleen `circuit.fuse`, `site.fuse`, siteStructure — nooit `ratedCurrent`
- Waarde gelijk aan hoofdzekering wordt overgeslagen; volgende probe gebruikt
- **eMobility limiet**: `maxAllocatedCurrent` heeft altijd voorrang boven `maxCurrent`

## [10.2.5] - 2026-06-15

### 🐛 Hoofdzekering limiet — extra probes
- Diepere parse van **siteStructure** (obs. 20): recursieve scan op `fuse`, `mainFuseLimit`, `fuseLimit`, …
- Root-circuit detectie verbeterd (`parentCircuitId` + child-graph)
- Extra bronnen: equalizer state/config, `/sites/{id}/circuits`, `/accounts/products` (incl. nested equalizers)
- **Debug logging** (Mode6=Debug): fuse-gerelateerde keys + siteStructure structuurkeys
- **eMobility limiet**: site `maxAllocatedCurrent` wint altijd boven equalizer-waarde; ook uit siteStructure

## [10.2.4] - 2026-06-15

### 🐛 Hoofdzekering limiet fix
- **Hoofdzekering limiet** toont nu alleen **Amperes** (geen kW-fallback meer op obs. 44 MaxPowerImport)
- Uitgebreide bronnen: `site.fuse`, `circuit.fuse` (root/equalizer-circuit), `siteStructure` (obs. 20), `/accounts/products`
- Bij ontbrekende amp-waarde: **onbekend** i.p.v. verkeerde kW
- **eMobility limiet** preferert `site.maxAllocatedCurrent` boven equalizer-waarden

## [10.2.3] - 2026-06-15

### ✨ Equalizer tegel uitgebreid
- **Hoofdzekering** (main fuse size) via `site.ratedCurrent` uit `/sites/{id}/state`
- **Hoofdzekering limiet** via `site.fuse` of fallback `MaxPowerImport` (obs. 44, kW)
- Emoji's terug op de Status-tegel (✅ ⚖️ 🔌 🏠 ⚡ 🔥)
- Site fuse-info gecached per poll-cyclus

## [10.2.2] - 2026-06-15

### ✨ Equalizer tegel verduidelijkt
- Status toont nu `eMobility limiet: 20 A` (zelfde als Easee Control)
- Duidelijke regels: online, load balancing, limiet, optioneel huisvermogen

## [10.2.1] - 2026-06-15

### 🐛 Equalizer discovery fix
- Nieuwe routes: `/accounts/products`, `/sites/{id}?detailed=true`, `site.equalizers`
- Handmatige fallback via **Equalizer ID** (IP-veld in hardware)
- Polling via `/equalizers/{id}/state` + `/config` + observations
- Betere debug-logging met probe-samenvatting

## [10.2.0] - 2026-06-15

### ✨ Equalizer stap 1
- **Auto-discovery** via `/sites/.../circuits`, `/equalizers` en sites-scan (HAN/P1)
- **2 nieuwe tegels** per Equalizer: `Status` en `Vermogen`
- **Optionele naam** via hardwareveld `Naam Equalizer` (Address)
- **LoadBal** schakelaar toont nu echte load-balancing status (niet meer altijd Uit)
- Status-tegel toont equalizer-aantal (`EQ: 1` of `Geen EQ`)

### Volgende stappen (nog niet in deze versie)
- Fase-stromen (L1/L2/L3)
- Observations API voor gedetailleerde meterdata

## [10.1.3] - 2026-06-15

### 🐛 Bugfix
- Geen `CDevice_update`-fouten meer bij hernoemen van tegels (`Update(Name=...)` vervangen door directe naamtoewijzing)

## [10.1.2] - 2026-06-15

### 🐛 Bugfix
- Alle tegels: dubbele `Easee` prefix verwijderd (kern- én laadpaal-tegels)
- Bestaande devices worden automatisch hernoemd bij upgrade
- Mode2/Mode3 en Easee API-namen worden opgeschoond als ze al `Easee -` bevatten

## [10.1.1] - 2026-06-15

### 🐛 Bugfix
- Geen dubbele `Easee` meer in tegelnamen (Domoticz voegt hardwarenaam al toe)
- Device-namen zijn nu kort: `Totaal Laden`, `Charge Lite Links - Status`
- Tip: geef je hardware in Domoticz een naam zoals `Easee`

## [10.1.0] - 2026-06-15

### ✨ Nieuw
- **Optionele laadpaalnamen** via `Mode2` (laadpaal 1) en `Mode3` (laadpaal 2)
- Device-namen bijv. `Easee - Charge Lite Links - Status`
- **Stabiele device-IDs** op basis van charger-ID — namen wijzigen geeft geen dubbele tegels

### 🐛 Fix t.o.v. v9.1.0
- Geen `Port`/`SerialPort` meer (die gaven `0` en USB-poort UI in Domoticz)
- Alleen tekst-Mode-velden voor namen

### ⚠️ Upgrade vanaf v10.0.x
- Nieuwe device-namen en IDs — oude tegels met ID-suffix (bijv. `AB12CD34 Status`) kun je handmatig verwijderen
- State file (`easee_v9_0_state.json`) blijft behouden

## [10.0.1] - 2026-06-15

### ✨ Verbetering
- Laadstatus (`chargerOpMode`) wordt als Nederlandse tekst getoond i.p.v. cijfers
  - Bijv. `Laden`, `Wacht op start`, `Geen auto` in plaats van `3`, `2`, `1`

### 📦 Overige
- Verder identiek aan v10.0.0 — zelfde devices, state file en UI

## [10.0.0] - 2026-06-15

### 🚀 Nieuwe start
- Schone release gebaseerd op stabiele v9.0 codebase
- Nieuw versienummer als basis voor toekomstige updates

### 🐛 Bugfixes
- Energie- en belastingkosten van laadsessie worden correct opgehaald wanneer er niet actief wordt geladen (`last_session_cost_energy` / `last_session_cost_tax`)

### 📦 Overige
- `easee_v9_0_state.json` blijft in gebruik — bestaande laadgeschiedenis blijft behouden
- Zelfde device-namen en UI als v9.0

## [9.0] - 2026-06-12

### ✨ Nieuw
- **Compacte UI** - Devices worden slim samengevoegd voor overzichtelijkere tegels
  - "Totaal & Sessie" combineert totale kWh en sessie kWh
  - "Kosten (Sessie/Dag)" combineert sessie- en dagkosten met prijs emoji
  - "Kosten & Samenvatting" geeft compleet kostenoverzicht
- **Intelligente emoji indicators**
  - Power emoji (⚡⚡, ⚡, 🔌, ⏸️) gebaseerd op vermogen
  - Status emoji (✅, 🔴, ❌) voor online/offline/laden status
  - Prijs emoji (🟢, 🟡, 🔴) voor Tibber tarieven
- **Nieuw repository** - Complete standalone plugin build
- **Dokumentatie** - Installation, Configuration, Troubleshooting guides

### 🐛 Bugfixes
- Verbeterde error handling in API calls
- Betere sessie state management
- Optimalisatie van device creation

### 🔧 Refactor
- Code reorganisatie voor betere maintainability
- Helper methoden voor emoji's
- Schonere device update logica

### 📦 Dependencies
- Python 3.7+
- Domoticz 2020.2+
- requests library (Python)
- Optional: Tibber API token

---

## [8.0.2] - 2026-06-11

### ✨ Nieuw
- Stabiele build met compacte overzichtstegel
- Emoji prijsstatus
- Verbeterde statustegel
- Optionele Tibber integratie

### 🎯 Status
- End of life: Zie v9.0 voor updates

---

## [8.0.1] en eerder

- Initiële releases en development versions
