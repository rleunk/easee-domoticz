# Easee AutoDiscovery Compact voor Domoticz

[![Version](https://img.shields.io/badge/version-10.4.0-blue)](CHANGELOG.md)
[![Domoticz](https://img.shields.io/badge/Domoticz-Python%20plugin-green)](https://www.domoticz.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Domoticz Python-plugin voor **Easee-laadpalen** met automatische detectie, compacte weergave, **Tibber**-stroomtarieven en **Equalizer** (meterkast) ondersteuning.

| | |
|---|---|
| **Plugin-key** | `EaseeCloudAutoDiscoveryV1000` |
| **Versie** | 10.4.0 |
| **Auteur** | Richard Leunk |
| **Serverpad** | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/` |

---

## Wat doet deze plugin?

De plugin verbindt Domoticz met je Easee-account en maakt automatisch devices aan voor:

- **Laadpalen** — status, vermogen, sessie-info, kWh en kosten per lader
- **Equalizer / meterkast** — online-status, load balancing, hoofdzekering en eMobility-limieten
- **Tibber (optioneel)** — actueel stroomtarief, goedkoopste laadvenster en kostenoverzicht

Kern-tiles in Domoticz:

| Tile | Functie |
|------|---------|
| Status | Online/offline, Equalizer-aantal, load balancing, Tibber-status |
| Totaal Laden | Gecombineerd laadvermogen (W) |
| Totaal kWh | Gecombineerde energie |
| LoadBal | Schakelaar: load balancing actief |
| Kosten & Samenvatting | Dagkosten, actueel tarief, energie/belasting |
| Beste laden | Goedkoopste Tibber-venster (3 uur) |

Per laadpaal worden o.a. status-, vermogen-, kWh- en kosten-tiles aangemaakt. Emoji-indicatoren maken de status in één oogopslag leesbaar.

---

## Vereisten

| Vereiste | Details |
|----------|---------|
| Domoticz | Met Python 3-ondersteuning |
| Python-pakket | `python3-requests` (zelfde Python-omgeving als Domoticz) |
| Easee-account | Gebruikersnaam (e-mail/telefoon) + wachtwoord |
| Tibber (optioneel) | Personal Access Token via [developer.tibber.com](https://developer.tibber.com/settings/access-token) |
| Git (aanbevolen) | Voor eenvoudige updates via `git pull` op de server |

---

## Snelle installatie (aanbevolen: git)

Op je Domoticz-server (Debian):

```bash
cd /home/root/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
sudo systemctl restart domoticz
```

Daarna in Domoticz: **Setup → Hardware → Python plugins** → voeg **Easee AutoDiscovery Compact v10.4.0** toe.

> **Git-authenticatie nodig?** Zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md) voor SSH (aanbevolen) of HTTPS met Personal Access Token.

### Alternatief: installatiescript

```bash
curl -fsSL https://raw.githubusercontent.com/rleunk/easee-domoticz/main/install.sh -o /tmp/install-easee.sh
chmod +x /tmp/install-easee.sh
sudo /tmp/install-easee.sh
```

Of kopieer `install.sh` naar de server en voer het lokaal uit.

### Alternatief: handmatig (zip)

1. Download de release-zip of clone deze repo op je PC
2. Kopieer **alleen** `plugin.py` naar `/home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py`
3. Herstart Domoticz

> Let op: bij zip-deploy moet `plugin.py` direct in de map `Easee-Domoticz-plugin/` staan — **niet** in een submap.

Uitgebreide stap-voor-stap instructies: **[INSTALL.md](INSTALL.md)**

---

## Configuratie in Domoticz

Na het toevoegen van het hardware-item:

| Veld | Beschrijving |
|------|--------------|
| **Username / Password** | Easee-inloggegevens |
| **Poll interval (Mode1)** | Seconden tussen updates (standaard 30) |
| **Debug logging (Mode6)** | Zet op *Debug* bij problemen |
| **Naam laadpaal 1 (Mode2)** | Optionele aangepaste naam voor eerste lader |
| **Naam laadpaal 2 (Mode3)** | Optionele aangepaste naam voor tweede lader |
| **Naam Equalizer (Address)** | Optionele weergavenaam voor je Equalizer |
| **Equalizer ID (IP)** | Handmatig ID als auto-detectie faalt |
| **Tibber token (Mode7)** | Optioneel — voor tarieven en kosten |

### Tips

- **Laadpaalnamen:** vul Mode2/Mode3 in als je hardware-namen wilt overschrijven (bijv. `Garage`, `Voordeur`).
- **Equalizer:** laat **Address** leeg voor automatische detectie; vul een naam in voor een eigen label.
- **Tibber:** zonder token werken laadpalen en Equalizer wel, maar zonder kosten/tarief-tiles.

---

## Updates

Met git op de server:

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

Bij upgrade van v10.3.4 → v10.4.0: state (`easee_v9_0_state.json`) en bestaande devices blijven behouden.

Wijzigingen per versie: **[CHANGELOG.md](CHANGELOG.md)**

---

## Probleemoplossing

### Git: "Password authentication is not supported"

GitHub accepteert geen accountwachtwoord meer bij HTTPS. Oplossingen:

- **SSH** (aanbevolen): zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — Optie A
- **HTTPS + PAT**: zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — Optie B

### Plugin laadt niet / geen devices

1. Controleer of `plugin.py` staat in `/home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py`
2. Installeer `python3-requests`: `sudo apt install python3-requests`
3. Zet **Debug logging** aan en bekijk het Domoticz-log
4. Controleer Easee-inloggegevens in Setup → Hardware

### Zip-structuur fout

Fout:
```
/home/root/domoticz/plugins/Easee-Domoticz-plugin/easee-domoticz/plugin.py  ❌
```

Goed:
```
/home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py  ✅
```

### Kosten-tile toont "0 €"

Verwijder de betreffende **Kosten (Sessie/Dag)**-tile in Domoticz, herstart het plugin — het device wordt opnieuw aangemaakt. Zie [CHANGELOG.md](CHANGELOG.md) v10.4.0.

### Equalizer niet gevonden

1. Zet Debug logging aan
2. Vul handmatig het Equalizer ID in bij **IP**
3. Controleer of je Equalizer gekoppeld is aan je Easee-site

---

## Versiegeschiedenis (samenvatting)

| Versie | Hoogtepunten |
|--------|--------------|
| **10.4.0** | Actueel Tibber-tarief in kostenoverzicht; sessie/dagkosten gefixt |
| **10.3.x** | Stabiliteit kostenberekening en Equalizer-weergave |
| **10.2.0** | Equalizer discovery (stap 1), load balancing, hoofdzekering |
| **10.1.0** | Eerste compacte release: auto-discovery, Tibber, emoji-UI |

Volledige changelog: **[CHANGELOG.md](CHANGELOG.md)**

---

## Documentatie

| Bestand | Inhoud |
|---------|--------|
| [INSTALL.md](INSTALL.md) | Uitgebreide installatiehandleiding (Debian/Domoticz) |
| [docs/GIT_SETUP.md](docs/GIT_SETUP.md) | SSH- en PAT-instellingen voor git op de server |
| [CHANGELOG.md](CHANGELOG.md) | Versiegeschiedenis |
| [install.sh](install.sh) | Automatisch clone/pull + herstart Domoticz |

---

## AI-bijdrage aan ontwikkeling

Deze plugin is in meerdere stappen ontwikkeld met behulp van AI-tools, onder begeleiding en review van de auteur:

| Fase | Tool | Rol |
|------|------|-----|
| Eerste opzet & basisontwikkeling | **GitHub Copilot** | Initiële structuur, API-integratie en device-logica |
| Verdere ontwikkeling | **GitHub Copilot** | Uitbreidingen, bugfixes en feature-iteraties |
| Verfijning & documentatie | **Cursor** | Code-review, stabilisatie en repository-documentatie |

Alle functionele keuzes, configuratie en productie-inzet worden door Richard Leunk beheerd. AI-tools fungeerden als ontwikkelassistent — niet als autonome auteur.

---

## Licentie

MIT License — zie [LICENSE](LICENSE).

## Links

- [Easee Developer API](https://developer.easee.com/docs/integrations)
- [Domoticz Python Plugin Wiki](https://wiki.domoticz.com/Developing_a_Python_plugin)
- [Tibber Access Token](https://developer.tibber.com/settings/access-token)
