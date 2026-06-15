# Easee Domoticz Plugin - v10.2.7 Release

## 📦 Release Notes

**Versie**: 10.2.7  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-15  

### Hoofdzekering limiet — 24 A fix
- v10.2.6 scheidde `ratedCurrent` (25 A) correct van de limiet, maar vond 24 A niet meer
- v10.2.7 verzamelt **alle** fuse-waarden uit de Easee API en kiest daarna de juiste limiet
- Nieuwe bronnen: circuit settings, siteStructure fuse-scan, root-circuit, circuitStates
- Bij opstarten één regel in het Domoticz-log met gevonden fuse-kandidaten (geen debug nodig)

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

## Previous: v10.2.6

- Hoofdzekering en limiet strikt gescheiden (ratedCurrent vs fuse)
- Regressie: limiet soms onbekend
