# Installatie

De canonieke installatiehandleiding staat in **[INSTALL.md](../INSTALL.md)** (Nederlands, stap-voor-stap voor Debian/Domoticz).

## Snelle verwijzing

| Onderwerp | Document |
|-----------|----------|
| Installatie & upgrade | [INSTALL.md](../INSTALL.md) |
| Git-authenticatie (SSH/PAT) | [GIT_SETUP.md](GIT_SETUP.md) |
| Configuratie | [CONFIGURATION.md](CONFIGURATION.md) |
| Probleemoplossing | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

### Plugin type in Domoticz

Selecteer bij **Setup → Hardware → Python plugins**:

**Easee Domoticz plugin v10.11.1**

### Updates (stable)

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.1-stable
sudo systemctl restart domoticz
```

Zie [INSTALL.md — Upgrade](../INSTALL.md#upgrade-van-bestaande-installatie) en [STABLE.md](../STABLE.md) voor details.
