# Easee Domoticz Plugin - v9.1.0 Release

## 📦 Release Notes

**Versie**: 9.1.0  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-13  
**Ondersteuning**: Python 3.7+, Domoticz 2020.2+

---

## ✨ Wat is nieuw in v9.1.0?

### Leesbare laadstatus
- `chargerOpMode` cijfers worden Nederlandse tekst: `Laden`, `Wacht op start`, `Geen auto`, enz.
- Status-tegel toont: `✅ Laden · 7,2 kW · 01:24`

### Betere tegels en iconen
- Duidelijkere device-namen: `Easee - Laadpaal 1 - Status`
- Optionele eigen namen per laadpaal in hardware-config
- Verbeterde icon-koppeling (Energie-tegel krijgt niet meer per ongeluk kosten-icoon)

### Upgrade-opmerking
Na upgrade van v9.0.x kunnen nieuwe tegels naast oude verschijnen. Verwijder oude Easee-tegels handmatig in Domoticz.

**Update:**
```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull origin main
sudo systemctl restart domoticz
```

---

# Easee Domoticz Plugin - v9.0.1 Release

## 📦 Release Notes

**Versie**: 9.0.1  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-13  
**Ondersteuning**: Python 3.7+, Domoticz 2020.2+

---

## 🐛 Wat is nieuw in v9.0.1?

### Bugfix: sessiekosten energie/belasting

- Energie- en belastingkosten van laadsessie worden correct opgehaald wanneer er niet actief wordt geladen
- Geen dataverlies bij update vanaf v9.0 — `easee_v9_0_state.json` blijft in gebruik

**Update:**

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull origin main
sudo systemctl restart domoticz
```

---

# Easee Domoticz Plugin - v9.0 Production Release

## 📦 Release Notes

**Versie**: 9.0  
**Status**: ✅ Production Ready  
**Release Date**: 2026-06-12  
**Ondersteuning**: Python 3.7+, Domoticz 2020.2+

---

## ✨ Wat is nieuw in v9.0?

### 🎨 Compact UI - Minder Tegels, Meer Info

**Samenvoegen van devices:**
- `Totaal kWh` + `Sessie kWh` → `Totaal & Sessie` (één tegel)
- `Kosten sessie` + `Kosten vandaag` → `Kosten (Sessie/Dag)` (één tegel)
- `Overzicht` + `Kosten vandaag` → `Kosten & Samenvatting` (één tegel met emoji)

**Resultaat**: -40% minder tegels, +100% beter overzicht! 📊

### 🎨 Intelligente Emoji Indicators

**Power Status**:
- `⚡⚡` Hoog vermogen (>7kW)
- `⚡` Medium vermogen (>3.5kW)  
- `🔌` Laag vermogen (>50W)
- `⏸️` Standby

**Charger Status**:
- `✅` Online & Laden
- `🔴` Online & Standby
- `❌` Offline

**Prijs Status** (Tibber):
- `🟢` Goedkoop (onderste 33%)
- `🟡` Normaal (middel 33%)
- `🔴` Duur (bovenste 33%)

### 🔧 Onder de Motorkap

- ✅ Beter error handling
- ✅ Optimized device management
- ✅ Cleaner code architecture
- ✅ Enhanced logging
- ✅ Better state persistence

---

## 🚀 Installation

### Eerste Keer (Fresh Install)

```bash
# 1. Clone
cd /home/root/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin

# 2. Permissions
chmod +x /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
chown -R root:root /home/root/domoticz/plugins/Easee-Domoticz-plugin/

# 3. Restart
sudo systemctl restart domoticz

# 4. Voeg toe in UI: Setup → Hardware → "Easee AutoDiscovery Compact v9.0"
```

### Update van v8.x

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull origin main
sudo systemctl restart domoticz
```

**Geen data verlies!** Alle devices en laadgeschiedenis blijven behouden.

---

## 📋 Pre-Flight Checklist

Voor productie deployment, zorg dat je dit hebt:

- [ ] ✅ Python 3.7+ geïnstalleerd
- [ ] ✅ `python3-requests` package
- [ ] ✅ Easee account met laadpaal(en)
- [ ] ✅ Domoticz 2020.2+
- [ ] ✅ SSH/directe server access
- [ ] ⚠️ Optioneel: Tibber account + token

## 🧪 Testing

**Start in test mode:**

1. Enable Debug logging (Mode6 = "Debug")
2. Monitor logs: `sudo tail -f /home/root/domoticz/domoticz.log | grep Easee`
3. Check voor errors
4. Verify devices worden aangemaakt
5. Verify data updates

**Verwachte output:**
```
[Easee v9.0] Plugin gestart
[Easee v9.0] Login geslaagd
[Easee v9.0] Discovery: 2 laadpalen gevonden
[Easee v9.0] Devices aangemaakt
[Easee v9.0] State geladen
```

## 🎯 Performance Targets

- **API calls**: ~30 seconden interval (configureerbaar)
- **CPU usage**: <1% (per poll)
- **Memory**: ~50-100MB
- **Startup time**: <10 seconden

## 🔐 Security Notes

- ✅ Credentials worden encrypted in Domoticz
- ✅ Tokens worden automatisch vernieuwd
- ✅ Geen credentials in logs
- ✅ HTTPS-only API calls

## 🆘 Support & Issues

- **Bug reports**: https://github.com/rleunk/easee-domoticz/issues
- **Documentation**: https://github.com/rleunk/easee-domoticz
- **Troubleshooting**: Zie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📊 Version History

| Versie | Datum | Status | Notes |
|--------|-------|--------|-------|
| **9.1.0** | 2026-06-13 | ✅ Production | Leesbare status, betere tegels/iconen |
| **9.0.1** | 2026-06-13 | ✅ Production | Fix sessiekosten energie/belasting |
| **9.0** | 2026-06-12 | ✅ Production | Compact UI, emoji indicators |
| 8.0.2 | 2026-06-11 | 🔴 EOL | Stabiel maar niet compact |
| 8.0.1 | 2026-06-10 | 🔴 EOL | Early release |

## 📝 Known Limitations

- ❌ Rate limiting: Easee API limiteert tot ~60 requests/minute
- ❌ Offline mode: Plugin vereist internet access
- ⚠️ Tibber: Prijsgegevens kan 1-2 minuten vertraagd zijn
- ⚠️ Sessie tracking: Reset bij Domoticz restart

## 🎓 Best Practices

### Performance
- Stel poll interval in op 30-60 seconden
- Voor meer laadpalen: verhoog naar 60-120 seconden
- Disable debug mode in productie

### Monitoring
- Monitor logs regelmatig
- Set alerts op offline status
- Check maandelijks update beschikbaarheid

### Maintenance
- Backup config/state files
- Update git repository maandelijks
- Controleer Domoticz forum voor tips

## 🙏 Credits

- **Easee**: https://easee.com/
- **Tibber**: https://tibber.com/
- **Domoticz**: https://www.domoticz.com/

---

**🎉 Klaar voor productie!**

Volg de installatiehandleiding en je bent aan de slag met slimme laadpaal monitoring! 🔌⚡

Vragen? Zie [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) of open een GitHub issue.
