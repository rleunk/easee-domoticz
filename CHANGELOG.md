# Changelog

Alle opmerkelijke veranderingen in dit project worden gedocumenteerd in dit bestand.

## [10.3.3] - 2026-06-15

### 🐛 Hoofdzekering limiet — site.circuits + root-circuit detail
- **`/sites/{id}/state` → `site.circuits[]`** wordt nu ook gelezen (naast `circuitStates`) — hier staat `circuit.fuse` vaak wél terwijl `circuitStates` het soms mist
- **Root-circuit detail**: voor elk root-circuit extra GET `/sites/{id}/circuits/{id}` + `/settings`
- **Selectie hersteld**: root `circuit.fuse` direct prefereren; hoogste waarde strikt onder `ratedCurrent` (23 A bij 25 A)
- **Betere logging bij onbekend**: toont gevonden ruwe fuse-waarden, afgewezen kandidaten én API-keys (niet alleen probe-namen)

## [10.3.2] - 2026-06-15

### 🐛 Hoofdzekering limiet — circuit.fuse (23 A)
- **Hoofdzekering limiet** uit Easee API-veld **`circuit.fuse`** (root-circuit in `/sites/{id}/state` → `circuitStates`, `/circuits`, siteStructure obs. 20)
- Kandidaten **strikt onder** `ratedCurrent` (25 A): 23 A wint, 25 A wordt uitgesloten
- **Geen** MaxPowerImport-fallback meer als limiet (blijft aparte regel Max import)
- **1× Domoticz-log**: volledige siteStructure key-structuur (truncated) + amp-range 15–30 A
- Bij **onbekend**: log welke API-probes zijn uitgevoerd
- Extra probes: `/sites/{id}`, `/cloud-loadbalancing/.../surplus-energy`

### 📋 Equalizer Status-tegel (ongewijzigde volgorde)
- Online → Load balancing → eMobility → Hoofdzekering → Hoofdzekering limiet → Max import → L1/L2/L3 → Huisvermogen

## [10.3.1] - 2026-06-15

### 🐛 Plugin laadfout (Domoticz)
- **Zip-structuur hersteld**: release-zip gebruikt weer map `easee-domoticz-v10.3.1-build/` (zoals v10.2.9) — v10.3.0 zip had platte structuur waardoor `plugin.py` bij verkeerd uitpakken niet in de plugin-map stond → `ModuleNotFoundError: No module named 'plugin'`
- **`# -*- coding: utf-8 -*-`** toegevoegd voor betrouwbare UTF-8 op Linux/Domoticz
- Logregel startup: `!=` i.p.v. Unicode `≠` (ASCII-veilig)

### ℹ️ Verder identiek aan v10.3.0
- MaxPowerImport niet meer als hoofdzekering limiet
- Aparte regel Max import, L1/L2/L3 fix, fuse-zoektocht

## [10.3.0] - 2026-06-15

### ⚠️ Bekend probleem
- Release-zip had **verkeerde mapstructuur** (bestanden in zip-root i.p.v. `-build/` submap). Gebruik **v10.3.1** of kopieer `plugin.py` handmatig uit de build-map.


### 🐛 Hoofdzekering limiet — geen MaxPowerImport meer als limiet
- **MaxPowerImport (obs. 44) verwijderd** als fallback voor hoofdzekering limiet — gaf altijd ~25 A (zekeringgrootte), niet de ingestelde limiet (bijv. 22 A)
- **Nieuwe aparte regel**: `📈 Max import: 17.2 kW (~25 A)` — informatief, niet gelabeld als limiet
- Bij ontbrekend fuse-veld: **onbekend** i.p.v. verkeerde 25 A

### 🔍 Agressievere fuse-limiet zoektocht
- Diepe scan siteStructure (obs. 20) op fuse, fuseLimit, mainFuseLimit, limit, maxCurrent, importLimit, …
- `/sites/{id}/state` — alle site-keys + recursieve limit-scan
- **Nieuwe endpoints**: `/cloud-loadbalancing/equalizer/{id}/config` (+ varianten)
- Circuit settings, equalizer-circuit, accounts/products (ongewijzigd maar uitgebreid)
- **1× Domoticz-log** (normaal, geen debug): alle numerieke waarden **15–30 A** in siteStructure — helpt het echte limiet-veld te vinden

### 📊 L1/L2/L3 weergave
- Alle drie fasen altijd zichtbaar als observations 31/32/33 aanwezig zijn
- Ontbrekende fase: `—`, nul stroom: `0.0`

### 📋 Equalizer Status-tegel (volgorde)
- Online → Load balancing → eMobility limiet → Hoofdzekering → Hoofdzekering limiet → **Max import** (optioneel) → L1/L2/L3 → Huisvermogen

### ℹ️ eMobility
- `site.state.maxAllocatedCurrent` blijft voorrang

## [10.2.9] - 2026-06-15

- **Hoofdzekering limiet fallback**: obs. 44 MaxPowerImport (kW) → A via 3×230 V als Easee geen fuse-waarde geeft *(vervangen in 10.3.0)*

## [10.2.8] - 2026-06-15

### ✨ Actuele stroom vs limiet — duidelijk onderscheid
- **📊 Actuele stroom** berekend uit huisvermogen op 3×230 V: `I = P / (√3 × 230)`
- **📊 L1/L2/L3** uit equalizer observations 31/32/33 (voorkeur boven berekening)
- **⚡ Hoofdzekering limiet** blijft ingestelde max (bijv. 24 A) — niet verwarren met actueel verbruik

### 🐛 Hoofdzekering limiet — extra probes
- Volledige **siteStructure** numerieke dump in debug-log (1× per site)
- **offlineMaxCircuitCurrentP1/P2/P3** uit circuit settings
- **min(maxCircuitCurrentP1/P2/P3)** als fuse-kandidaat
- **Equalizer circuitId**: direct `/sites/{id}/circuits/{circuitId}` voor fuse

### 🐛 eMobility limiet
- **`site.state.maxAllocatedCurrent`** heeft absolute voorrang (21 A i.p.v. equalizer 20 A)

### 📋 Equalizer Status-tegel (volgorde)
- Online → Load balancing → eMobility limiet → Hoofdzekering → Hoofdzekering limiet → Actuele stroom → Huisvermogen

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
