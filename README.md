# Easee Domoticz Plugin v9.0

**Complete Easee laadpaal integratie voor Domoticz met compacte UI, intelligente emoji indicators en Tibber stroomtarief integratie.**

![Version](https://img.shields.io/badge/version-9.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

## 🚀 Features

✨ **Auto-Discovery** - Automatische detectie van alle Easee laadpalen  
📊 **Realtime Monitoring** - Live power, energy en status updates  
💰 **Cost Tracking** - Automatische berekening van laadkosten  
💵 **Tibber Integration** - Stroomtarieven en goedkope laadwindows  
🎨 **Compact UI** - Intelligente samengevoegde tegels met emoji indicators  
🔐 **Secure** - Veilige token opslag en session management  
🔄 **State Persistence** - Behoudt laadsessie gegevens over restarts  

## 📦 Installatie

Zie [INSTALLATION.md](docs/INSTALLATION.md) voor stap-voor-stap instructies.

### Quick Start

1. **Clone repository**
   ```bash
   git clone https://github.com/rleunk/easee-domoticz.git
   cd easee-domoticz
   ```

2. **Kopieer naar Domoticz plugins**
   ```bash
   cp -r . /home/domoticz/userdata/plugins/Easee/
   ```
   (Pas het pad aan voor jouw Domoticz installatie)

3. **Restart Domoticz**
   ```bash
   sudo systemctl restart domoticz
   ```

4. **Voeg plugin toe in Domoticz UI**
   - Setup → Hardware
   - Type: "Easee AutoDiscovery Compact v9.0"
   - Username/Password: Jouw Easee credentials
   - Create

## ⚙️ Configuratie

Zie [CONFIGURATION.md](docs/CONFIGURATION.md) voor alle beschikbare parameters.

### Basis Settings

| Parameter | Standaard | Omschrijving |
|-----------|-----------|---------------|
| Username | - | Easee account username/telefoonnummer |
| Password | - | Easee account wachtwoord |
| Poll interval | 30 sec | Hoe vaak data wordt opgehaald |
| Device prefix | "Easee" | Prefix voor alle devices |
| Site filter | - | Optioneel: filter op sitenaam |
| Tibber token | - | Optioneel: Tibber API token voor prijzen |

## 📊 Devices

### Core Devices
- **Status** - Online status en Tibber status
- **Totaal Laden** - Huidige vermogen (Watt)
- **Totaal kWh** - Totaal geladen energie
- **LoadBal** - Load balancing switch (reservering)
- **Kosten & Samenvatting** - Dagelijkse kosten + emoji prijsindicator (met Tibber)
- **Beste laden** - Goedkoopste laadwindow (met Tibber)

### Per Laadpaal
- **[ID] Laden** - Power meter
- **[ID] Totaal & Sessie** - Samengevoegde energie info
- **[ID] Status** - Charger status met emoji's
- **[ID] Kosten (Sessie/Dag)** - Samengevoegde kosteninfo (met Tibber)

## 🎨 Emoji Indicators

### Power Status
- `⚡⚡` = Hoog vermogen (>7kW)
- `⚡` = Medium vermogen (>3.5kW)
- `🔌` = Laag vermogen (>50W)
- `⏸️` = Standby

### Charger Status
- `✅` = Online & Laden
- `🔴` = Online & Standby
- `❌` = Offline

### Prijs Status (Tibber)
- `🟢` = Goedkoop (untere 33%)
- `🟡` = Normaal (middel 33%)
- `🔴` = Duur (bovenste 33%)

## 🔧 Troubleshooting

Zie [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) voor veelvoorkomende problemen en oplossingen.

## 📝 Changelog

Zie [CHANGELOG.md](CHANGELOG.md) voor volledige versiegeschiedenis.

## 🤝 Support

- **Issue tracker**: [GitHub Issues](https://github.com/rleunk/easee-domoticz/issues)
- **Documentation**: [docs/](docs/)
- **Domoticz Wiki**: [wiki.domoticz.com](https://wiki.domoticz.com/)

## 📄 Licentie

MIT License - zie [LICENSE](LICENSE) voor details.

## 🙏 Credits

- Easee API: [developer.easee.com](https://developer.easee.com/)
- Tibber API: [developer.tibber.com](https://developer.tibber.com/)
- Domoticz: [www.domoticz.com](https://www.domoticz.com/)

---

**Versie 9.0** - Gemaakt door Rleunk met Copilot 🤖
