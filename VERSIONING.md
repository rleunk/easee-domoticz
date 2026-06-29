# Versioning

Dit project heeft twee versielijnen naast elkaar.

## Legacy v10 (bevroren)

| Item | Waarde |
|------|--------|
| **Huidige stable** | `v10.11.6-stable` op branch `main` |
| **Status** | Bevroren productie-baseline — geen hernummering naar 0.10.x |
| **Tags** | `v10.x.y` en `v10.x.y-stable` blijven op `main` |

De v10-lijn blijft beschikbaar voor bestaande installaties. Wijzigingen aan v10 gaan alleen via hotfixes op `main` tot Richard v1 als stable promoot.

## v1 (nieuwe publieke lijn)

| Item | Waarde |
|------|--------|
| **Branch** | `v1` |
| **Huidige versie** | **0.6.1** (pre-release) |
| **Startversie** | `0.1.0` (scaffold; gedrag gelijk aan v10.11.6-stable) |
| **0.x** | Ontwikkeling — pre-release, niet productie-stable |
| **1.0.0-stable** | Eerste publieke stable v1 (gepland — na soak test) |

### Semver v1

- **0.x.y** — ontwikkeling op branch `v1`; pre-releases (`v0.1.0` t/m `v0.6.1`, …)
- **1.0.0-stable** — eerste stable v1 voor productie (annotated tag, suffix `-stable` zoals v10)
- **Geen** hernummering van v10 naar 0.10.x — v10 en v1 zijn parallel

### Criteria voor 1.0.0-stable

| Criterium | Status (0.6.1) |
|-----------|----------------|
| Prijsbronnen Geen / Handmatig / Tibber / ENTSO-E / EnergyZero | ✅ Getest |
| 11 tegels + LoadBal, energy hints, status prijsbron | ✅ |
| Docs gesynchroniseerd | ✅ |
| Soak test op productie-Domoticz | ⏳ Richard — ongoing |
| Tag + GitHub release + forum post | ⏳ Na soak |

Details: [docs/RELEASE_1.0.0.md](docs/RELEASE_1.0.0.md).

## Checkout

```bash
# Legacy productie (v10)
git checkout main
git checkout v10.11.6-stable

# v1 ontwikkeling
git fetch origin
git checkout v1
```

Zie [STABLE.md](STABLE.md) voor aanbevolen stable-tags en [CHANGELOG.md](CHANGELOG.md) voor release-notes.
