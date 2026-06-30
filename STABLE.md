# Stable releases

Dit project heeft **twee versielijnen**: **v1** (productie op `main`) en legacy **v10** (bewaard op branch `legacy/v10`). Zie [VERSIONING.md](VERSIONING.md).

## v1 — productie (main)

v1 gebruikt **semver-tags** zonder `-stable` suffix (bijv. **`v1.0.0`**).

### Huidige stable v1

| Tag | Branch | Status |
|-----|--------|--------|
| **`v1.0.0`** | `main` | **Aanbevolen productie** — vijf prijsbronnen, energy hints, 11 tegels + LoadBal |

### Installeren v1 (productie)

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main
# of: git checkout v1.0.0
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v1 (1.0.0)**.

**Na elke upgrade:** herstart het Easee hardware-item in Domoticz (**Setup → Hardware**).

### Upgrade naar nieuwste v1

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main
git pull origin main
sudo systemctl restart domoticz
```

## v1 — ontwikkeling (branch `v1`)

Branch **`v1`** blijft beschikbaar voor toekomstige v1-ontwikkeling (1.1.x). Na release **1.0.0** staan `main` en `v1` op dezelfde commit; nieuwe features komen eerst op `v1`.

| Versie | Status | Inhoud (kort) |
|--------|--------|---------------|
| **1.0.0** | **Released** | Eerste stable v1 — alle prijsbronnen, hints, 11 tegels |
| **0.6.1** | Pre-release | Status-tegel toont actieve prijsbron |
| **0.6.0** | Pre-release | Prijsbron **EnergyZero** |
| **0.5.0** | Pre-release | Prijsbron **ENTSO-E** |
| **0.4.1** | Pre-release | Thuisbatterij-labels generiek |
| **0.4.0** | Pre-release | Handmatig Dal/piek; P1/zon/thuisbatterij hints |
| **0.3.0** | Pre-release | Handmatig Dag/nacht; Energieprijs UI-reorder |
| **0.2.1** | Pre-release | BesteLadenHours fix |
| **0.2.0** | Pre-release | Prijsbron Geen/Handmatig/Tibber; `pricing/` end-to-end |
| **0.1.0** | Pre-release | Scaffold; Tibber-only runtime gelijk aan v10.11.6 |

Pre-release tags: `v0.1.0` t/m `v0.6.1`. Zie [CHANGELOG.md](CHANGELOG.md).

## Legacy v10 — bewaard (branch `legacy/v10`)

Legacy v10 is **bevroren** op v10.11.6. Branch **`legacy/v10`** en tags **`v10.11.6`** / **`v10.11.6-stable`** blijven beschikbaar voor bestaande installaties en rollback.

| Tag | Status |
|-----|--------|
| **`v10.11.6`** / **`v10.11.6-stable`** | Legacy productie-baseline — Tibber-only, 11 tegels |
| `v10.11.5-stable` | Rollback-baseline |
| `v10.11.4-stable` | Rollback-baseline |
| `v10.10.8-stable` | Rollback (16-tegel layout) |

### Checkout legacy v10

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout legacy/v10
# of: git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

In Domoticz: **Easee Domoticz plugin v10.11.6**.

### Rollback v10

#### Naar v10.11.5

```bash
git fetch --tags origin
git checkout v10.11.5-stable
sudo systemctl restart domoticz
```

#### Naar v10.10.8 (16 tegels)

```bash
git fetch --tags origin
git checkout v10.10.8-stable
sudo systemctl restart domoticz
```

## Releases

### v1 (productie)

- [**v1.0.0**](https://github.com/rleunk/easee-domoticz/releases/tag/v1.0.0) — Eerste stable v1 (main)

### v1 (pre-release)

- [v0.6.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.6.1) — Status-tegel prijsbron
- [v0.6.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.6.0) — EnergyZero prijsbron
- [v0.5.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.5.0) — ENTSO-E prijsbron
- [v0.4.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.4.1) · [v0.4.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.4.0) · [v0.3.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.3.0) · [v0.2.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.2.1) · [v0.2.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.2.0) · [v0.1.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.1.0)

### Legacy v10

- [v10.11.6](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6) — legacy baseline (branch `legacy/v10`)
- [v10.11.5](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.5) — rollback
- [v10.10.8](https://github.com/rleunk/easee-domoticz/releases/tag/v10.10.8) — rollback (16 tegels)

Zie [CHANGELOG.md](CHANGELOG.md) en [README.md](README.md) voor details per versie.
