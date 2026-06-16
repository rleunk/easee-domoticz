# Easee Domoticz Plugin v10.4.0

**Complete Easee laadpaal integratie voor Domoticz met compacte UI, intelligente emoji indicators, Equalizer/meterkast ondersteuning en Tibber stroomtarief integratie.**

![Version](https://img.shields.io/badge/version-10.4.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

## ✨ Features

✨ **Auto-Discovery** — Automatische detectie van alle Easee laadpalen en Equalizer  
📊 **Realtime Monitoring** — Live vermogen, energie en status updates  
💬 **Leesbare status** — Laadstatus in Nederlands (Laden, Wacht op start, …)  
🏷️ **Eigen namen** — Optionele namen per laadpaal via Mode2/Mode3  
⚖️ **Equalizer / Meterkast** — Auto-discovery, load balancing, hoofdzekering en eMobility-limieten  
⚡ **Hoofdzekering limiet** — Correcte weergave via `maxContinuousCurrent` en `circuit.fuse` (API)  
💰 **Cost Tracking** — Sessie- en dagkosten per laadpaal (v10.4 fix)  
💵 **Tibber Integration** — Actueel stroomtarief, goedkope laadwindows en kostenoverzicht (v10.4 fix)  
🎨 **Compact UI** — Intelligente samengevoegde tegels met emoji indicators  
🔐 **Secure** — Veilige token opslag en session management  
🔄 **State Persistence** — Behoudt laadsessie gegevens over restarts  
📦 **Git installatie** — Eenvoudige updates via `git pull` op je Domoticz-server  

## 📦 Installatie

Zie **[INSTALL.md](INSTALL.md)** voor stap-voor-stap instructies (Debian/Domoticz).

> Git-authenticatie (SSH of PAT): [docs/GIT_SETUP.md](docs/GIT_SETUP.md)

### Quick Start

Op je Domoticz-server (Debian):

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
sudo systemctl restart domoticz
```

Daarna in Domoticz:

1. **Setup → Hardware**
2. Type: **"Easee AutoDiscovery Compact v10.4.0"**
3. Geef de hardware een naam, bijv. `Easee` (prefix op alle tegels)
4. Username/Password: jouw Easee-inloggegevens
5. **Create**

Alternatief: automatisch installatiescript — zie [INSTALL.md](INSTALL.md).

## ⚙️ Configuratie

Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md) voor alle beschikbare parameters.

### Basis Settings

| Parameter | Standaard | Omschrijving |
|-----------|-----------|--------------|
| Username | - | Easee account username/telefoonnummer |
| Password | - | Easee account wachtwoord |
| Poll interval (Mode1) | 30 sec | Hoe vaak data wordt opgehaald |
| Debug logging (Mode6) | Normal | Zet op *Debug* bij problemen |
| Naam laadpaal 1 (Mode2) | - | Optioneel, bijv. `Charge Lite Links` |
| Naam laadpaal 2 (Mode3) | - | Optioneel, bijv. `Charge Lite Rechts` |
| Naam Equalizer (Address) | - | Optioneel, bijv. `Meterkast` |
| Equalizer ID (IP) | - | Handmatig, alleen als discovery faalt |
| Tibber token (Mode7) | - | Optioneel: Tibber API token voor prijzen |

## 📊 Devices

### Core Devices
- **Status** — Online status, Equalizer-aantal, load balancing, Tibber-status
- **Totaal Laden** — Huidige vermogen (Watt)
- **Totaal kWh** — Totaal geladen energie
- **LoadBal** — Load balancing schakelaar (Equalizer)
- **Kosten & Samenvatting** — Dagkosten, actueel Tibber-tarief, energie/belasting
- **Beste laden** — Goedkoopste laadwindow (3 uur, met Tibber)

### Per Equalizer (indien gevonden)
- **[Naam] - Status** — online, load balancing, limieten, hoofdzekering, actuele stroom, huisvermogen
- **[Naam] - Vermogen** — actueel vermogen (Watt)

### Per Laadpaal
- **[Naam] - Laden** — Power meter (Watt)
- **[Naam] - Totaal & Sessie** — Totaal en sessie kWh
- **[Naam] - Status** — Laadstatus in Nederlands + emoji
- **[Naam] - Kosten (Sessie/Dag)** — Sessie- en dagkosten (met Tibber)

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
- `⚡⚡` = Hoog vermogen (>7 kW)
- `⚡` = Medium vermogen (>3,5 kW)
- `🔌` = Laag vermogen (>50 W)
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

**Kosten-tile toont "0 €"?** Verwijder de **Kosten (Sessie/Dag)**-tile en herstart het hardware-item — het device wordt opnieuw aangemaakt (v10.4.0 fix).

## 📝 Changelog

Zie [CHANGELOG.md](CHANGELOG.md) voor volledige versiegeschiedenis.

## 🆙 Updates

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

**Van v10.3.4 naar v10.4.0?** Vervang `plugin.py` of doe `git pull` — state (`easee_v9_0_state.json`) en bestaande devices blijven behouden.

## 🤖 AI Development

Deze plugin is in meerdere stappen ontwikkeld met behulp van AI-tools, onder begeleiding en review van de auteur:

| Fase | Tool | Rol |
|------|------|-----|
| Eerste versies (v9.x – v10.2) | **Copilot** | Initiële opzet, API-integratie en device-logica |
| Verdere ontwikkeling (v10.3+) | **GitHub Copilot** | Uitbreidingen, bugfixes en feature-iteraties |
| Verfijning & documentatie (v10.4) | **Cursor** | Code-review, stabilisatie en repository-documentatie |

Alle functionele keuzes, configuratie en productie-inzet worden door Richard Leunk beheerd.

## 🤝 Support

- **Issue tracker**: [GitHub Issues](https://github.com/rleunk/easee-domoticz/issues)
- **Documentatie**: [INSTALL.md](INSTALL.md) · [docs/](docs/)
- **Domoticz Wiki**: [wiki.domoticz.com](https://wiki.domoticz.com/)
- **Easee Developer**: [developer.easee.com](https://developer.easee.com/)

## 📄 Licentie

MIT License — zie [LICENSE](LICENSE) voor details.

## 🙏 Credits

- **Easee API**: [developer.easee.com](https://developer.easee.com/)
- **Tibber API**: [developer.tibber.com](https://developer.tibber.com/)
- **Domoticz Platform**: [www.domoticz.com](https://www.domoticz.com/)

---

**Versie 10.4.0** — Gemaakt door Richard Leunk

**Status**: ✅ Production Ready
