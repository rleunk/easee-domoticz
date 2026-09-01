# Release — v1 **1.1.7** ✅

**Language / Taal:** [English](../RELEASE_1.1.7.md) · **Nederlands** (this page)

Branch **`main`**, code version **1.1.7**, tag **`v1.1.7`**. Released **2026-09-01**.

Hotfix voor Easee API-wijziging per **2026-09-01**.

---

## Opgelost

| Item | Details |
|------|---------|
| **Charger 404-fouten** | Easee verwijderde `GET /api/chargers/{id}/state` — plugin gebruikt nu **Get Observations** op `/state/{serial}/observations?ids=…` |
| **Legacy fallback** | Oude state-endpoint blijft geprobeerd als observations geen data geeft |
| **Logging** | Verwachte legacy 404 → DEBUG; ERROR alleen als observations én legacy falen |

---

## Upgrade vanaf 1.1.6

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Herstart het Easee hardware-item. Log: `Plugin v1.1.7 gestart`. Geen herhaalde `404 … /state`-errors meer op laadpalen.

---

## Rollback

```bash
git checkout v1.1.6
sudo systemctl restart domoticz
```

Let op: **1.1.6** herstelt laadpaal-tegels niet na 2026-09-01 (Easee API). Rollback alleen zinvol vóór de cutoff.

Zie [STABLE.nl.md](../../STABLE.nl.md) · [CHANGELOG.md](../../CHANGELOG.md).
