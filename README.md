# Easee Domoticz plugin v10.11.1

**Easee-laadpalen, Equalizer (meterkast) en Tibber in Domoticz — modulaire plugin, custom tegeliconen, compacte statusweergave.**

![Version](https://img.shields.io/badge/version-10.11.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Domoticz-orange)

> **Status:** v10.11.1 — compacte tegels (11 i.p.v. 16 bij 2 laders + EQ + Tibber). **Stable baseline: v10.10.8-stable** ([STABLE.md](STABLE.md)) — test v10.11.x eerst voordat je stable wijzigt.

## TL;DR — installeren in 2 minuten

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v10.11.1** → Easee-gebruikersnaam + wachtwoord → **Create**.

Optioneel maar **verplicht voor kosten-tegels**: Tibber-token (Mode7). Verder optioneel: laadpaalnamen (Mode2/3/4), Equalizer-naam (Address).

> Git-authenticatie: [docs/GIT_SETUP.md](docs/GIT_SETUP.md) · Problemen: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Wat doet deze plugin?

- Auto-detectie van laadpalen en Equalizer
- Live vermogen, status en load balancing in Domoticz
- Kosten via Tibber (sessie, dag, goedkoopste laadwindow) — **Tibber-token (Mode7) vereist**
- 13 custom tegeliconen (P-max laadpaal + Equalizer-puck) — auto-load + handmatige upload als fallback
- Modulaire codebase (sinds v10.6) — updates via `git pull`

## Voor wie is dit?

- Domoticz-gebruikers met Easee-laadpaal(en)
- Met of zonder Equalizer (meterkast)
- Optioneel met Tibber-energiecontract (voor kosten/tarief-tegels)
- Geen programmeerkennis nodig — scannable tegels en Nederlandse status

## Features

| Onderdeel | Wat je krijgt |
|-----------|---------------|
| **Laadpalen** | Auto-discovery; per lader: **Laden** (grafiek + sessie in Description), **Status** (incl. kosten bij Tibber) |
| **Equalizer** | 2 tegels per Equalizer: **Status** (LB, limieten, stroom, spanning) + **Vermogen** (import/terug/netto W, vandaag kWh) |
| **Tibber** | Actueel tarief, **Dag overzicht**, **Beste laden** (configureerbaar venster) — **Mode7 verplicht** |
| **Core** | Globale Status, Totaal Laden, Totaal kWh, LoadBal-schakelaar |
| **Iconen** | 13 sets in `Easee_icons_v2.zip`; zie [Custom iconen](#-custom-iconen) |
| **Upgrade** | `git pull` + hardware herstarten; bij icon-wijzigingen zip opnieuw uploaden |

Verder: eigen namen per laadpaal (Mode2/3/4), state in `easee_state.json`, gestructureerde logging `[Easee v10.11.1][LEVEL]…`.

## Logniveaus (kort)

| Niveau | Wanneer zichtbaar | Voorbeelden |
|--------|-------------------|-------------|
| **INFO** | Altijd (Mode6 = Normal) | Plugin gestart, Tibber actief/uit, iconen geladen (`image_ids: 13/13`), migratie bij upgrade |
| **DEBUG** | Alleen bij Mode6 = *Debug* | Poll voltooid, kosten-tegel bijgewerkt, siteStructure-details, per-tegel iconen, **verwachte optionele API 403/405** |
| **WARNING** | Altijd | Kosten-tegel niet gevonden, **HTTP 429**, iconen ontbreken |
| **ERROR** | Altijd | Login mislukt, zip laden mislukt |

Zet **Debug logging** (Mode6) alleen aan als je problemen onderzoekt — dan wordt het log veel uitgebreider.

## Screenshots

> **Let op:** de afbeeldingen hieronder zijn **gesanitiseerde demo-mockups** in echte Domoticz-tegelstijl (lichtgrijze achtergrond, witte tegels met lichtblauwe header, italic *Laatst gezien*, *Type:*-regel, footer met ster links en Log/Aanpassen-knoppen) — geen live Domoticz-data. Alle getallen zijn **0** / **€0.00**. De README-demo toont **10 tegels** met **één laadpaal** (*Lader 1*); **2 laadpalen + EQ + Tibber** = **11 tegels** (zie [CONFIGURATION.md](docs/CONFIGURATION.md)). Opnieuw genereren: `scripts/generate_dashboard_mockup.ps1`.

### Dashboard (10 demo-tegels)

![Domoticz dashboard — gesanitiseerde demo](docs/screenshot-dashboard.png)

*Demo-layout (3×4, 10 tegels): globale tegels incl. LoadBal + Dag overzicht, 2 laadpaal-tegels (*Lader 1*), 2 Equalizer-tegels (*Meterkast*).*

### Iconen (actuele referentie)

![Alle 13 iconensets — preview](docs/icon-preview-v2.png)

*Actuele iconensets v10.9.18+, inclusief `EaseeStatusGlobal` (combo: EQ linksonder, laadpaal rechtsboven) en `EaseeStatus` (laadpaal-only). Gegenereerde preview, geen Domoticz-capture.*

### Equalizer & combo-icoon (demo)

![Equalizer-tegels en StatusGlobal combo](docs/screenshot-equalizer.png)

*Close-up in Domoticz-tegelstijl: combo-icoon op globale Status, Meterkast Status (LB/fase/spanning) en Vermogen (import/terug/netto). Gesanitiseerde waarden.*

## Ondersteunde scenario's

| Scenario | Wat werkt | Configuratie |
|----------|-----------|--------------|
| **1 laadpaal** | Alle laadpaal-tegels + totaal | Alleen **Mode2** (optioneel) |
| **2 laadpalen** | Per lader eigen tegels | **Mode2** + **Mode3** (optioneel) |
| **3+ laadpalen** | Auto-discovery + tegels per lader | **Mode4** (komma-gescheiden vanaf lader 3) |
| **Geen Equalizer** | Plugin werkt volledig | Geen meterkast-tegels; Status toont `Geen EQ` |
| **Geen Tibber** | Laadpalen + Equalizer OK | Geen kosten-/tarief-tegels; log: *Tibber uit* |

Laat naamvelden leeg voor de Easee-appnaam. De **hardwarenaam** in Domoticz (bijv. `Easee`) is het prefix op alle tegels.

## Devices

### Core
- **Easee - Status** — online, Equalizer-aantal, load balancing, Tibber
- **Totaal Laden**, **Totaal kWh**, **LoadBal**
- **Kosten & Samenvatting**, **Beste laden**, **Dagrapport** (met Tibber, Mode7)

### Per Equalizer
- **[Naam] - Status** — verbinding, LB (fase-detail), limieten, stroom L1/L2/L3, spanning
- **[Naam] - Vermogen** — import/terug/netto W, vandaag import en netto kWh (Text-tegel)

### Per laadpaal
- **[Naam] - Laden**, **Totaal & Sessie**, **Status**, **Kosten (Sessie/Dag)** (met Tibber, Mode7)

Details: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Custom iconen

De plugin levert **13 iconensets** via **`Easee_icons_v2.zip`** (master zip + map `icons/` met 13 mini-zips).

**Automatisch:** bij pluginstart geladen en toegepast op bestaande tegels na herstart.

**Handmatig** (als log `image_ids: 0/13` of generieke iconen):
1. Verwijder oude Easee custom icons via **Instellingen → Aangepaste pictogrammen**
2. Upload `Easee_icons_v2.zip`
3. Herstart hardware-item

Verwacht in log: `Custom icons geladen: 13 sets` of `Custom icons uit Domoticz (handmatig geüpload)` en `image_ids: 13/13 sets`.

### Welke tegel krijgt welk icoon?

| Iconenset | Tegel(s) |
|-----------|----------|
| **EaseeStatusGlobal** | Alleen globale **Easee - Status** (laadpaal + EQ-puck + **i**) |
| **EaseeStatus** | Laadpaal **Status** per locatie (bijv. Lader 1, Garage, Voordeur) — laadpaal + **i**, geen EQ |
| **EaseeEqualizer** | Equalizer **Status** en **Vermogen** (Meterkast) |
| **EaseeCharger** | Laadpaal **Laden** |
| **EaseePower** | **Totaal Laden**, laadpaal **Totaal & Sessie** |
| **EaseeCost** | Kosten-tegels |
| **EaseeOverview** | **Beste laden**, **Dagrapport**, overzicht |
| **EaseeLoadBal** | **LoadBal**-schakelaar |
| Overige sets | Legacy/gereserveerd (Import, Export, Net, Voltage, Alert) |

**Bekende beperking:** sommige **Energy**-tegels (bliksem/globe) tonen ondanks custom Image het Domoticz-standaardicoon — bekend Domoticz-gedrag.

Volledige LED/badge-tabel: [INSTALL.md — Custom iconen](INSTALL.md#custom-iconen-handmatig-uploaden) · preview: [docs/icon-preview-v2.png](docs/icon-preview-v2.png).

## Configuratie (kort)

| Parameter | Standaard | Omschrijving |
|-----------|-----------|--------------|
| Username / Password | — | Easee-inlog (verplicht) |
| Poll interval (Mode1) | 30 sec | API-interval; zet op **60 sec** bij 429-waarschuwingen (zie [CONFIGURATION.md](docs/CONFIGURATION.md)) |
| Debug (Mode6) | Normal | Zet op *Debug* bij problemen — toont extra DEBUG-regels |
| Mode2 / Mode3 / Mode4 | — | Laadpaalnamen 1 / 2 / 3+ |
| Address / IP | — | Equalizer-naam / handmatig ID |
| Tibber token (Mode7) | — | **Vereist voor kosten-tegels** (per lader + globaal) |

Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Updates & upgrade

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.10.8-stable   # huidige stable; of: git pull op main
sudo systemctl restart domoticz
```

**Na elke upgrade:** herstart het Easee hardware-item in Domoticz. Zie [STABLE.md](STABLE.md) voor stable-tags en rollback.

**Bij icon-wijzigingen (v10.9.5+):** upload **`Easee_icons_v2.zip` opnieuw** via Aangepaste pictogrammen. Controleer log: `image_ids: 13/13 sets`.

Stap-voor-stap: [INSTALL.md](INSTALL.md).

## Changelog & release

- Volledige geschiedenis: [CHANGELOG.md](CHANGELOG.md)
- **Huidige stable:** **[v10.10.8-stable](https://github.com/rleunk/easee-domoticz/releases/tag/v10.10.8)** — Tibber kwartierprijzen, Dagrapport, sessie-kWh-fixes
- Vorige stable: [v10.9.32-stable](https://github.com/rleunk/easee-domoticz/releases/tag/v10.9.32) (rollback)

### v10.9.19 – v10.9.28 in het kort

| Versie | Thema |
|--------|-------|
| **10.9.28** | Versies gesynchroniseerd; kosten-tegels niet meer vast op €0,00; stale sessionEnergy-fix; cost_track migratie |
| **10.9.27** | Negatieve Vandaag kWh (v10.9.26-regressie) opgelost; lifetime Counter + dagtracking |
| **10.9.26** | Vandaag kWh ~3 kWh-fix; kosten timestamp/delta; state migratie |
| **10.9.24–10.9.25** | Middernacht-baseline dag-kWh; display_wh reset na middernacht |
| **10.9.21–10.9.23** | Kosten DeviceID lookup (legacy); 429/herstart fallback; sessie-kWh decimalen |
| **10.9.19–10.9.20** | Legacy *Kosten*-tegel lookup; sessielabel tijdens laden |

### Eerdere v10.9.x

| Versie | Thema |
|--------|-------|
| **10.9.18** | `EaseeStatusGlobal` combo-icoon verfijnd |
| **10.9.17** | Equalizer Vermogen sticky power; per-endpoint rate limit |
| **10.9.11–10.9.16** | Equalizer poll/429/observations fixes |
| **10.9.0–10.9.10** | Equalizer 2 tegels; icon mapping; combo-icoon |

## Troubleshooting (snel)

| Probleem | Zie |
|----------|-----|
| Plugin niet in lijst | [INSTALL.md](INSTALL.md) — pad + `python3-requests` |
| Geen iconen | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — custom iconen |
| Login mislukt | Credentials + rate limit (5–10 min wachten) |
| Geen Equalizer | Debug aan; handmatig ID in IP-veld |
| Kosten 0 € / geen kosten-tegels | **Tibber-token (Mode7)** invullen; tile verwijderen + hardware herstarten |
| 429 rate limit in log | Poll interval (Mode1) op **60 sec** — [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#http-429-rate-limit-easee-api)
| Verkeerd icoon op tegel | Upgrade naar v10.9.18+; zip opnieuw uploaden |

## Module structuur

Sinds v10.6.0: 13 Python-modules naast `Easee_icons_v2.zip`. Overzicht: [docs/REFACTOR_MAPPING.md](docs/REFACTOR_MAPPING.md).

## Problemen melden

[GitHub Issues](https://github.com/rleunk/easee-domoticz/issues) → **Bug melden** (Nederlands formulier). Vermeld pluginversie **v10.10.8** (of stable-tag), Domoticz-versie en logregels `[Easee v…]` (geen wachtwoorden).

## Support & credits

- **Repo:** [github.com/rleunk/easee-domoticz](https://github.com/rleunk/easee-domoticz)
- **Installatie:** [INSTALL.md](INSTALL.md)
- **Easee API:** [developer.easee.com](https://developer.easee.com/) · **Tibber:** [developer.tibber.com](https://developer.tibber.com/)

MIT License — [LICENSE](LICENSE)

---

**Versie 10.10.8** (stable: v10.10.8-stable) — Richard Leunk
