# Release — v1 **1.1.8** ✅

**Language:** **English** · [Nederlands](nl/RELEASE_1.1.8.md)

Branch **`main`**, version **1.1.8**, tag **`v1.1.8`**. Released **2026-11-26**.

Tibber accounts with more than one home now use the home that still has price data.

---

## What's fixed

| Item | Details |
|------|---------|
| **Several Tibber homes** | The plugin used `homes[0]`. An old address without a contract produced no prices. It now uses the first home whose `priceInfo` contains a price, and logs that home id. If two homes have prices, the first one in Tibber's list is used. |
| **User-Agent** | The Tibber GraphQL call sends `Domoticz-Easee/1.1.8`. |
| **Optional circuit 403** | `GET /sites/…/circuits` without permission logs at DEBUG, same as the cloud-loadbalancing fallbacks. Those probes stay. |

---

## Upgrade from 1.1.7

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart the Easee hardware item. Log: `Plugin v1.1.8 gestart`. With debug on, Tibber logs `Tibber-woning in gebruik` and then `Tibber prijzen geladen`.

---

## Rollback

```bash
git checkout v1.1.7
sudo systemctl restart domoticz
```

See [STABLE.md](../STABLE.md) · [CHANGELOG.md](../CHANGELOG.md).
