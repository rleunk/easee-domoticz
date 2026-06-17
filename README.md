# Easee Domoticz plugin v10.9.1

**Complete Easee laadpaal integratie voor Domoticz met compacte UI, intelligente emoji indicators, Equalizer/meterkast ondersteuning en Tibber stroomtarief integratie.**

![Version](https://img.shields.io/badge/version-10.9.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

## 🚀 Wat doet deze plugin in 1 minuut

- ✅ Auto-detectie van laadpalen en Equalizer
- ✅ Live vermogen en status in Domoticz
- ✅ Kostenberekening via Tibber
- ✅ Slimme UI met emoji's en compacte tegels

**Installeren → 2 minuten, werken → direct** · [Quick Start](#quick-start)

> ⚠️ **Problemen?** Zie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📸 Screenshots

### Easee - Domoticz dashboard

![Easee Domoticz dashboard met laadpaal- en Equalizer-tegels](docs/screenshot-dashboard.png)

*Emoji-status, compacte tegels en live vermogen/kosten.*

### Equalizer & custom iconen

![Equalizer puck en P-max laadpaal iconen met functie-badges](docs/screenshot-equalizer.png)

*Custom iconen met LED-kleuren per tegelfunctie.*

## 🎯 Voor wie is dit?

- Domoticz gebruikers met Easee laadpaal
- Met of zonder Equalizer
- Optioneel met Tibber energiecontract

## ✨ Features

✨ **Auto-Discovery** — Automatische detectie van alle Easee laadpalen en Equalizer  
📊 **Realtime Monitoring** — Live vermogen, energie en status updates  
💬 **Leesbare status** — Laadstatus in Nederlands (Laden, Wacht op start, …)  
🏷️ **Eigen namen** — Optionele namen per laadpaal via Mode2/Mode3/Mode4  
⚖️ **Equalizer / Meterkast** — Auto-discovery, load balancing, hoofdzekering en eMobility-limieten  
⚡ **Hoofdzekering limiet** — Correcte weergave via `maxContinuousCurrent` en `circuit.fuse` (API)  
💰 **Cost Tracking** — Sessie- en dagkosten per laadpaal (v10.4 fix)  
💵 **Tibber Integration** — Actueel stroomtarief, goedkope laadwindows en kostenoverzicht (v10.4 fix)  
🎨 **Custom iconen** — Foto-gebaseerde P-max/EQ-max tegels uit `Easee_icons_v2.zip` met LED-kleuren en functie-badges; zie [Custom iconen](#-custom-iconen)  
🔐 **Secure** — Veilige token opslag en session management  
🔄 **State Persistence** — `easee_state.json` met atomische writes; automatische migratie van legacy state  
📋 **Gestructureerde logging** — Centrale logger `[Easee vX][LEVEL][module][context]`; zie [Logging](#-logging)  
🧩 **Modulaire codebase** — Plugin opgesplitst in losse Python-modules (sinds v10.6.0); zie [Module structuur](#-module-structuur)  
🚀 **Betrouwbare startup** — Initiële sync losgekoppeld van poll-interval; readiness-check op Domoticz Devices  
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

### Quick Start {#quick-start}

Op je Domoticz-server (Debian):

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
sudo systemctl restart domoticz
```

Daarna in Domoticz:

1. **Setup → Hardware**
2. Type: **"Easee Domoticz plugin v10.9.1"**
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
- **[Naam] - Status** — verbinding, load balancing (fase-detail), limieten, max import, L1/L2/L3 stroom (A) en spanning (V)
- **[Naam] - Vermogen** — import/terug/netto W, vandaag import en netto kWh (gecombineerde teksttegel sinds v10.9.1)

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

De plugin levert twaalf Easee-tegeliconen via **`Easee_icons_v2.zip`** (P-max productfoto laadpaal + Equalizer-max puck) in de pluginmap.

- **`Easee_icons_v2.zip`** — enige iconenarchief, meegeleverd in de pluginmap
- **12 icon sets:** EaseeCharger, EaseePower, EaseeImport, EaseeExport, EaseeNet, EaseeVoltage, EaseeStatus, EaseeCost, EaseeEqualizer, EaseeOverview, EaseeLoadBal, EaseeAlert
- **LED-strip kleur** op P-max laadpaal-foto (of LED-dot op Equalizer-puck) volgt de **tegelfunctie** — zie tabel hieronder
- **Functie-badge** rechtsonder op icoon (W, ↓, ↑, Σ, V, i, €, !, E, L) — ~30% groter sinds v10.6.0 (16px: 8px, 48px: 17px); EaseeCharger heeft geen badge
- Automatisch geladen bij pluginstart; toegepast op **bestaande** tegels na herstart van het hardware-item
- Mislukt automatisch laden? Upload de zip **eenmalig** via **Setup → Instellingen → Meer opties → Aangepaste pictogrammen**
- Verwacht logregel: `Custom icons geladen: 12 sets (Easee_icons_v2.zip)` of `Custom icons uit Domoticz (handmatig geüpload)`
- Preview: [`docs/icon-preview-v2.png`](docs/icon-preview-v2.png) · regeneratie: `.\scripts\generate_photo_icon_variants.ps1`

| Iconenset | LED-kleur | Badge | Tegelfunctie |
|-----------|-----------|-------|--------------|
| EaseeCharger | Groen `#2EA043` | — | Standaard laadpaal |
| EaseePower | Geel `#FFC107` | W | Laadpaal vermogen W/kW |
| EaseeImport | Geel `#FFC107` | ↓ | Meterkast Vermogen (import/terug/netto) |
| EaseeNet | Teal `#009688` | Σ | Meterkast terug & netto |
| EaseeVoltage | Paars `#673AB7` | V | (legacy v10.8.0 spanning-tegel) |
| EaseeStatus | Blauw `#2196F3` | i | Core status |
| EaseeCost | Oranje `#FF9800` | € | Kosten / tarief |
| EaseeAlert | Rood `#E53935` | ! | Fout / waarschuwing |
| EaseeOverview | Teal `#009688` | Σ | Overzicht |
| EaseeEqualizer | Blauw `#2196F3` | E | EQ status (LB, spanning, limieten) |
| EaseeLoadBal | Teal `#00BCD4` | L | (legacy v10.8.0 LB-detail) |

Zie [INSTALL.md — Custom iconen handmatig uploaden](INSTALL.md#custom-iconen-handmatig-uploaden) voor details.

## 🧩 Module structuur

Sinds v10.6.0 is de monolithische `plugin.py` opgesplitst in **13 Python-bestanden** (refactor op main na v10.5.18, inclusief import-fixes; v10.7.0 verkleinde `plugin.py` verder door wrapper-cleanup). Alle `.py`-bestanden horen in de pluginmap naast `Easee_icons_v2.zip`.

| Bestand | Rol |
|---------|-----|
| `plugin.py` | Domoticz lifecycle, heartbeat, orchestratie |
| `easee_constants.py` | Versie, API-URLs, device-ID's, labels |
| `easee_logging.py` | Centrale logging (DEBUG/INFO/WARNING/ERROR) |
| `easee_api.py` | Easee login, token refresh, HTTP GET |
| `easee_api_keys.py` | Gecentraliseerde API-veldnamen (fuse, charger, Tibber, …) |
| `easee_state.py` | Runtime state (`easee_state.json`), migratie, atomisch opslaan |
| `easee_helpers.py` | Gedeelde formatting en helpers |
| `domoticz_runtime.py` | Domoticz `Parameters`/`Devices`/`Images` binding |
| `domoticz_devices.py` | Device-aanmaak, index, tegel-updates |
| `domoticz_icons.py` | Laden en toepassen van custom iconen |
| `charger_logic.py` | Laadpaal discovery, poll, sessie |
| `equalizer_logic.py` | Equalizer discovery, fuse/limiet-detectie |
| `tibber_pricing.py` | Tibber GraphQL, tarieven en kosten |

Details: [`docs/REFACTOR_MAPPING.md`](docs/REFACTOR_MAPPING.md).

## 📋 Logging

Centrale logging via `easee_logging.py` (v10.6.0+):

```
[Easee v10.9.1][LEVEL][module][context] message
```

| Niveau | Wanneer zichtbaar |
|--------|-------------------|
| **DEBUG** | Alleen bij **Debug logging** (Mode6) of `ULTRA_DEBUG` |
| **INFO** | Normale logregels (login, discovery, poll-samenvatting in debug) |
| **WARNING** | Domoticz-log met ⚠ (bijv. geforceerde startup-sync na 60s) |
| **ERROR** | Domoticz Error-log (API-fouten, device-aanmaak, state-save) |

Bij problemen: zet Mode6 op *Debug* en zoek op `[Easee v` in het Domoticz-log.

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

**Sinds v10.6.0:** gebruik `git pull` (alle `.py`-modules), niet alleen `plugin.py`. State-bestand heet `easee_state.json` (automatische rename van `easee_v9_0_state.json`).

### Recente wijzigingen (v10.5.18 → v10.7.2)

| Versie | Belangrijkste wijzigingen |
|--------|---------------------------|
| **v10.9.1** | Equalizer 2 tegels (Status + Vermogen Text); icon fix na fresh add; legacy Import/Terug & netto → Vermogen |
| **v10.9.0** | Equalizer tegels geconsolideerd: 3 tegels (Status, Import, Terug & netto); spanning/LB-detail op Status; legacy Netto/Teruglevering → Terug & netto |
| **v10.8.0** | Equalizer Proposal C: 6 meterkast-tegels; Import/Teruglevering/Netto/Spanning/LB-detail; 4 nieuwe icon sets; legacy Vermogen → Import |
| **v10.5.18** | Definitieve foto-iconen (P-max laadpaal, Equalizer-max puck); LED-kleur per tegelfunctie; functie-badges; alleen nog `Easee_icons_v2.zip` |
| **Module refactor** | `plugin.py` opgesplitst in modules op main (zelfde basis als 10.5.18); fixes voor Domoticz-imports en Parameters-binding |
| **v10.6.0** | `easee_logging.py`; state → `easee_state.json` + migratie; functie-badges ~30% groter |
| **v10.6.1** | Atomisch state opslaan (`.tmp` + `os.replace`) tegen corrupt JSON bij crash |
| **v10.6.2** | Device-aanmaak: bij mislukte `Device.Create()` worden kwargs + traceback gelogd |
| **v10.6.3** | `easee_api_keys.py` — gecentraliseerde API-veldnamen i.p.v. magic strings |
| **v10.6.4** | Startup-sync losgekoppeld van poll-interval: 3s min. vertraging, readiness-check op Devices, 60s fallback |
| **v10.6.5** | Equalizer Vermogen-tegel: **Vandaag** kWh via observation 45 (cumulatief import); fallback vermogensintegratie |
| **v10.7.0** | Code cleanup: ~150 passthrough-wrappers verwijderd; directe module-aanroepen; `plugin.py` kleiner; geen functionele wijzigingen |
| **v10.7.1** | Fix: onHeartbeat crash door `power_emoji`/`status_emoji` naam-shadowing in `poll_charger` |
| **v10.7.2** | Fix: onHeartbeat crash door verwijderde `plugin.is_*_limit_key` wrappers in `equalizer_logic` |

**Upgrade vanaf v10.5.x:** `git pull`, herstart hardware-item. Upload **`Easee_icons_v2.zip` opnieuw** (v10.5.18 iconen + v10.6.0 grotere badges). State en devices blijven behouden.

**Upgrade naar v10.9.1:** `git pull`, herstart hardware-item. Bestaande *Import*- of *Terug & netto*-tegel wordt hernoemd naar *Vermogen* (één tegel); verwijder eventuele wees-tegels handmatig. Controleer log op `Custom icons geladen: 12 sets` — anders upload `Easee_icons_v2.zip` opnieuw via Instellingen → Aangepaste pictogrammen.

**Upgrade naar v10.9.0:** `git pull`, herstart hardware-item. Bestaande *Netto*- of *Teruglevering*-tegel wordt hernoemd naar *Terug & netto*; *Spanning* en *Load balancing* blijven als wees-tegels (handmatig verwijderen). Geen nieuwe icon zip nodig.

**Upgrade naar v10.8.0:** `git pull`, **upload `Easee_icons_v2.zip` opnieuw** (12 sets), herstart hardware-item. Bestaande *Vermogen*-tegel wordt automatisch hernoemd naar *Import*; nieuwe tegels (Teruglevering, Netto, Spanning, Load balancing) worden aangemaakt bij eerste poll.

**Upgrade naar v10.7.x:** `git pull`, herstart hardware-item. Geen state-migratie nodig; v10.7.1 en v10.7.2 lossen regressies op na de wrapper-cleanup in v10.7.0.

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

**Versie 10.9.1** — Gemaakt door Richard Leunk

**Status**: ✅ Production Ready
