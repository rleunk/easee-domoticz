# Installatiehandleiding — Easee Domoticz plugin v10.5.9

Stap-voor-stap instructies voor installatie op een **Domoticz-server** (Debian Linux).

---

## Overzicht

| Item | Waarde |
|------|--------|
| Plugin | Easee Domoticz plugin v10.5.9 |
| Plugin-key | `EaseeCloudAutoDiscoveryV1000` |
| Doelmap op server | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/` |
| Hoofdbestand | `plugin.py` |
| Custom iconen | `Easee_icons.zip` (automatisch geladen bij pluginstart; zie [handmatige upload](#custom-iconen-handmatig-uploaden) als dat mislukt) |
| GitHub-repo | https://github.com/rleunk/easee-domoticz (privé) |

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
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons.zip
```

Je moet beide bestanden zien met een recente datum. De icon-zip wordt bij pluginstart automatisch geladen; bestaande tegels krijgen de Easee-iconen na een herstart van het hardware-item (of Domoticz). Als automatisch laden mislukt, upload de zip eenmalig handmatig — zie [Custom iconen handmatig uploaden](#custom-iconen-handmatig-uploaden).

### Stap 4: Domoticz herstarten

```bash
sudo systemctl restart domoticz
```

### Stap 5: Plugin activeren in Domoticz

1. Open Domoticz in je browser
2. Ga naar **Setup → Hardware**
3. Voeg een nieuw hardware-item toe: **Python plugins**
4. Selecteer **Easee Domoticz plugin v10.5.9**
5. Vul je Easee-gebruikersnaam en -wachtwoord in
6. Optioneel: vul Tibber-token, laadpaalnamen en Equalizer-naam in
7. Klik **Add**

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

Download `easee-domoticz-github.zip` van GitHub (of maak hem lokaal op je PC).

### Stap 2: Uploaden naar de server

Via SCP, SFTP of WinSCP:

```
Lokaal:  plugin.py
Server:  /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
```

### Stap 3: Map aanmaken (indien nodig)

```bash
mkdir -p /home/root/domoticz/plugins/Easee-Domoticz-plugin
```

### Stap 4: Bestand plaatsen

Zorg dat de structuur **plat** is:

```
Easee-Domoticz-plugin/
└── plugin.py       ← direct hier, geen submap eronder
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

### Geen Tibber

Zonder Tibber-token werken laadpalen en Equalizer normaal. Je mist alleen de kosten- en tarief-tegels (**Kosten & Samenvatting**, **Beste laden**, per-lader **Kosten (Sessie/Dag)**).

### Optioneel — Equalizer

| Veld | Wat invullen | Voorbeeld |
|------|--------------|-----------|
| Naam Equalizer (Address) | Weergavenaam | `Meterkast` |
| Equalizer ID (IP) | Handmatig ID bij detectieproblemen | `EQ-...` |

### Optioneel — Tibber

| Veld | Wat invullen |
|------|--------------|
| Tibber Personal Access Token (Mode7) | Token van [developer.tibber.com](https://developer.tibber.com/settings/access-token) |

---

## Upgrade van bestaande installatie

### Via git (aanbevolen)

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

Custom iconen uit `Easee_icons.zip` worden bij start automatisch geladen en op bestaande devices toegepast.

### Handmatig (alleen plugin.py vervangen)

1. Stop het hardware-item in Domoticz (**Setup → Hardware** → disablen)
2. Vervang `plugin.py` op de server
3. Start het hardware-item weer

> State-bestand (`easee_v9_0_state.json`) en bestaande devices blijven behouden bij upgrade.

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

Custom iconen uit `Easee_icons.zip` worden bij start automatisch geladen en op bestaande devices toegepast.

Controleer [CHANGELOG.md](CHANGELOG.md) voor wijzigingen per versie.

---

## Custom iconen handmatig uploaden

De plugin laadt `Easee_icons.zip` automatisch uit de pluginmap. Sommige Domoticz-installaties accepteren die zip alleen via de webinterface. Upload is **eenmalig per Domoticz-installatie** — iconen blijven in de Domoticz-database bewaard.

### Wanneer nodig?

- Logmelding: *zip gevonden maar laden mislukt*
- Tegels tonen standaard Domoticz-iconen i.p.v. groene/oranje Easee-tegels

### Stappen

1. Open Domoticz in de browser
2. Ga naar **Setup** → **Instellingen** → **Meer opties** → **Aangepaste pictogrammen**
3. Klik **Upload** en kies `Easee_icons.zip` uit de pluginmap:
   ```
   /home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons.zip
   ```
4. Herstart het Easee hardware-item (of Domoticz)

Na een succesvolle upload herkent de plugin de iconen als *Custom icons uit Domoticz (handmatig geüpload)* in het log.

---

## Probleemoplossing

### Git-authenticatie faalt

| Symptoom | Oplossing |
|----------|-----------|
| Password not supported | Gebruik PAT of SSH — zie [docs/GIT_SETUP.md](docs/GIT_SETUP.md) |
| Permission denied (publickey) | SSH-sleutel toevoegen aan GitHub |
| Repository not found | Controleer toegang tot private repo |

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

De plugin heeft ingebouwde bescherming tegen dubbele devices. Als het toch gebeurt:

1. Stop het plugin
2. Verwijder dubbele devices handmatig in Domoticz
3. Start het plugin opnieuw

---

## Bestandslocaties op de server

| Bestand | Pad |
|---------|-----|
| Plugin | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py` |
| Custom iconen | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/Easee_icons.zip` |
| State (runtime) | `/home/root/domoticz/plugins/Easee-Domoticz-plugin/easee_v9_0_state.json` |
| Domoticz-log | `sudo journalctl -u domoticz` |

---

## Meer hulp

- [README.md](README.md) — overzicht en snelle start
- [docs/GIT_SETUP.md](docs/GIT_SETUP.md) — git-authenticatie (SSH / PAT)
- [CHANGELOG.md](CHANGELOG.md) — versiegeschiedenis
