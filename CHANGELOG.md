# Changelog

Alle opmerkelijke veranderingen in dit project worden gedocumenteerd in dit bestand.

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
