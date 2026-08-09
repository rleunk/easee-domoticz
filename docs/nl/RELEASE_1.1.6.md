# Release — v1 **1.1.6** ✅

**Language / Taal:** [English](../RELEASE_1.1.6.md) · **Nederlands** (this page)

Branch **`main`**, code version **1.1.6**, tag **`v1.1.6`**. Released **2026-08-09**.

Volgt op **1.1.5** (2026-07-16). Ontwikkeling op branch **`v1`**, gemerged naar **`main`**.

Zie ook [STABLE.nl.md](../../STABLE.nl.md), [VERSIONING.nl.md](../../VERSIONING.nl.md), [CHANGELOG.md](../../CHANGELOG.md), [RELEASE_1.1.5.md](RELEASE_1.1.5.md).

---

## Wat is nieuw

| Item | Details |
|------|---------|
| **English UI** | Hardware **Taal / Language** (Mode30): tegelteksten, status, Equalizer LB, prijshints in **English** |
| **Default** | **Nederlands** — bestaande installs ongewijzigd tot je Mode30 wijzigt |
| **1.1.5 basis** | LB fase-detail, Tibber Vrij≈/Laad fallbacks, adaptief poll — ongewijzigd |

Zie [CONFIGURATION.md](CONFIGURATION.md#taal--language-mode30).

---

## Checklist

| Item | Status |
|------|--------|
| English UI (Mode30) ontwikkeld op `v1` | ✅ |
| Default Nederlands — backward compatible | ✅ |
| Public docs synced naar 1.1.6 | ✅ |
| Tag **`v1.1.6`** + GitHub release | ✅ |
| Merge `v1` → `main` | ✅ |

---

## Upgrade vanaf 1.1.5

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main
git pull origin main
sudo systemctl restart domoticz
```

Herstart het Easee hardware-item. Log: `Plugin v1.1.6 gestart`.

Optioneel: **Setup → Hardware → Easee → Taal / Language → English**.

---

## Rollback

```bash
git checkout v1.1.5
sudo systemctl restart domoticz
```
