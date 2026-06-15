# Easee Domoticz Plugin - v10.3.2 Release

## 📦 Release Notes

**Versie**: 10.3.2  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-15

### Hoofdfix: Hoofdzekering limiet (23 A)

De ingestelde **Main fuse limit** in Easee Control komt uit API-veld **`circuit.fuse`** op het root-circuit — niet uit MaxPowerImport (17,2 kW ≈ 25 A zekeringgrootte).

### Installatie (Domoticz)

1. Download `easee-domoticz-v10.3.2.zip`
2. Pak uit in Downloads
3. Kopieer **alle inhoud** van map `easee-domoticz-v10.3.2-build/` naar je plugin-map (bijv. `domoticz/plugins/Easee-Domoticz-plugin/`)
4. Herstart Domoticz (Setup → Herstart systeem, of `sudo systemctl restart domoticz`)

### Verwachte Equalizer-tegel

```
✅ Equalizer online
⚖️ Load balancing: Aan
🔌 eMobility limiet: 21 A
🏠 Hoofdzekering: 25 A
⚡ Hoofdzekering limiet: 23 A
📈 Max import: 17.2 kW (~25 A)
📊 L1/L2/L3: — / 4.0 / — A
🔥 Huisvermogen: 802 W
```
