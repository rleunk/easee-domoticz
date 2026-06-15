# Easee Domoticz Plugin - v10.2.8 Release

## 📦 Release Notes

**Versie**: 10.2.8  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-15  

### Wat is nieuw?

De Equalizer-tegel toont nu **twee verschillende soorten stroom**:

| Regel | Betekenis | Voorbeeld |
|-------|-----------|-----------|
| ⚡ Hoofdzekering limiet | **Ingestelde maximum** in Easee Control | 24 A |
| 📊 Actuele stroom | **Wat je huis nu echt verbruikt** | 2,0 A (3-fase) |
| 🔥 Huisvermogen | Vermogen in Watt | 802 W |

**802 W is niet 24 A.**  
802 watt is ongeveer **2 ampère** verbruik in je hele huis (berekend voor een 3-fase aansluiting).  
24 ampère is de **limiet** die je in Easee hebt ingesteld — het maximum dat mag worden gebruikt voor laden.

### Equalizer Status-tegel (voorbeeld)

```
✅ Equalizer online
⚖️ Load balancing: Uit
🔌 eMobility limiet: 21 A
🏠 Hoofdzekering: 25 A
⚡ Hoofdzekering limiet: 24 A
📊 Actuele stroom: 2,0 A (3-fase)
🔥 Huisvermogen: 802 W
```

Als de meter fase-stromen doorgeeft, zie je in plaats daarvan:  
`📊 L1/L2/L3: 0,7 / 0,6 / 0,7 A`

### Overige fixes
- eMobility limiet: nu **21 A** via `site.state.maxAllocatedCurrent` (was soms 20 A)
- Hoofdzekering limiet: extra API-bronnen (circuit settings, equalizer-circuit)
- Debug-modus: volledige numerieke dump van siteStructure (1× per site)

### Installatie (upgrade van v10.2.7)

1. Kopieer de map `easee-domoticz-v10.2.8-build` naar je Domoticz plugins-map  
   (bijv. `domoticz/plugins/Easee/` — vervang de oude bestanden)
2. Herstart Domoticz via **Setup → Settings → System → Restart System**
3. Wacht ~30 seconden — de Equalizer-tegel vernieuwt automatisch

Geen extra instellingen nodig. Je laadpaal- en equalizer-tegels blijven behouden.

---

## Previous: v10.2.7

- Hoofdzekering limiet 24 A — robuuste fuse-detectie uit alle API-bronnen
- eMobility via site.state.maxAllocatedCurrent
