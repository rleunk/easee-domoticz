# Release — v1 **1.1.9** ✅

**Language / Taal:** [English](../RELEASE_1.1.9.md) · **Nederlands** (this page)

Branch **`main`**, versie **1.1.9**, tag **`v1.1.9`**. Uitgebracht **2026-11-26**.

Energie-hints kunnen een P1-meter, omvormer of thuisbatterij van een ander hardware-item lezen.

---

## Wat is opgelost

| Onderdeel | Details |
|-----------|---------|
| **Energie-hints** | Mode21–23 verwachten een Domoticz-apparaatnaam of de **Idx** uit Instellingen → Apparaten. De plugin leest ze via de lokale API `http://127.0.0.1:<www-poort>/json.htm?type=devices`. `127.0.0.1` hoort in Lokale netwerken te staan (de standaard). |
| **P1** | Elektriciteitsmeter. Vermogen komt uit `Usage` en `UsageDeliv` in watt. Een gasmeter telt niet. |
| **Zon en batterij** | Elk één apparaat, actueel vermogen in `Usage` of `Data`. Mode23 leeg zetten zet de batterij-hint uit. |

---

## Upgrade vanaf 1.1.8

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Herstart het Easee hardware-item. Log: `Plugin v1.1.9 gestart`. Met debug aan: `P1: <naam> (idx <n>), import … W, export … W`.

---

## Rollback

```bash
git checkout v1.1.8
sudo systemctl restart domoticz
```

Zie [STABLE.nl.md](../../STABLE.nl.md) · [CHANGELOG.md](../../CHANGELOG.md).
