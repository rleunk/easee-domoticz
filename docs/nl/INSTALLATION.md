# Installatie

**Language / Taal:** [English](../INSTALLATION.md) · **Nederlands** (this page)

De canonieke installatiehandleiding staat in **[INSTALL.nl.md](../../INSTALL.nl.md)** (Nederlands, stap-voor-stap voor Debian/Domoticz).

English: **[INSTALL.md](../../INSTALL.md)**

## Snelle verwijzing

| Onderwerp | Document |
|-----------|----------|
| Installatie & upgrade | [INSTALL.nl.md](../../INSTALL.nl.md) |
| Git-authenticatie (HTTPS/PAT, SSH optioneel) | [GIT_SETUP.md](GIT_SETUP.md) |
| Configuratie | [CONFIGURATION.md](CONFIGURATION.md) |
| Probleemoplossing | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 1.1.6 release | [RELEASE_1.1.6.md](RELEASE_1.1.6.md) |
| 1.1.5 release | [RELEASE_1.1.5.md](RELEASE_1.1.5.md) |
| 1.0.0 release | [RELEASE_1.0.0.md](RELEASE_1.0.0.md) |

### Plugin type in Domoticz

Selecteer bij **Setup → Hardware → Python plugins**:

| Lijn | Pluginnaam in Domoticz | Branch / tag |
|------|------------------------|--------------|
| **v1 productie** | **Easee Domoticz plugin v1 (1.1.6)** | `main` / `v1.1.6` |
| **Legacy v10** | **Easee Domoticz plugin v10.11.6** | `legacy/v10` / `v10.11.6-stable` |

### Updates v1 (productie)

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main
git pull origin main
sudo systemctl restart domoticz
```

### Updates legacy v10

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout legacy/v10
# of: git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

Zie [INSTALL.nl.md — Upgrade](../../INSTALL.nl.md#upgrade-van-bestaande-installatie) en [STABLE.nl.md](../../STABLE.nl.md) voor details.
