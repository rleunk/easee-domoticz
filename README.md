# Easee Domoticz plugin v10.5.10

**Complete Easee laadpaal integratie voor Domoticz met compacte UI, intelligente emoji indicators, Equalizer/meterkast ondersteuning en Tibber stroomtarief integratie.**

![Version](https://img.shields.io/badge/version-10.5.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

## ✨ Features

✨ **Auto-Discovery** — Automatische detectie van alle Easee laadpalen en Equalizer  
📊 **Realtime Monitoring** — Live vermogen, energie en status updates  
💬 **Leesbare status** — Laadstatus in Nederlands (Laden, Wacht op start, …)  
🏷️ **Eigen namen** — Optionele namen per laadpaal via Mode2/Mode3/Mode4  
⚖️ **Equalizer / Meterkast** — Auto-discovery, load balancing, hoofdzekering en eMobility-limieten  
⚡ **Hoofdzekering limiet** — Correcte weergave via `maxContinuousCurrent` en `circuit.fuse` (API)  
💰 **Cost Tracking** — Sessie- en dagkosten per laadpaal (v10.4 fix)  
💵 **Tibber Integration** — Actueel stroomtarief, goedkope laadwindows en kostenoverzicht (v10.4 fix)  
🎨 **Custom iconen** — Easee-tegeliconen uit `Easee_icons_v2.zip`; zie [Custom iconen](#-custom-iconen)  
🔐 **Secure** — Veilige token opslag en session management  
🔄 **State Persistence** — Behoudt laadsessie gegevens over restarts  
📦 **Git installatie** — Eenvoudige updates via `git pull` op je Domoticz-server  

## 📋 Ondersteunde scenario's

| Scenario | Wat werkt | Configuratie |
|----------|-----------|--------------|
| **1 laadpaal** | Alle laadpaal-tegels, totaal-overzicht | Alleen **Mode2** invullen (optioneel) |
| **2 laadpalen** | Per lader: Laden, Totaal & Sessie, Status (+ Kosten met Tibber) | **Mode2** + **Mode3** (optioneel) |
| **3+ laadpalen** | Auto-discovery + tegels per lader | Namen uit Easee-app **of** **Mode4** (komma-gescheiden, vanaf lader 3) |
| **Geen Equalizer** | Plugin werkt volledig | Geen meterkast-tegels; Status toont `Geen EQ` |
| **Geen Tibber** | Laadpalen + Equalizer OK | Geen kosten-/tarief-tegels; rest blijft werken |

### Laadpaalnamen (1 / 2 / 3+)

| Aantal | Velden | Voorbeeld |
|--------|--------|-----------|
| 1 lader | Mode2 (optioneel) | `Garage` |
| 2 laders | Mode2 + Mode3 (optioneel) | `Garage`, `Voordeur` |
| 3+ laders | Mode2 + Mode3 + **Mode4** | Mode4: `Carport, Werf` → 3e lader = Carport, 4e = Werf |

Laat velden leeg om de naam uit de Easee-app te gebruiken. De **hardwarenaam** in Domoticz (bijv. `Easee`) wordt automatisch als prefix op alle tegels gezet.

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
2. Type: **"Easee Domoticz plugin v10.5.10"**
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
| Extra laadpaalnamen (Mode4) | - | Komma-gescheiden vanaf lader 3, bijv. `Carport, Werf` |
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

## ⚠️ Bekende beperkingen

- Domoticz biedt beperkt aantal Mode-velden: namen voor lader 1–2 via Mode2/Mode3; lader 3+ via Mode4 (komma-gescheiden) of Easee-appnaam.
- Zonder Equalizer: geen meterkast-tegels; load balancing en fuse-limieten niet zichtbaar in Domoticz.
- Zonder Tibber: geen **Kosten & Samenvatting**, **Beste laden** of per-lader kosten-tegels.
- Device-namen wijzigen niet automatisch als je later Mode2/Mode3/Mode4 aanpast — herstart het hardware-item of verwijder en laat opnieuw aanmaken.

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

## 🎨 Custom iconen

De plugin levert acht Easee-tegeliconen via `Easee_icons_v2.zip` (v2, Easee Charge/Equalizer silhouetten) in de pluginmap; valt terug op `Easee_icons.zip`.

- **`Easee_icons_v2.zip`** — aanbevolen, meegeleverd in de pluginmap (v2 hardware-stijl)
- **`Easee_icons.zip`** — legacy fallback
- **8 icon sets:** EaseeCharger (groen), EaseePower (geel), EaseeStatus (blauw), EaseeCost (oranje), EaseeEqualizer (paars), EaseeOverview (teal), EaseeLoadBal, EaseeAlert
- **LED-strip kleur op lader-iconen:** groen=online, geel=laden, blauw=status, oranje=kosten, rood=fout, teal=overzicht (Equalizer: statusdot onderaan)
- Automatisch geladen bij pluginstart; toegepast op **bestaande** tegels na herstart van het hardware-item
- Mislukt automatisch laden? Upload de zip **eenmalig** via **Setup → Instellingen → Meer opties → Aangepaste pictogrammen**
- Verwacht logregel: `Custom icons geladen: 8 sets` of `Custom icons uit Domoticz (handmatig geüpload)`

Zie [INSTALL.md — Custom iconen handmatig uploaden](INSTALL.md#custom-iconen-handmatig-uploaden) voor details.

## 🔧 Troubleshooting

Zie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) voor veelvoorkomende problemen en oplossingen.

**Kosten-tile toont "0 €"?** Verwijder de **Kosten (Sessie/Dag)**-tile en herstart het hardware-item — het device wordt opnieuw aangemaakt (v10.4.0 fix).

## 🐛 Problemen melden

Werkt iets niet zoals verwacht? Open een issue op GitHub:

1. Ga naar **[GitHub Issues](https://github.com/rleunk/easee-domoticz/issues)** → **New issue**
2. Kies **Bug melden** (gestructureerd formulier in het Nederlands)
3. Vul minimaal in: pluginversie, Domoticz-versie, OS, beschrijving en relevante logregels (`[Easee v...]`)

Voor nieuwe ideeën: kies **Feature voorstel**. Zie eerst [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) voor veelvoorkomende oplossingen.

## 📝 Changelog

Zie [CHANGELOG.md](CHANGELOG.md) voor volledige versiegeschiedenis.

## 🆙 Updates

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

Custom iconen na upgrade: zie [Custom iconen](#-custom-iconen).

**Van v10.4.0 naar v10.5.0?** Vervang `plugin.py` of doe `git pull` — state (`easee_v9_0_state.json`) en bestaande devices blijven behouden. Nieuwe laadpalen worden automatisch gedetecteerd.

## 🚀 Release

Deze plugin staat op [GitHub](https://github.com/rleunk/easee-domoticz) als **openbare** repository. Bugreports en featurevoorstellen via [Issues](https://github.com/rleunk/easee-domoticz/issues) (Nederlandse templates).
## 🤖 AI Development

Deze plugin is in meerdere stappen ontwikkeld met behulp van AI-tools, onder begeleiding en review van de auteur:

| Fase | Tool | Rol |
|------|------|-----|
| Eerste versies (v9.x – v10.2) | **Copilot** | Initiële opzet, API-integratie en device-logica |
| Verdere ontwikkeling (v10.3+) | **GitHub Copilot** | Uitbreidingen, bugfixes en feature-iteraties |
| Verfijning & documentatie (v10.4+) | **Cursor** | Code-review, stabilisatie en repository-documentatie |

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

**Versie 10.5.10** — Gemaakt door Richard Leunk

**Status**: ✅ Production Ready
