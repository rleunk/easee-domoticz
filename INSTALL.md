# Installatiehandleiding — Easee Domoticz plugin

Stap-voor-stap instructies voor installatie op een **Domoticz-server** (Debian Linux).

> **Twee versielijnen:** branch **`v1`** (ontwikkeling, huidig **0.6.1**) en **`main`** / tag **v10.11.6-stable** (legacy productie). Kies bewust welke branch je checkout — zie [STABLE.md](STABLE.md) en [VERSIONING.md](VERSIONING.md).

---

## v1 ontwikkeling (branch `v1`) — 0.6.1

| Item | Waarde |
|------|--------|
| Plugin | **Easee Domoticz plugin v1 (0.6.1)** |
| Branch | `v1` |
| Prijsbronnen | Geen, Handmatig, Tibber, ENTSO-E, EnergyZero |
| Status | Pre-release — **niet** productie-stable |

### Snel installeren (v1)

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git fetch origin
git checkout v1
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v1 (0.6.1)** → Easee-gebruikersnaam + wachtwoord → **Add**.

Kies **Prijsbron (Mode9)** in hardware-instellingen. Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md) voor Tibber (Mode7), ENTSO-E (Mode24 + e-mail goedkeuring), EnergyZero (geen token) en Handmatig.

### Upgrade naar nieuwste v1

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch origin
git checkout v1
git pull origin v1
sudo systemctl restart domoticz
```

Herstart daarna het Easee hardware-item in Domoticz. Zie [CHANGELOG.md](CHANGELOG.md) voor wijzigingen per versie.

---

## Legacy productie (branch `main` / v10.11.6-stable)

| Item | Waarde |
|------|--------|
| Plugin | Easee Domoticz plugin v10.11.6 |
| Branch / tag | `main` of `v10.11.6-stable` |
| Kosten | Alleen via **Tibber** (Mode7) |
| Status | Aanbevolen productie-baseline |

### Checkout legacy stable

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

In Domoticz: **Easee Domoticz plugin v10.11.6**. Onderstaande secties beschrijven installatie en upgrade voor **beide** lijnen (zelfde pluginmap en bestandsstructuur).

## Overzicht

| Item | Waarde |
|------|--------|
| Plugin-key | `EaseeCloudAutoDiscoveryV1000` |
| Doelmap op server | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/` |
| Hoofdbestand | `plugin.py` (+ modules + `pricing/` op v1) |
| Custom iconen | `Easee_icons_v2.zip` (automatisch geladen bij pluginstart; zie [handmatige upload](#custom-iconen-handmatig-uploaden) als dat mislukt) |
| GitHub-repo | https://github.com/rleunk/easee-domoticz |
| v1 pluginnaam | **Easee Domoticz plugin v1 (0.6.1)** — branch `v1` |
| Legacy pluginnaam | **Easee Domoticz plugin v10.11.6** — `main` / `v10.11.6-stable` |

---

## Vereisten controleren

Log in op je Domoticz-server via SSH en controleer:

### 1. Domoticz draait

```bash
systemctl status domoticz
```

### 2. Python requests beschikbaar is

```bash
python3 -c "import requests; print('OK:', requests.__version__)"
```

Als dit faalt:

```bash
sudo apt update
sudo apt install -y python3-requests
```

### 3. Git geïnstalleerd is (voor git-workflow)

```bash
git --version
```

Zo niet:

```bash
sudo apt install -y git
```

---

## Methode 1: Git clone (aanbevolen)

Deze methode maakt toekomstige updates eenvoudig via `git pull`.

### Stap 1: Git-authenticatie instellen

Kies één optie:

- **SSH (aanbevolen):** volg [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — Optie A
- **HTTPS + PAT:** volg [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — Optie B

> Heb je eerder een foutmelding gehad zoals *"Password authentication is not supported"*? Dan moet je een SSH-sleutel of Personal Access Token gebruiken — niet je GitHub-wachtwoord.

### Stap 2: Plugin clonen

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git fetch origin
git checkout v1              # v1 ontwikkeling (0.6.1)
# of: git checkout v10.11.6-stable   # legacy productie
```

Of met HTTPS (na PAT-instelling):

```bash
cd /home/root/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
```

> **Belangrijk:** de mapnaam `Easee-Domoticz-plugin` aan het einde van het commando zorgt dat `plugin.py` direct op de juiste plek staat.

### Stap 3: Controleren

```bash
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/*.py
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons_v2.zip
```

Je moet **alle `.py`-bestanden** (root + map `pricing/`), **`domoticz_energy_hints.py`** en de icon-zip zien met een recente datum. Op v1: **14** root-modules + **9** bestanden in `pricing/` (totaal **23** Python-bestanden). De icon-zip wordt bij pluginstart automatisch geladen; bestaande tegels krijgen de Easee-iconen na een herstart van het hardware-item (of Domoticz). Als automatisch laden mislukt, upload de zip eenmalig handmatig — zie [Custom iconen handmatig uploaden](#custom-iconen-handmatig-uploaden).

### Stap 4: Domoticz herstarten

```bash
sudo systemctl restart domoticz
```

### Stap 5: Plugin activeren in Domoticz

1. Open Domoticz in je browser
2. Ga naar **Setup → Hardware**
3. Voeg een nieuw hardware-item toe: **Python plugins**
4. Selecteer **Easee Domoticz plugin v1 (0.6.1)** (branch `v1`) of **Easee Domoticz plugin v10.11.6** (legacy stable)
5. Vul je Easee-gebruikersnaam en -wachtwoord in
6. Optioneel: kies **Prijsbron (Mode9)** en vul token/tarief in (v1); legacy v10 alleen Tibber (Mode7)
7. Optioneel: laadpaalnamen en Equalizer-naam
8. Klik **Add**

Na enkele seconden verschijnen de devices automatisch.

---

## Methode 2: Installatiescript

Als `install.sh` al in de repo staat (of je hebt het gekopieerd):

```bash
# Eerst eenmalig clonen (als de map nog niet bestaat)
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin

# Daarna voor updates
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
chmod +x install.sh
sudo ./install.sh
```

Het script doet een `git pull` (als de map al een repo is) of `git clone`, en herstart Domoticz.

Opties:

```bash
sudo ./install.sh --no-restart   # alleen pull, geen herstart
```

---

## Methode 3: Handmatig via zip

Gebruik dit als je geen git op de server wilt instellen.

### Stap 1: Zip downloaden

Op GitHub: **Code** → **Download ZIP**. GitHub levert een archief met een naam als `easee-domoticz-main.zip`. Pak lokaal uit; je vindt alle `.py`-modules en `Easee_icons_v2.zip` in de map `easee-domoticz-main/` (of vergelijkbaar).

### Stap 2: Uploaden naar de server

Via SCP, SFTP of WinSCP kopieer **alle `.py`-bestanden** (root + map `pricing/`), **`domoticz_energy_hints.py`** en **`Easee_icons_v2.zip`** naar de pluginmap (sinds v10.6.0 modulair — niet alleen `plugin.py`; sinds v1 ook `pricing/`):

```
Lokaal:  *.py                 → Server: .../Easee-Domoticz-plugin/
Lokaal:  pricing/*.py         → Server: .../Easee-Domoticz-plugin/pricing/
Lokaal:  Easee_icons_v2.zip  → Server: .../Easee-Domoticz-plugin/Easee_icons_v2.zip
```

Als iconen na start niet verschijnen, upload `Easee_icons_v2.zip` eenmalig handmatig — zie [Custom iconen handmatig uploaden](#custom-iconen-handmatig-uploaden).

### Stap 3: Map aanmaken (indien nodig)

```bash
mkdir -p /home/root/domoticz/plugins/Easee-Domoticz-plugin
```

### Stap 4: Bestand plaatsen

Zorg dat de structuur **plat** is:

```
Easee-Domoticz-plugin/
├── plugin.py
├── easee_constants.py
├── easee_logging.py
├── easee_api.py
├── easee_api_keys.py
├── easee_state.py
├── easee_helpers.py
├── domoticz_runtime.py
├── domoticz_devices.py
├── domoticz_icons.py
├── domoticz_energy_hints.py    ← v0.4.0+ (P1/zon/thuisbatterij hints)
├── charger_logic.py
├── equalizer_logic.py
├── tibber_pricing.py
├── pricing/                    ← v0.2.0+ (prijsbronnen)
│   ├── __init__.py
│   ├── base.py
│   ├── none.py
│   ├── manual.py
│   ├── tibber.py
│   ├── entsoe.py
│   ├── energyzero.py
│   ├── factory.py
│   └── ui.py
└── Easee_icons_v2.zip          ← custom tegeliconen (zelfde map)
```

**Fout** (submap te diep):

```
Easee-Domoticz-plugin/
└── easee-domoticz/
    └── plugin.py   ← Domoticz vindt dit niet
```

### Stap 5: Herstarten en activeren

```bash
sudo systemctl restart domoticz
```

Activeer daarna het plugin in Domoticz (zie Methode 1, stap 5).

---

## Configuratie

### Verplicht

| Veld | Wat invullen |
|------|--------------|
| Easee Username | Je Easee-login (e-mail of telefoonnummer) |
| Easee Password | Je Easee-wachtwoord |

### Optioneel — weergave

| Veld | Wat invullen | Voorbeeld |
|------|--------------|-----------|
| Poll interval (Mode1) | Seconden tussen updates | `30` |
| Debug logging (Mode6) | *Debug* bij problemen | `Debug` |
| Site filter (Mode5) | Filter op sitenaam | `Thuis` |

### Optioneel — laadpaalnamen

| Scenario | Velden | Voorbeeld |
|----------|--------|-----------|
| **1 laadpaal** | Mode2 (optioneel) | `Garage` |
| **2 laadpalen** | Mode2 + Mode3 (optioneel) | `Garage`, `Voordeur` |
| **3+ laadpalen** | Mode2 + Mode3 + Mode4 | Mode4: `Carport, Werf` |

| Veld | Wat invullen | Voorbeeld |
|------|--------------|-----------|
| Naam laadpaal 1 (Mode2) | Eigen naam eerste lader | `Garage` |
| Naam laadpaal 2 (Mode3) | Eigen naam tweede lader | `Voordeur` |
| Extra laadpaalnamen (Mode4) | Komma-gescheiden, vanaf lader 3 | `Carport, Werf` |

Laat leeg om de naam uit de Easee-app te gebruiken. De **hardwarenaam** in Domoticz (bijv. `Easee`) is het prefix op alle tegels.

### Geen Equalizer

De plugin werkt volledig zonder Equalizer. Er verschijnen dan geen meterkast-tegels; Status toont `Geen EQ`. Load balancing en fuse-limieten zijn niet zichtbaar in Domoticz.

### Geen Tibber / andere prijsbron (v1)

Op branch **`v1`**: kies **Prijsbron (Mode9)** — **Geen** (alleen kWh), **Handmatig**, **Tibber**, **ENTSO-E** of **EnergyZero**. Zie [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

Op **legacy v10** (`main`): alleen Tibber voor kosten. Zonder Tibber-token werken laadpalen en Equalizer normaal; je mist **Dag overzicht**, **Beste laden** en sessie/dag-€ op laadpaal-**Status**.

### Tibber (Prijsbron Tibber of legacy v10)

| Veld | Wat invullen |
|------|--------------|
| Tibber Personal Access Token (Mode7) | Token van [developer.tibber.com](https://developer.tibber.com/settings/access-token) — **vereist bij Prijsbron Tibber** (v1) of legacy v10 |

Bij start zie je in het log: `Tibber actief — kosten na eerste poll` of `Tibber uit (Mode7 leeg)`.

### Optioneel — Equalizer

| Veld | Wat invullen | Voorbeeld |
|------|--------------|-----------|
| Naam Equalizer (Address) | Weergavenaam | `Meterkast` |
| Equalizer ID (IP) | Handmatig ID bij detectieproblemen | `EQ-...` |

### Logniveaus (Mode6)

| Mode6 | Wat je ziet |
|-------|-------------|
| **Normal** (standaard) | Startup, prijsbron/Tibber-status, `image_ids: 13/13`, migratie, WARNING/ERROR |
| **Debug** | Extra: `Poll voltooid`, kosten-tegel updates, siteStructure, per-tegel iconen |

Zet Debug alleen aan bij problemen — het log wordt dan veel langer.

---

## Upgrade van bestaande installatie

### Via git (aanbevolen)

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch origin
git checkout v1              # v1 ontwikkeling
# of: git checkout v10.11.6-stable   # legacy productie
git pull
sudo systemctl restart domoticz
```

Sinds v10.6.0 haalt `git pull` alle `.py`-modules op — niet alleen `plugin.py`. Op v1 komt ook de map `pricing/` mee. State migreert automatisch naar `easee_state.json`.

### Specifiek: v1 (0.2.0 – 0.6.1)

- Checkout branch **`v1`** — pluginnaam **Easee Domoticz plugin v1 (0.6.1)**
- **Prijsbron (Mode9):** Geen, Handmatig, Tibber, ENTSO-E, EnergyZero
- **ENTSO-E:** e-mail naar **transparency@entsoe.eu** (onderwerp *Restful API access*), wacht ~3 werkdagen, daarna Mode24 token
- **EnergyZero:** geen token — kies Prijsbron EnergyZero
- **0.6.1:** Status-tegel toont actieve prijsbron
- Zie [CHANGELOG.md](CHANGELOG.md) en [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

Custom iconen uit `Easee_icons_v2.zip` worden bij start automatisch geladen en op bestaande devices toegepast.

### Handmatig (zip of losse bestanden)

1. Stop het hardware-item in Domoticz (**Setup → Hardware** → disablen)
2. Vervang **alle `.py`-modules** en `Easee_icons_v2.zip` op de server (sinds v10.6.0 niet alleen `plugin.py`; op v1 ook map `pricing/`)
3. Start het hardware-item weer

> State-bestand (`easee_state.json`; legacy `easee_v9_0_state.json` wordt automatisch hernoemd) en bestaande devices blijven behouden bij upgrade.

### Specifiek: v10.6.0+

- `git pull` haalt alle 13 `.py`-bestanden op; herstart hardware-item of Domoticz.
- State migreert automatisch naar `easee_state.json` (atomisch opslaan sinds v10.6.1).
- Upload **`Easee_icons_v2.zip` opnieuw** als badges/iconen niet veranderen (Domoticz cached iconen).

### Specifiek: v10.11.x (legacy stable — v10.11.6-stable)

- **v10.11.0** — Compacte UI: **11 tegels** (2 laders + EQ + Tibber). *Kosten & Samenvatting* + *Dagrapport* → **Dag overzicht**; *Totaal & Sessie* → **Laden**; *Kosten (Sessie/Dag)* → **Status**. Oude tegels verborgen (`Used=0`).
- **v10.11.1** — Fix deprecated-tegel `Used=0`-update; stable promotion.
- **v10.11.2** — Status-timer pauze-fix; stable promotion.
- **v10.11.4** — truthy()-fix in laad-timer; stable tag `v10.11.4-stable`.
- **v10.11.6** — Dag overzicht-migratie fix (`Device.Update(Name=…)` i.p.v. readonly direct assignment); idle timer **00:00**; stable promotion.
- **v10.11.5** — Dag overzicht-migratie (legacy tegel hernoemen); idle timer **00:00** (readonly-fout op nieuwere Domoticz).
- **Stable tag** — `v10.11.6-stable` is de aanbevolen baseline; zie [STABLE.md](STABLE.md). Vorige stable tags blijven voor rollback.

```bash
git fetch --tags origin
git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

### Specifiek: v10.10.x (vorige stable — v10.10.8-stable)

- **v10.10.0** — Tibber kwartierprijzen, Dagrapport-tegel, laadhints, configureerbaar Beste laden, **16 tegels** met Tibber (2 laders + EQ).
- **v10.10.1** — API-timeout crasht hardware-thread niet meer.
- **v10.10.2–v10.10.8** — Sessie-kWh, timer, kosten, EQ fase-weergave; Totaal & Sessie numerische Custom sValue; sessie-kWh cap op dagtotaal.
- **Stable tag** — `v10.10.8-stable` voor rollback; zie [STABLE.md](STABLE.md).

```bash
git fetch --tags origin
git checkout v10.10.8-stable
sudo systemctl restart domoticz
```

### Specifiek: v10.9.28–v10.9.32 (vorige stable testing line)

- **Kosten-tegels + Vandaag kWh** — fixes v10.9.19–v10.9.28 (legacy DeviceID lookup, dag-tracking, lifetime Counter, Tibber vereist in Mode7). Getest door Richard (19-06-2026).
- **v10.9.29** — logging opgeschoond: normaal log toont minder spam; zet **Debug logging (Mode6)** op *Debug* voor per-poll details.
- **v10.9.30** — Tibber-token backup in `easee_state.json` (token blijft bewaard na hardware-opslag/plugin-update).
- **`EaseeStatusGlobal` combo-icoon** — upload **`Easee_icons_v2.zip` opnieuw** als het combo-icoon niet verandert.
- Verder: sticky power + per-endpoint rate limit (v10.9.17); discovery-throttle, equalizer vóór laders (v10.9.11–v10.9.16).

### Specifiek: v10.9.18

- **`EaseeStatusGlobal` combo-icoon** — EQ-puck iets groter linksonder, laadpaal iets kleiner rechtsboven. Upload **`Easee_icons_v2.zip` opnieuw** als het combo-icoon niet verandert.

### Specifiek: v10.9.17

- **Equalizer Vermogen sticky power** — laatste geldige import/export blijft op tegel bij mislukte poll; charger-429 blokkeert equalizer niet meer.
- **429 rate limit** — bij herhaalde `HTTP 429`-waarschuwingen in het log: zet **Poll interval (Mode1)** op **60 seconden**.

### Specifiek: v10.9.10 – v10.9.16

- **Status-iconen gesplitst** — combo-icoon (laadpaal + EQ-puck + **i**) alleen op globale *Easee - Status*; laadpaal Status (Garage, Voordeur) = laadpaal-only met **i**.
- **13 icon sets** — upload **`Easee_icons_v2.zip` opnieuw** via Aangepaste pictogrammen; controleer log op `image_ids: 13/13 sets`.
- **Equalizer: 2 tegels** — Status + Vermogen (sinds v10.9.1).

### Specifiek: v10.9.3 – v10.9.9

- Icon-loading fixes (zip-pad, plugin-key-prefix, `Device.Update`-parameters).
- v10.9.8: laadpaal Status kreeg weer `EaseeStatus`, Equalizer Vermogen `EaseeEqualizer`.
- Verwijder oude Easee custom icons vóór her-upload als iconen ontbreken.

### Oudere versies (v10.8.0 en eerder)

- v10.8.0 had **6** Equalizer-tegels — upgrade naar v10.9.1+ voor **2** tegels (Status + Vermogen).
- Wees-tegels uit oude versies (*Import*, *Spanning*, *Load balancing*, …) handmatig verwijderen.

### Specifiek: v10.7.x

- **v10.7.0** — code cleanup: ~150 passthrough-wrappers verwijderd; kleinere `plugin.py`; geen functionele wijzigingen.
- **v10.7.1** — fix: onHeartbeat crash door `power_emoji`/`status_emoji` naam-shadowing in `poll_charger`.
- **v10.7.2** — fix: onHeartbeat crash door verwijderde fuse/limit callbacks in `equalizer_logic`.
- Upgrade: `git pull`, herstart hardware-item. State en devices blijven behouden.

### Specifiek: v10.4.0 → v10.5.0

Geen schone installatie nodig. Vervang `plugin.py` of doe `git pull`, herstart. Nieuwe laadpalen worden automatisch gedetecteerd. Mode4 is nu het veld voor extra laadpaalnamen (vanaf lader 3) — als je daar nog `Easee` stond (oud, ongebruikt veld), mag dat leeg.

### Specifiek: v10.3.4 → v10.4.0

Geen schone installatie nodig. Vervang `plugin.py`, herstart. Als een kosten-tile nog `0 €` toont: verwijder die tile in Domoticz en herstart het plugin.

---

## Updates in de toekomst

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

Custom iconen uit `Easee_icons_v2.zip` worden bij start automatisch geladen en op bestaande devices toegepast.

Controleer [CHANGELOG.md](CHANGELOG.md) voor wijzigingen per versie.

---

## Eigen screenshot toevoegen (fork)

De README gebruikt **gesanitiseerde demo-mockups** in `docs/` (geen live kWh/vermogen). Wil je in je eigen fork een echte screenshot tonen?

1. Maak in Domoticz een screenshot van je dashboard (browser of OS-screenshot).
2. Sla op als `docs/screenshot-dashboard.png` (overschrijf de mockup) of een nieuwe naam.
3. Pas de afbeelding in [README.md](README.md) aan als je een andere bestandsnaam gebruikt.
4. Commit en push naar je fork.

Gebruik geen nep-screenshots — alleen echte captures van jouw installatie.

---

## Custom iconen handmatig uploaden

De plugin laadt `Easee_icons_v2.zip` automatisch uit de pluginmap. Sommige Domoticz-installaties accepteren die zip alleen via de webinterface. Upload is **eenmalig per Domoticz-installatie** — iconen blijven in de Domoticz-database bewaard.

### Wanneer nodig?

- Logmelding: *zip gevonden maar laden mislukt* of `image_ids: 0/13`
- Tegels tonen standaard Domoticz-iconen i.p.v. Easee-tegels
- Na upgrade waarbij icon sets zijn gewijzigd (bijv. v10.9.10 → `EaseeStatusGlobal`)

### Stappen

1. **Verwijder eerst** oude Easee custom icons (zelfde menu) — voorkomt conflicten met oude Base-namen
2. Open Domoticz in de browser
3. Ga naar **Setup** → **Instellingen** → **Meer opties** → **Aangepaste pictogrammen**
4. Klik **Upload** en kies `Easee_icons_v2.zip` uit de pluginmap:
   ```
   /home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons_v2.zip
   ```
5. Herstart het Easee hardware-item (of Domoticz)

Na een succesvolle upload herkent de plugin de iconen als *Custom icons uit Domoticz (handmatig geüpload)* in het log. Verwacht: `Custom icons geladen: 13 sets` of `image_ids: 13/13 sets`.

> **Energy-tegels** (*Laden*, *Totaal Laden*) kunnen in sommige Domoticz-versies toch het standaard bliksem-icoon tonen — bekende beperking.

---

## Probleemoplossing

### Git-authenticatie faalt

| Symptoom | Oplossing |
|----------|-----------|
| Password not supported | Gebruik PAT of SSH — zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md) |
| Permission denied (publickey) | SSH-sleutel toevoegen aan GitHub |
| Repository not found | Controleer repo-URL, SSH-sleutel of PAT (zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md)) |

### Plugin verschijnt niet in hardwarelijst

1. Controleer pad: `ls /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py`
2. Herstart Domoticz: `sudo systemctl restart domoticz`
3. Bekijk log: `sudo journalctl -u domoticz -f`

### "Python module 'requests' ontbreekt"

```bash
sudo apt install -y python3-requests
sudo systemctl restart domoticz
```

### Login mislukt

- Controleer Easee-gebruikersnaam en -wachtwoord
- Test of je kunt inloggen op de Easee-app
- Zet Debug logging aan voor meer details in het log

### Geen Equalizer gevonden

1. Zet **Debug logging** op *Debug*
2. Herstart het plugin en bekijk het log
3. Vul handmatig **Equalizer ID** in bij het IP-veld
4. Controleer of de Equalizer zichtbaar is in de Easee-app

### Devices dubbel na herstart

De plugin wacht bij opstarten tot Domoticz de Devices-lijst heeft geladen (minimaal 3 seconden, daarna readiness-check op bestaande Easee-devices of een stabiele device-count). Polling start pas na deze initiële sync. Als het toch gebeurt:

1. Stop het plugin
2. Verwijder dubbele devices handmatig in Domoticz
3. Start het plugin opnieuw

---

## Bestandslocaties op de server

| Bestand | Pad |
|---------|-----|
| Plugin | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py` |
| Custom iconen | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons_v2.zip` |
| State (runtime) | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/easee_state.json` |
| Domoticz-log | `sudo journalctl -u domoticz` |

---

## Meer hulp

- [README.md](README.md) — overzicht en snelle start
- [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — git-authenticatie (SSH / PAT)
- [CHANGELOG.md](CHANGELOG.md) — versiegeschiedenis
