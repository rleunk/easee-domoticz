# Versioning

**Language:** **English** · [Nederlands](VERSIONING.nl.md)

## v1 (production)

| Item | Value |
|------|--------|
| **Current version** | **1.1.9** (2026-11-26) |
| **Production branch** | `main` |
| **Development branch** | `v1` |
| **Tag** | `v1.1.9` |

- **1.1.9** — current production (energy hints read any Domoticz device)
- **1.1.8** — rollback (Tibber home with price data)
- **1.1.7** — rollback (Easee charger observations API hotfix)
- **1.1.6** — rollback (English UI + 1.1.5 base; charger state broken after Sep 2026)
- **1.1.5** — rollback baseline
- **1.0.0** — first public stable v1

## Legacy v10 (frozen)

| Item | Value |
|------|--------|
| **Version** | v10.11.6 |
| **Branch** | `legacy/v10` |

New installs: use **`main`** / **`v1.1.9`**.

## Install

```bash
git fetch --tags origin
git checkout main
```

See [STABLE.md](STABLE.md) · [docs/RELEASE_1.1.9.md](docs/RELEASE_1.1.9.md)
