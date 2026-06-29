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

| Versie | Status | Inhoud (kort) |
|--------|--------|---------------|
| **0.6.1** | **Huidig pre-release** | Status-tegel toont actieve prijsbron (alle Mode9-waarden) |
| **0.6.0** | Pre-release | Prijsbron **EnergyZero** (geen token) |
| **0.5.0** | Pre-release | Prijsbron **ENTSO-E** (day-ahead spot + toeslagen) |
| **0.4.1** | Pre-release | Thuisbatterij-labels generiek |
| **0.4.0** | Pre-release | Handmatig Dal/piek; P1/zon/thuisbatterij hints |
| **0.3.0** | Pre-release | Handmatig Dag/nacht; Energieprijs UI-reorder |
| **0.2.1** | Pre-release | BesteLadenHours fix |
| **0.2.0** | Pre-release | Prijsbron Geen/Handmatig/Tibber; `pricing/` end-to-end |
| **0.1.0** | Pre-release | Scaffold; Tibber-only runtime gelijk aan v10.11.6-stable |
| **1.0.0** | Gepland | Eerste publieke stable v1 |

**Niet productie-stable** — gebruik voor testen en feedback. Prijsbronnen: Geen, Handmatig, Tibber, ENTSO-E, EnergyZero — **alle getest** op Richard-setup (ENTSO-E bevestigd 2026-06-29).

### Klaar voor 1.0.0-stable?

Volledige checklist, soak-testcriteria en tag-procedure: **[docs/RELEASE_1.0.0.md](docs/RELEASE_1.0.0.md)**.

| Gereed | Open |
|--------|------|
| ✅ Alle prijsbronnen werkend | ⏳ Soak test op productie-Domoticz |
| ✅ Docs gesynchroniseerd (0.6.1) | ⏳ Tag `1.0.0-stable` + GitHub release |
| ✅ Forumdraft ([FORUM_POST.md](docs/FORUM_POST.md)) | ⏳ Forum post bij go-live |

Code blijft **0.6.1** tot soak is afgerond en de tag wordt gezet — geen premature version bump.

### Installeren v1 (ontwikkeling)

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch origin
git checkout v1
sudo systemctl restart domoticz
```

In Domoticz: **Setup → Hardware → Python plugins** → **Easee Domoticz plugin v1 (0.6.1)**.

Pre-release tags op GitHub: `v0.1.0` t/m `v0.6.1`. Zie [CHANGELOG.md](CHANGELOG.md) voor release-notes per versie.

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

### v1 (pre-release, branch `v1`)

- [v0.6.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.6.1) — Status-tegel prijsbron
- [v0.6.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.6.0) — EnergyZero prijsbron
- [v0.5.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.5.0) — ENTSO-E prijsbron
- [v0.4.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.4.1) — Thuisbatterij-labels
- [v0.4.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.4.0) · [v0.3.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.3.0) · [v0.2.1](https://github.com/rleunk/easee-domoticz/releases/tag/v0.2.1) · [v0.2.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.2.0) · [v0.1.0](https://github.com/rleunk/easee-domoticz/releases/tag/v0.1.0)

### Legacy v10 (productie)

- [v10.11.6](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6) — legacy stable (aanbevolen productie)
- [v10.11.5](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.5) — rollback
- [v10.10.8](https://github.com/rleunk/easee-domoticz/releases/tag/v10.10.8) — rollback (16 tegels)

Zie [CHANGELOG.md](CHANGELOG.md) en [README.md](README.md) voor details per versie.
