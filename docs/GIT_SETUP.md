# Git-authenticatie op de Domoticz-server (Debian)

GitHub accepteert sinds augustus 2021 **geen wachtwoord meer** bij HTTPS-clones. Als je een foutmelding krijgt zoals *"Password authentication is not supported"*, gebruik dan een Personal Access Token (PAT) — niet je GitHub-wachtwoord.

> **Standaard:** clone via **HTTPS**. Werkt direct voor publieke repos; bij een inlogprompt gebruik je een PAT (zie hieronder).

---

## Standaard — HTTPS clone

```bash
cd /home/USER/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout v1
```

> De mapnaam `Easee-Domoticz-plugin` is belangrijk: Domoticz verwacht `plugin.py` direct in die map.

### Updates ophalen

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

---

## HTTPS met Personal Access Token (PAT)

Gebruik dit wanneer Git om inloggegevens vraagt (private fork, of GitHub vraagt om authenticatie).

### Stap 1: PAT aanmaken op GitHub

1. Ga naar [GitHub → Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Klik **Generate new token** (classic)
3. Geef een naam, bijv. `domoticz-server`
4. Vink **repo** aan (voor clone/pull via HTTPS)
5. Genereer en **kopieer het token** — je ziet het maar één keer!

> Bewaar het token veilig. Deel het nooit in chat, e-mail of documentatie.

### Stap 2: Clonen met PAT

```bash
cd /home/USER/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout v1
```

Wanneer Git om inloggegevens vraagt:

| Veld | Waarde |
|------|--------|
| Username | `rleunk` |
| Password | je **PAT** (niet je GitHub-wachtwoord) |

### Stap 3: Credentials opslaan (optioneel)

Zodat je niet bij elke `git pull` opnieuw het token hoeft in te voeren:

```bash
git config --global credential.helper store
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git pull
# Voer eenmalig username + PAT in; daarna wordt het opgeslagen in ~/.git-credentials
```

> **Let op:** het token staat dan als platte tekst op de server. SSH (hieronder) is veiliger voor een vaste server.

---

## Optioneel: SSH (als je GitHub SSH-sleutels hebt geconfigureerd)

Eenmalig instellen; daarna werken `git clone` en `git pull` zonder wachtwoord of PAT. Alleen nodig als je SSH liever gebruikt dan HTTPS.

### Stap 1: SSH-sleutel aanmaken op de server

Log in op je Domoticz-server en voer uit:

```bash
ssh-keygen -t ed25519 -C "domoticz-easee-plugin" -f ~/.ssh/id_ed25519_github -N ""
```

Dit maakt een sleutelpaar aan zonder wachtwoord (geschikt voor een thuisserver).

### Stap 2: Publieke sleutel tonen

```bash
cat ~/.ssh/id_ed25519_github.pub
```

Kopieer de volledige regel (begint met `ssh-ed25519 ...`).

### Stap 3: Sleutel toevoegen aan GitHub

1. Ga naar [GitHub → Settings → SSH and GPG keys](https://github.com/settings/keys)
2. Klik **New SSH key**
3. Titel: bijv. `Domoticz server`
4. Plak de publieke sleutel
5. Klik **Add SSH key**

### Stap 4: SSH-configureren (optioneel maar handig)

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
```

### Stap 5: Verbinding testen

```bash
ssh -T git@github.com
```

Verwachte melding: *"Hi rleunk! You've successfully authenticated..."*

### Stap 6: Repository clonen via SSH

```bash
cd /home/USER/domoticz/plugins
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout v1
```

### Updates ophalen (SSH)

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

> Het installatiescript `install.sh` gebruikt standaard HTTPS. Geef `--ssh` mee als je SSH hebt ingesteld.

---

## Veelvoorkomende fouten

| Foutmelding | Oorzaak | Oplossing |
|-------------|---------|-----------|
| `Password authentication is not supported` | HTTPS met GitHub-wachtwoord | Gebruik PAT (HTTPS) of SSH (optioneel) |
| `Permission denied (publickey)` | SSH-sleutel niet op GitHub | Voeg publieke sleutel toe (SSH, stap 3) |
| `Repository not found` | Verkeerde URL of geen toegang | Controleer repo-URL; bij HTTPS: PAT met `repo`-scope; bij SSH: sleutel op GitHub |
| `fatal: not a git repository` | Verkeerde map | `cd` naar `/home/USER/domoticz/plugins/Easee-Domoticz-plugin` |

---

## Mapstructuur na clone

```
/home/USER/domoticz/plugins/Easee-Domoticz-plugin/
├── plugin.py              ← Domoticz entrypoint
├── easee_constants.py
├── easee_logging.py
├── easee_api.py
├── easee_api_keys.py
├── easee_state.py
├── easee_helpers.py
├── domoticz_runtime.py
├── domoticz_devices.py
├── domoticz_icons.py
├── domoticz_energy_hints.py   ← v0.4.0+ (P1/zon/thuisbatterij hints)
├── charger_logic.py
├── equalizer_logic.py
├── tibber_pricing.py
├── pricing/                   ← v0.2.0+ (prijsbronnen)
│   ├── __init__.py
│   ├── base.py
│   ├── none.py
│   ├── manual.py
│   ├── tibber.py
│   ├── entsoe.py
│   ├── energyzero.py
│   ├── factory.py
│   └── ui.py
├── Easee_icons_v2.zip     ← custom iconen (automatisch geladen)
├── easee_state.json       ← runtime state (aangemaakt bij eerste run)
├── README.md
├── INSTALL.md
├── install.sh
└── docs/
```

Domoticz laadt `plugin.py`; alle **14 root `.py`-bestanden** plus map **`pricing/`** (9 bestanden) zijn verplicht op branch `v1`. Legacy v10 op `main` heeft geen `pricing/` of `domoticz_energy_hints.py`. Overige bestanden zijn documentatie en hulpscripts.
