# Release — v1 **1.1.8** ✅

**Language / Taal:** [English](../RELEASE_1.1.8.md) · **Nederlands** (this page)

Branch **`main`**, versie **1.1.8**, tag **`v1.1.8`**. Uitgebracht **2026-11-26**.

Een Tibber-account met meerdere woningen gebruikt nu de woning die nog prijsdata heeft.

---

## Wat is opgelost

| Onderdeel | Details |
|-----------|---------|
| **Meerdere Tibber-woningen** | De plugin nam altijd `homes[0]`. Een oud adres zonder contract gaf daardoor geen prijzen. Nu wordt de eerste woning met een prijs in `priceInfo` gebruikt, en dat home-id gelogd. Bij twee woningen met prijzen wint de eerste in de Tibber-lijst. |
| **User-Agent** | De Tibber-call stuurt `Domoticz-Easee/1.1.8` mee. |
| **Optionele circuit-403** | `GET /sites/…/circuits` zonder rechten logt als debug, net als de cloud-loadbalancing-fallbacks. Die probes blijven staan. |

---

## Upgrade vanaf 1.1.7

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Herstart het Easee hardware-item. Log: `Plugin v1.1.8 gestart`. Met debug aan: `Tibber-woning in gebruik` en daarna `Tibber prijzen geladen`.

---

## Rollback

```bash
git checkout v1.1.7
sudo systemctl restart domoticz
```

Zie [STABLE.nl.md](../../STABLE.nl.md) · [CHANGELOG.md](../../CHANGELOG.md).
