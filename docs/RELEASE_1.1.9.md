# Release — v1 **1.1.9** ✅

**Language:** **English** · [Nederlands](nl/RELEASE_1.1.9.md)

Branch **`main`**, version **1.1.9**, tag **`v1.1.9`**. Released **2026-11-26**.

Energy hints can read a P1 meter, solar inverter, or home battery that belongs to another hardware item.

---

## What's fixed

| Item | Details |
|------|---------|
| **Energy hints** | Mode21–23 accept a Domoticz device **name** or **Idx** from Setup → Devices. The plugin reads them through the local API `http://127.0.0.1:<www port>/json.htm?type=devices`. `127.0.0.1` must stay in Local Networks (the default). |
| **P1** | Electricity meter. Power comes from `Usage` and `UsageDeliv` in watts. A gas meter is ignored. |
| **Solar and battery** | One device each, current watts in `Usage` or `Data`. An empty Mode23 turns the battery hint off. |

---

## Upgrade from 1.1.8

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart the Easee hardware item. Log: `Plugin v1.1.9 gestart`. With debug on, a found meter logs `P1: <name> (idx <n>), import … W, export … W`.

---

## Rollback

```bash
git checkout v1.1.8
sudo systemctl restart domoticz
```

See [STABLE.md](../STABLE.md) · [CHANGELOG.md](../CHANGELOG.md).
