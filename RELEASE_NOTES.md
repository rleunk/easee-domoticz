# Easee Domoticz Plugin - v10.2.6 Release

## 📦 Release Notes

**Versie**: 10.2.6  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-15  

### Hoofdzekering limiet — aparte bron (fix)
- **Hoofdzekering** (25 A) en **Hoofdzekering limiet** (24 A) komen nu uit verschillende API-velden
- Hoofdzekering: alleen `ratedCurrent` / `mainFuseSize`
- Hoofdzekering limiet: `circuit.fuse`, `site.fuse`, siteStructure — nooit `ratedCurrent`
- Waarde gelijk aan hoofdzekering wordt overgeslagen; volgende probe levert de echte limiet (24 A)
- **eMobility limiet**: `maxAllocatedCurrent` heeft voorrang boven `maxCurrent`

### Equalizer Status-tegel
| Regel | Voorbeeld |
|-------|-----------|
| Hoofdzekering | 25 A |
| Hoofdzekering limiet | 24 A |
| eMobility limiet | 21 A |

### Installatie
1. Upload / git pull naar je Domoticz plugin-map
2. Herstart Domoticz

---

## Previous: v10.2.5

- Diepe fuse discovery via siteStructure, circuits, products
- Debug logging voor fuse-probes
