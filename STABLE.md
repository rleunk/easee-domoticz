# Stable releases

Dit project heeft **twee versielijnen**: legacy **v10** (productie op `main`) en **v1** (ontwikkeling op branch `v1`). Zie [VERSIONING.md](VERSIONING.md).

## Legacy v10 — productie (main)

Legacy v10 gebruikt **annotated git-tags** met suffix `-stable` voor aanbevolen productie-baselines.

### Huidige stable v10

| Tag | Commit | Status |
|-----|--------|--------|
| **`v10.11.6-stable`** | zelfde als `v10.11.6` | **Aanbevolen productie** — Dag overzicht-migratie fix; idle timer **00:00**; compacte UI (**11 tegels**) |
| `v10.11.5-stable` | zelfde als `v10.11.5` | **Bewaard** — rollback-baseline |
| `v10.11.4-stable` | zelfde als `v10.11.4` | **Bewaard** — rollback-baseline |
| `v10.11.2-stable` | zelfde als `v10.11.2` | **Bewaard** — rollback-baseline |
| `v10.10.8-stable` | zelfde als `v10.10.8` | **Bewaard** — rollback (16-tegel layout) |

### Installeren legacy stable

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

Of blijf op `main` volgen (`git pull`) — `main` wijst naar v10.11.6-stable.

**Na elke upgrade:** herstart het Easee hardware-item in Domoticz (**Setup → Hardware**).

## v1 — ontwikkeling (branch `v1`)

| Item | Status |
|------|--------|
| **0.1.0** | Scaffold — **niet stable**; gedrag gelijk aan v10.11.6 bij Tibber + token |
| **1.0.0** | Gepland eerste publieke stable v1 |

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch origin
git checkout v1
sudo systemctl restart domoticz
```

Pre-release tag: `v0.1.0` (optioneel op GitHub).

## Rollback v10

### Naar v10.11.5

```bash
git fetch --tags origin
git checkout v10.11.5-stable
sudo systemctl restart domoticz
```

### Naar v10.10.8 (16 tegels)

```bash
git fetch --tags origin
git checkout v10.10.8-stable
sudo systemctl restart domoticz
```

## Releases

- [v0.1.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.1.0) — v1 scaffold (pre-release)
- [v10.11.6](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6) — legacy stable (aanbevolen productie)
- [v10.11.5](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.5) — rollback
- [v10.10.8](https://github.com/rleunk/easee-domoticz/releases/tag/v10.10.8) — rollback (16 tegels)

Zie [CHANGELOG.md](CHANGELOG.md) en [README.md](README.md) voor details per versie.
