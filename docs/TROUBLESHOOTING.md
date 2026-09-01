# Troubleshooting

**Language:** **English** · [Nederlands](nl/TROUBLESHOOTING.md)

> **Versions:** **main** = **1.1.7** (production) · Legacy **v10.11.6** on `legacy/v10`  
> Install: [INSTALL.md](../INSTALL.md) · Config: [CONFIGURATION.md](CONFIGURATION.md)

## Plugin does not load

**Symptom:** Easee plugin type missing in Hardware menu

```bash
ls -la /home/USER/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
sudo apt install -y python3-requests
sudo systemctl restart domoticz
sudo journalctl -u domoticz -f | grep Easee
```

## Login failed

**Symptom:** `Login mislukt` / `Login failed` in Status tile or log

1. Check credentials in **Setup → Hardware**
2. Test login in Easee app
3. Enable **Debug logging** (Mode6)
4. Wait 5–10 minutes on Easee rate limit

## No devices created

1. Chargers visible in Easee app?
2. Clear site filter (Mode5)
3. Wait 1–2 minutes after first start
4. Log: `grep -i "charger\|Discovery" domoticz.log`

## Wrong tile count / legacy tiles

**Expected:** 2 chargers + 1 Equalizer + pricing → **11 tiles + LoadBal**

Remove legacy tiles manually if present: *Import*, *Spanning*, *Netto*, old *Load balancing* equalizer tiles.

Merged in v10.11: *Day report* → **Daily overview**, session costs → **Status** / **Charging**.

## Custom icons missing

Log: `image_ids: 0/13`

1. Remove old Easee custom icons in Domoticz settings
2. `git pull` on `main`, restart hardware item
3. Upload `Easee_icons_v2.zip` manually if needed
4. Expect `image_ids: 13/13 sets`

## Charger state HTTP 404 (from 2026-09-01)

**Symptom:** `State ophalen mislukt voor lader … 404 … /api/chargers/…/state` every poll; Equalizer still works.

**Cause:** Easee removed `GET /api/chargers/{id}/state` on **2026-09-01**. Plugin **1.1.6 and older** no longer receive charger telemetry.

**Fix:** Upgrade to **1.1.7+**:

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin && git checkout main && git pull origin main
sudo systemctl restart domoticz
```

Restart the Easee hardware item. Log should show `Plugin v1.1.7 gestart` and charger polls via observations (no repeated 404 errors).

## HTTP 429 rate limit {#http-429-rate-limit-easee-api}

**Symptom:** `HTTP 429` in log; WARNING about rate limit

1. Set **Poll interval (Mode1)** to **60** (or higher)
2. Plugin **automatically** increases interval temporarily (up to 120 s) on 429
3. Returns to Mode1 when limits clear

## Equalizer power 0/0/0

1. Enable Debug (Mode6) — check equalizer state keys in log
2. Enter manual Equalizer ID in **IP** field if discovery fails
3. 403/405 on cloud-LB endpoints with Tibber is **normal** — plugin uses fallbacks

## ENTSO-E unauthorized

Token requires email approval from ENTSO-E. Until approved: use Tibber, EnergyZero, or Manual temporarily.

Token backup in `easee_state.json` (`entsoe_token_backup`) — same pattern as Tibber Mode7.

## Tibber token cleared

Domoticz sometimes clears password fields on save. Re-enter Mode7 or rely on `tibber_token_backup` in state file. Log: `token restored from state backup`.

## Costs show €0.00

1. Check **Price source (Mode9)** matches your token (Mode7 / Mode24)
2. Wait for first price poll after startup
3. Restart hardware item after changing Mode9

## English UI not showing

1. Set **Taal / Language (Mode30)** to **English**
2. Restart hardware item
3. Tile **names** update on next device sync; **text** updates every poll

Full Dutch guide: [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
