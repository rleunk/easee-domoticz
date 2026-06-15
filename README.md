# Easee Domoticz Plugin v10.2.8

**Complete Easee laadpaal integratie voor Domoticz met compacte UI, intelligente emoji indicators en Tibber stroomtarief integratie.**

![Version](https://img.shields.io/badge/version-10.2.8-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

## ✨ Features

✨ **Auto-Discovery** - Automatische detectie van alle Easee laadpalen  
📊 **Realtime Monitoring** - Live power, energy en status updates  
💬 **Leesbare status** - Laadstatus in Nederlands (Laden, Wacht op start, …)  
🏷️ **Eigen namen** - Optionele namen per laadpaal via Mode2/Mode3  
⚖️ **Equalizer (stap 1)** - Auto-discovery + Status/Vermogen tegels  
💰 **Cost Tracking** - Automatische berekening van laadkosten  
💵 **Tibber Integration** - Stroomtarieven en goedkope laadwindows  
🎨 **Compact UI** - Intelligente samengevoegde tegels met emoji indicators  
🔐 **Secure** - Veilige token opslag en session management  
🔄 **State Persistence** - Behoudt laadsessie gegevens over restarts  

## 📦 Installatie

Zie [docs/INSTALLATION.md](docs/INSTALLATION.md) voor stap-voor-stap instructies.

### Quick Start

1. **Clone repository**
   ```bash
   git clone https://github.com/rleunk/easee-domoticz.git
   cd easee-domoticz
   ```

2. **Kopieer naar Domoticz plugins**
   ```bash
   cp -r . /home/root/domoticz/plugins/Easee-Domoticz-plugin/
   ```
   (Pas het pad aan voor jouw Domoticz installatie)

3. **Zet permissies**
   ```bash
   chmod +x /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
   chown -R root:root /home/root/domoticz/plugins/Easee-Domoticz-plugin/
   ```

4. **Restart Domoticz**
   ```bash
   sudo systemctl restart domoticz
   ```

5. **Voeg plugin toe in Domoticz UI**
   - Setup → Hardware
   - Type: "Easee AutoDiscovery Compact v10.2.8"
   - Geef de hardware een naam, bijv. `Easee` (dit wordt het prefix op alle tegels)
   - Username/Password: Jouw Easee credentials
   - Create

## ⚙️ Configuratie

Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md) voor alle beschikbare parameters.

### Basis Settings

| Parameter | Standaard | Omschrijving |
|-----------|-----------|--------------|
| Username | - | Easee account username/telefoonnummer |
| Password | - | Easee account wachtwoord |
| Poll interval | 30 sec | Hoe vaak data wordt opgehaald |
| Device prefix | "Easee" | Prefix voor alle devices |
| Naam laadpaal 1 (Mode2) | - | Optioneel, bijv. `Charge Lite Links` |
| Naam laadpaal 2 (Mode3) | - | Optioneel, bijv. `Charge Lite Rechts` |
| Naam Equalizer (Address) | - | Optioneel, bijv. `Meterkast` |
| Equalizer ID (IP) | - | Handmatig, alleen als discovery faalt |
| Site filter | - | Optioneel: filter op sitenaam |
| Tibber token | - | Optioneel: Tibber API token voor prijzen |

## 📊 Devices

### Core Devices
- **Status** - Online status en Tibber status
- **Totaal Laden** - Huidige vermogen (Watt)
- **Totaal kWh** - Totaal geladen energie
- **LoadBal** - Load balancing status (van Equalizer, indien gevonden)
- **Kosten & Samenvatting** - Dagelijkse kosten + emoji prijsindicator (met Tibber)
- **Beste laden** - Goedkoopste laadwindow (met Tibber)

### Per Equalizer (indien gevonden)
- **[Naam] - Status** — online, load balancing, limieten, actuele stroom, huisvermogen
- **[Naam] - Vermogen** — actueel vermogen (Watt)

### Per Laadpaal
- **[Naam] - Laden** - Power meter (Watt)
- **[Naam] - Totaal & Sessie** - Totaal en sessie kWh
- **[Naam] - Status** - Laadstatus in Nederlands + emoji
- **[Naam] - Kosten (Sessie/Dag)** - Kosten (met Tibber)

## 🎨 Emoji Indicators

### Charger Status (tekst op tegel)
| Tekst | Betekenis |
|-------|-----------|
| Laden | Actief aan het laden |
| Wacht op start | Auto aangesloten, wacht op start |
| Geen auto | Geen auto aangesloten |
| Voltooid | Laden afgerond/pauze |
| Fout | Fout op de lader |
| Offline | Lader offline |

### Power Status (emoji)
- `⚡⚡` = Hoog vermogen (>7kW)
- `⚡` = Medium vermogen (>3.5kW)
- `🔌` = Laag vermogen (>50W)
- `⏸️` = Standby/niet laden

### Charger Status
- `✅` = Online & Laden
- `🔴` = Online & Standby
- `❌` = Offline

### Prijs Status (Tibber)
- `🟢` = Goedkoop (onderste 33%)
- `🟡` = Normaal (middel 33%)
- `🔴` = Duur (bovenste 33%)

## 🔧 Troubleshooting

Zie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) voor veelvoorkomende problemen en oplossingen.

## 📝 Changelog

Zie [CHANGELOG.md](CHANGELOG.md) voor volledige versiegeschiedenis.

## 🆙 Updates

**Van v10.0.x naar v10.1.0?**

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull origin main
sudo systemctl restart domoticz
```

Geen data verlies - alle devices en laadgeschiedenis blijven behouden!

## 🤝 Support

- **Issue tracker**: [GitHub Issues](https://github.com/rleunk/easee-domoticz/issues)
- **Documentation**: [docs/](docs/)
- **Domoticz Wiki**: [wiki.domoticz.com](https://wiki.domoticz.com/)
- **Easee Developer**: [developer.easee.com](https://developer.easee.com/)

## 📄 Licentie

MIT License - zie [LICENSE](LICENSE) voor details.

## 🙏 Credits

- **Easee API**: [developer.easee.com](https://developer.easee.com/)
- **Tibber API**: [developer.tibber.com](https://developer.tibber.com/)
- **Domoticz Platform**: [www.domoticz.com](https://www.domoticz.com/)

---

**Versie 10.2.8** - Gemaakt door Richard Leunk

**Status**: ✅ Production Ready
