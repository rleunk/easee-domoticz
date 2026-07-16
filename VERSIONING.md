# Versioning

Dit project heeft twee versielijnen naast elkaar.

## v1 (productie)

| Item | Waarde |
|------|--------|
| **Huidige versie** | **1.1.5** (released 2026-07-16) |
| **Branch productie** | `main` |
| **Branch ontwikkeling** | `v1` (1.2.x en verder) |
| **Tag** | `v1.1.5` (semver, geen `-stable` suffix) |

### Semver v1

- **0.x.y** — pre-release ontwikkeling op branch `v1` (`v0.1.0` t/m `v0.6.1`)
- **1.1.5** — huidige productie op `main` (LB fase-detail, Tibber fallbacks)
- **1.0.0** — eerste publieke stable v1 op `main`
- **1.x.y** — toekomstige releases; ontwikkeling start op branch `v1`, merge naar `main` bij release

## Legacy v10 (bevroren)

| Item | Waarde |
|------|--------|
| **Laatste versie** | `v10.11.6` |
| **Branch** | `legacy/v10` |
| **Tags** | `v10.11.6`, `v10.11.6-stable` (en oudere `v10.x.y` / `-stable`) |
| **Status** | Bevroren — geen hernummering naar 0.10.x |

Legacy v10 blijft beschikbaar voor bestaande installaties en rollback. Nieuwe installaties: gebruik **`main`** / **`v1.1.5`**.

## Checkout

```bash
# v1 productie (aanbevolen)
git fetch --tags origin
git checkout main
# of: git checkout v1.1.5

# v1 ontwikkeling (1.2.x)
git fetch origin
git checkout v1

# Legacy v10
git checkout legacy/v10
# of: git checkout v10.11.6-stable
```

Zie [STABLE.md](STABLE.md) voor aanbevolen tags en rollback, [CHANGELOG.md](CHANGELOG.md) voor release-notes, [docs/RELEASE_1.1.5.md](docs/RELEASE_1.1.5.md) voor de huidige productie-release.
