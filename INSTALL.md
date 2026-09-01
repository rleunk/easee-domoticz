# Installation guide — Easee Domoticz plugin

**Language:** **English** · [Nederlands](INSTALL.nl.md)

Step-by-step installation on a **Domoticz server** (Debian Linux).

> **Paths:** Replace `USER` with your Linux username (e.g. `root`, `pi`). Plugin folder: `/home/USER/domoticz/plugins/Easee-Domoticz-plugin/`.

> **Branches:** **`main`** = production **1.1.7** · **`v1`** = development · **`legacy/v10`** = v10.11.6. See [STABLE.md](STABLE.md).

---

## v1 production (`main`) — 1.1.7

| Item | Value |
|------|--------|
| Plugin | **Easee Domoticz plugin v1 (1.1.7)** |
| Branch | `main` or tag `v1.1.7` |
| Price sources | None, Manual, Tibber, ENTSO-E, EnergyZero |
| UI language | Dutch (default) or English (Mode30) |

### Quick install

```bash
cd /home/USER/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout main
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v1 (1.1.7)** → Easee credentials → **Add**.

Set **Price source (Mode9)**. See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

### Upgrade

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart the Easee hardware item. Log should show: `Plugin v1.1.6 gestart`.

### Requirements

```bash
sudo apt install -y python3-requests
```

Plugin path must contain `plugin.py` directly:

```
/home/USER/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
```

### Custom icons

1. Plugin auto-loads **`Easee_icons_v2.zip`** on startup
2. If log shows `image_ids: 0/13`: remove old Easee icons in Domoticz **Settings → Custom icons**
3. Upload `Easee_icons_v2.zip`, restart hardware item
4. Expect: `Custom icons loaded: 13 sets` and `image_ids: 13/13`

Some **Energy** tiles may still show Domoticz default lightning icon — known Domoticz limitation.

### English UI

After install: **Setup → Hardware → Easee → Taal / Language → English** (Mode30). Restart hardware item.

---

## Legacy v10 (`legacy/v10`)

For existing v10 installs only:

```bash
git fetch --tags origin
git checkout legacy/v10   # or v10.11.6-stable
sudo systemctl restart domoticz
```

Plugin name: **Easee Domoticz plugin v10.11.6**. Tibber-only pricing.

Full legacy install details: [INSTALL.nl.md](INSTALL.nl.md) (Dutch).

---

## Git authentication

GitHub requires a **Personal Access Token** for HTTPS, not your password. See [docs/GIT_SETUP.md](docs/GIT_SETUP.md).

---

## Troubleshooting

| Problem | See |
|---------|-----|
| Plugin not in list | Path + `python3-requests` |
| Login failed | Credentials; wait 5–10 min on rate limit |
| No devices | Check Easee app; clear Mode5 filter |
| HTTP 429 | Set Mode1 to **60 sec** — [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#http-429-rate-limit-easee-api) |
| No icons | Re-upload zip — above |

Full guide: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
