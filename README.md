# Easee Domoticz plugin v10.9.16

**Easee-laadpalen, Equalizer (meterkast) en Tibber in Domoticz — modulaire plugin, custom tegeliconen, compacte statusweergave.**

![Version](https://img.shields.io/badge/version-10.9.15-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

> **Status:** v10.9.16 — *stable testing* (pauze in actieve ontwikkeling). Getest met 2× Charge Lite, 1× Equalizer en Tibber. Bugreports welkom via [Issues](https://github.com/rleunk/easee-domoticz/issues).

## TL;DR — installeren in 2 minuten

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v10.9.10** → Easee-gebruikersnaam + wachtwoord → **Create**.

Optioneel: Tibber-token (Mode7), laadpaalnamen (Mode2/3/4), Equalizer-naam (Address).

> Git-authenticatie: [docs/GIT_SETUP.md](docs/GIT_SETUP.md) · Problemen: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Wat doet deze plugin?

- Auto-detectie van laadpalen en Equalizer
- Live vermogen, status en load balancing in Domoticz
- Kosten via Tibber (sessie, dag, goedkoopste laadwindow)
- 13 custom tegeliconen (P-max laadpaal + Equalizer-puck) — auto-load + handmatige upload als fallback
- Modulaire codebase (sinds v10.6) — updates via `git pull`

## Voor wie is dit?

- Domoticz-gebruikers met Easee-laadpaal(en)
- Met of zonder Equalizer (meterkast)
- Optioneel met Tibber-energiecontract
- Geen programmeerkennis nodig — scannable tegels en Nederlandse status

## Features

| Onderdeel | Wat je krijgt |
|-----------|---------------|
| **Laadpalen** | Auto-discovery; per lader: Laden, Totaal & Sessie, Status, Kosten (met Tibber) |
| **Equalizer** | 2 tegels per Equalizer: **Status** (LB, limieten, stroom, spanning) + **Vermogen** (import/terug/netto W, vandaag kWh) |
| **Tibber** | Actueel tarief, dagkosten, **Beste laden** (3 uur goedkoop) |
| **Core** | Globale Status, Totaal Laden, Totaal kWh, LoadBal-schakelaar |
| **Iconen** | 13 sets in `Easee_icons_v2.zip`; zie [Custom iconen](#-custom-iconen) |
| **Upgrade** | `git pull` + hardware herstarten; bij icon-wijzigingen zip opnieuw uploaden |

Verder: eigen namen per laadpaal (Mode2/3/4), state in `easee_state.json`, gestructureerde logging `[Easee v10.9.10][LEVEL]…`.

## Screenshots

### Dashboard (illustratie)

![Illustratief dashboard-overzicht](docs/screenshot-dashboard.png)

*Illustratief tegeloverzicht — geen echte Domoticz-screenshot. Toont globale tegels, laadpaal (Garage) en Equalizer (Meterkast).*

### Iconen (actuele referentie)

![Alle 13 iconensets — preview](docs/icon-preview-v2.png)

*Actuele iconensets v10.9.10, inclusief `EaseeStatusGlobal` (combo) en `EaseeStatus` (laadpaal-only).*

### Equalizer-tegels (illustratie)

![Equalizer puck en laadpaal-iconen](docs/screenshot-equalizer.png)

*Illustratie van custom iconen met LED-kleuren en functie-badges — geen live Domoticz-capture.*

## Ondersteunde scenario's

| Scenario | Wat werkt | Configuratie |
|----------|-----------|--------------|
| **1 laadpaal** | Alle laadpaal-tegels + totaal | Alleen **Mode2** (optioneel) |
| **2 laadpalen** | Per lader eigen tegels | **Mode2** + **Mode3** (optioneel) |
| **3+ laadpalen** | Auto-discovery + tegels per lader | **Mode4** (komma-gescheiden vanaf lader 3) |
| **Geen Equalizer** | Plugin werkt volledig | Geen meterkast-tegels; Status toont `Geen EQ` |
| **Geen Tibber** | Laadpalen + Equalizer OK | Geen kosten-/tarief-tegels |

Laat naamvelden leeg voor de Easee-appnaam. De **hardwarenaam** in Domoticz (bijv. `Easee`) is het prefix op alle tegels.

## Devices

### Core
- **Easee - Status** — online, Equalizer-aantal, load balancing, Tibber
- **Totaal Laden**, **Totaal kWh**, **LoadBal**
- **Kosten & Samenvatting**, **Beste laden** (met Tibber)

### Per Equalizer
- **[Naam] - Status** — verbinding, LB (fase-detail), limieten, stroom L1/L2/L3, spanning
- **[Naam] - Vermogen** — import/terug/netto W, vandaag import en netto kWh (Text-tegel)

### Per laadpaal
- **[Naam] - Laden**, **Totaal & Sessie**, **Status**, **Kosten (Sessie/Dag)** (met Tibber)

Details: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Custom iconen

De plugin levert **13 iconensets** via **`Easee_icons_v2.zip`** (master zip + map `icons/` met 13 mini-zips).

**Automatisch:** bij pluginstart geladen en toegepast op bestaande tegels na herstart.

**Handmatig** (als log `image_ids: 0/13` of generieke iconen):
1. Verwijder oude Easee custom icons via **Instellingen → Aangepaste pictogrammen**
2. Upload `Easee_icons_v2.zip`
3. Herstart hardware-item

Verwacht in log: `Custom icons geladen: 13 sets` of `Custom icons uit Domoticz (handmatig geüpload)`.

### Welke tegel krijgt welk icoon?

| Iconenset | Tegel(s) |
|-----------|----------|
| **EaseeStatusGlobal** | Alleen globale **Easee - Status** (laadpaal + EQ-puck + **i**) |
| **EaseeStatus** | Laadpaal **Status** per locatie (bijv. Garage, Voordeur) — laadpaal + **i**, geen EQ |
| **EaseeEqualizer** | Equalizer **Status** en **Vermogen** (Meterkast) |
| **EaseeCharger** | Laadpaal **Laden** |
| **EaseePower** | **Totaal Laden**, laadpaal **Totaal & Sessie** |
| **EaseeCost** | Kosten-tegels |
| **EaseeOverview** | **Beste laden**, overzicht |
| **EaseeLoadBal** | **LoadBal**-schakelaar |
| Overige sets | Legacy/gereserveerd (Import, Export, Net, Voltage, Alert) |

**Bekende beperking:** sommige **Energy**-tegels (bliksem/globe) tonen ondanks custom Image het Domoticz-standaardicoon — bekend Domoticz-gedrag.

Volledige LED/badge-tabel: [INSTALL.md — Custom iconen](INSTALL.md#custom-iconen-handmatig-uploaden) · preview: [docs/icon-preview-v2.png](docs/icon-preview-v2.png).

## Configuratie (kort)

| Parameter | Standaard | Omschrijving |
|-----------|-----------|--------------|
| Username / Password | — | Easee-inlog (verplicht) |
| Poll interval (Mode1) | 30 sec | API-interval |
| Debug (Mode6) | Normal | Zet op *Debug* bij problemen |
| Mode2 / Mode3 / Mode4 | — | Laadpaalnamen 1 / 2 / 3+ |
| Address / IP | — | Equalizer-naam / handmatig ID |
| Tibber token (Mode7) | — | Optioneel |

Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Updates & upgrade

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

**Na elke upgrade:** herstart het Easee hardware-item in Domoticz.

**Bij icon-wijzigingen (v10.9.5+):** upload **`Easee_icons_v2.zip` opnieuw** via Aangepaste pictogrammen. Controleer log: `image_ids: 13/13 sets`.

Stap-voor-stap: [INSTALL.md](INSTALL.md).

## Changelog & release

- Volledige geschiedenis: [CHANGELOG.md](CHANGELOG.md)
- Laatste release: **[v10.9.16](https://github.com/rleunk/easee-domoticz/releases/tag/v10.9.16)** — fix Equalizer Vermogen 429/API-druk

### v10.9.x in het kort

| Versie | Thema |
|--------|-------|
| **10.9.10** | Combo-icoon alleen op *Easee - Status*; `EaseeStatusGlobal` |
| **10.9.9** | Combo-icoon op Status (later gesplitst in 10.9.10) |
| **10.9.8** | Icon mapping: laadpaal Status → `EaseeStatus`; EQ Vermogen → `EaseeEqualizer` |
| **10.9.3–10.9.7** | Icon laden/toepassen fixes (zip-pad, plugin-key prefix, `Device.Update`) |
| **10.9.1** | Equalizer: 2 tegels (Status + Vermogen) |
| **10.9.0** | Equalizer geconsolideerd (was 6 tegels in v10.8) |

## Troubleshooting (snel)

| Probleem | Zie |
|----------|-----|
| Plugin niet in lijst | [INSTALL.md](INSTALL.md) — pad + `python3-requests` |
| Geen iconen | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — custom iconen |
| Login mislukt | Credentials + rate limit (5–10 min wachten) |
| Geen Equalizer | Debug aan; handmatig ID in IP-veld |
| Kosten 0 € | Tibber-token; tile verwijderen + hardware herstarten |
| Verkeerd icoon op tegel | Upgrade naar v10.9.10+; zip opnieuw uploaden |

## Module structuur

Sinds v10.6.0: 13 Python-modules naast `Easee_icons_v2.zip`. Overzicht: [docs/REFACTOR_MAPPING.md](docs/REFACTOR_MAPPING.md).

## Problemen melden

[GitHub Issues](https://github.com/rleunk/easee-domoticz/issues) → **Bug melden** (Nederlands formulier). Vermeld pluginversie **v10.9.10**, Domoticz-versie en logregels `[Easee v…]` (geen wachtwoorden).

## Support & credits

- **Repo:** [github.com/rleunk/easee-domoticz](https://github.com/rleunk/easee-domoticz)
- **Installatie:** [INSTALL.md](INSTALL.md)
- **Easee API:** [developer.easee.com](https://developer.easee.com/) · **Tibber:** [developer.tibber.com](https://developer.tibber.com/)

MIT License — [LICENSE](LICENSE)

---

**Versie 10.9.10** — Richard Leunk
