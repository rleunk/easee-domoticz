# Stable releases

**Language:** **English** · [Nederlands](STABLE.nl.md)

Two version lines: **v1** (production on `main`) and legacy **v10** (`legacy/v10`). See [VERSIONING.md](VERSIONING.md).

## v1 — production (`main`)

Semver tags without `-stable` suffix (e.g. **`v1.1.7`**).

| Tag | Branch | Status |
|-----|--------|--------|
| **`v1.1.7`** | `main` | **Recommended** — Easee charger observations API (Sep 2026 hotfix) |
| **`v1.1.6`** | `main` | Rollback — English UI; charger `/state` broken after Easee cutoff |
| **`v1.1.5`** | `main` | Rollback (Jul 2026, soak Aug 2026) |
| **`v1.0.0`** | `main` | Rollback (Jun 2026) |

### Install

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main   # or: git checkout v1.1.7
sudo systemctl restart domoticz
```

Domoticz: **Easee Domoticz plugin v1 (1.1.7)**.

### Upgrade

```bash
git fetch --tags origin && git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart the Easee hardware item after every upgrade.

## Legacy v10

Frozen at **v10.11.6** on branch **`legacy/v10`**.

```bash
git checkout legacy/v10   # or v10.11.6-stable
```

## Releases

- [**v1.1.7**](https://github.com/rleunk/easee-domoticz/releases/tag/v1.1.7) — current production
- [**v1.1.6**](https://github.com/rleunk/easee-domoticz/releases/tag/v1.1.6) — rollback
- [**v1.1.5**](https://github.com/rleunk/easee-domoticz/releases/tag/v1.1.5) — rollback
- [**v10.11.6**](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6) — legacy

See [CHANGELOG.md](CHANGELOG.md) for details.
