# Release — v1 **1.1.6** ✅

**Language:** **English** · [Nederlands](../RELEASE_1.1.6.md)

Branch **`main`**, version **1.1.6**, tag **`v1.1.6`**. Released **2026-08-09**.

Follows **1.1.5** (2026-07-16).

---

## What's new

| Item | Details |
|------|---------|
| **English UI** | Hardware **Taal / Language** (Mode30) — tile text, status, Equalizer LB, pricing hints |
| **Default** | **Dutch** — existing installs unchanged until you switch Mode30 |
| **1.1.5 base** | LB phase detail (Avail≈/Charge/Measured), Tibber fallbacks, adaptive poll on HTTP 429 |

---

## Upgrade from 1.1.5

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart Easee hardware item. Log: `Plugin v1.1.6 gestart`.

Optional: **Setup → Hardware → Easee → Taal / Language → English**.

---

## Rollback

```bash
git checkout v1.1.5
sudo systemctl restart domoticz
```

See [STABLE.en.md](../../STABLE.en.md) · [CHANGELOG.md](../../CHANGELOG.md).
