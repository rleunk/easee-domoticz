# Installatie

De canonieke installatiehandleiding staat in **[INSTALL.md](../INSTALL.md)** (Nederlands, stap-voor-stap voor Debian/Domoticz).

## Snelle verwijzing

| Onderwerp | Document |
|-----------|----------|
| Installatie & upgrade | [INSTALL.md](../INSTALL.md) |
| Git-authenticatie (HTTPS/PAT, SSH optioneel) | [GIT_SETUP.md](GIT_SETUP.md) |
| Configuratie | [CONFIGURATION.md](CONFIGURATION.md) |
| Probleemoplossing | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 1.0.0 release | [RELEASE_1.0.0.md](RELEASE_1.0.0.md) |

### Plugin type in Domoticz

Selecteer bij **Setup → Hardware → Python plugins**:

| Lijn | Pluginnaam in Domoticz | Branch / tag |
|------|------------------------|--------------|
| **v1 productie** | **Easee Domoticz plugin v1 (1.0.0)** | `main` / `v1.0.0` |
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

Zie [INSTALL.md — Upgrade](../INSTALL.md#upgrade-van-bestaande-installatie) en [STABLE.md](../STABLE.md) voor details.
