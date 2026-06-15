# Changelog

Alle opmerkelijke veranderingen in dit project worden gedocumenteerd in dit bestand.

## [9.1.0] - 2026-06-13

### ✨ Nieuw
- **Leesbare laadstatus** — `chargerOpMode` cijfers worden Nederlandse tekst (bijv. `Laden`, `Wacht op start`)
- **Betere tegelteksten** — status toont nu `Laden · 7,2 kW · 01:24` i.p.v. ruwe cijfers
- **Optionele laadpaalnamen** — configureer namen voor laadpaal 1/2/3 in hardware-instellingen
- **Slimmere iconen** — verbeterde koppeling tussen tegeltype en Easee-icon (fix: Energie-tegel kreeg ten onrechte kosten-icoon)

### 🎨 UI verbeteringen
- Laadpaal devices heten nu bijv. `Easee - Laadpaal 1 - Status` i.p.v. alleen een ID
- Energie-tegel: `Totaal 1245 kWh · Sessie 18 kWh`
- Kosten-tegel: `Sessie €2,45 · Vandaag €5,10`
- Systeemstatus: `2/2 laders online`

### ⚠️ Opmerking bij upgrade
- Nieuwe device-namen kunnen extra tegels aanmaken naast oude v9.0-tegels
- Verwijder oude Easee-tegels handmatig in Domoticz na upgrade, of verwijder en hermaak de hardware

## [9.0.1] - 2026-06-13

### 🐛 Bugfixes
- Energie- en belastingkosten van laadsessie worden correct opgehaald wanneer er niet actief wordt geladen

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
