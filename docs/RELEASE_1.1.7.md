# Release — v1 **1.1.7** ✅

**Language:** **English** · [Nederlands](nl/RELEASE_1.1.7.md)

Branch **`main`**, version **1.1.7**, tag **`v1.1.7`**. Released **2026-09-01**.

Hotfix for Easee API change effective **2026-09-01**.

---

## What's fixed

| Item | Details |
|------|---------|
| **Charger 404 errors** | Easee removed `GET /api/chargers/{id}/state` — plugin now uses **Get Observations** at `/state/{serial}/observations?ids=…` |
| **Legacy fallback** | Old state endpoint still tried when observations return no data (pre-cutoff accounts) |
| **Logging** | Expected legacy 404 → DEBUG; ERROR only when both observations and legacy fail |

---

## Upgrade from 1.1.6

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart Easee hardware item. Log: `Plugin v1.1.7 gestart`. Charger poll should no longer show repeated `404 … /state` errors.

---

## Rollback

```bash
git checkout v1.1.6
sudo systemctl restart domoticz
```

Note: **1.1.6** will not restore charger tiles after 2026-09-01 (Easee API). Rollback only useful before the Easee cutoff or for non-charger testing.

See [STABLE.md](../STABLE.md) · [CHANGELOG.md](../CHANGELOG.md).
