# Configuration guide

**Language:** **English** · [Nederlands](../CONFIGURATION.md)

Hardware parameters in Domoticz **Setup → Hardware → Easee**.

## Basic

| Field | Required | Description |
|-------|----------|-------------|
| **Username** | Yes | Easee account email or phone |
| **Password** | Yes | Easee password |

## Display & polling

| Field | Default | Description |
|-------|---------|-------------|
| **Poll interval (Mode1)** | 30 s | API poll rate; use **60 s** on HTTP 429 |
| **Language (Mode30)** | Nederlands | **English** — tile text and status lines |
| **Site filter (Mode5)** | empty | Filter chargers/equalizers by name substring |
| **Debug logging (Mode6)** | Normal | Set **Debug** only when investigating issues |

## Charger names (optional)

| Field | Description |
|-------|-------------|
| **Mode2** | Charger 1 display name |
| **Mode3** | Charger 2 display name |
| **Mode4** | Extra names comma-separated (from charger 3) |

Leave empty to use Easee app names.

## Equalizer (optional)

| Field | Description |
|-------|-------------|
| **Address** | Equalizer display name (e.g. Meter cupboard) |
| **IP** | Manual Equalizer ID if auto-discovery fails |

### Equalizer Status tile

Shows per phase when load balancing is active:

| Label | Meaning |
|-------|---------|
| **Avail** / **Avail≈** | Available capacity L1/L2/L3; **≈** when estimated (Tibber/cloud-LB) |
| **Charge** | Charging current per phase (charger fallback if API omits data) |
| **Measured** | Grid current L1/L2/L3 |

Also: fuse limits, max import, voltage per phase.

## Expected tiles (reference)

**2 chargers + 1 Equalizer + pricing:** **11 active tiles + LoadBal**

| Global | Per charger | Equalizer |
|--------|-------------|-----------|
| Status, Total charging, Total kWh | Charging, Status | Status, Power |
| Best charging, Daily overview | | |
| LoadBal switch | | |

Deprecated since v10.11 (hidden after upgrade): *Costs & Summary*, *Day report*, *Total & Session*, *Costs (Session/Day)*.

## Price source (Mode9)

| Value | Token / config |
|-------|----------------|
| **None** | kWh and hours only — no € |
| **Manual** | Mode10–19 (Fixed / Day-night / Off-peak-peak) |
| **Tibber** | Mode7 token (default price source) |
| **ENTSO-E** | Mode24 token + Mode25–27 markup |
| **EnergyZero** | No token — public NL hourly API |

### Manual tariff (Mode11)

| Type | Fields |
|------|--------|
| **Fixed** | Mode10 €/kWh |
| **Day/night** | Mode12 dal, Mode13 normal, Mode14–15 hours |
| **Off-peak/peak** | Mode12–13, Mode16 peak €, Mode17–18 peak hours, Mode19 weekend |

### Tibber (Mode7)

- Token from [developer.tibber.com](https://developer.tibber.com/settings/access-token)
- Backed up in `easee_state.json` if Domoticz clears password field on save
- Token is **never** logged

### ENTSO-E (Mode24)

- Request token via [transparency.entsoe.eu](https://transparency.entsoe.eu/) (email approval)
- Mode25 supplier markup, Mode26 energy tax, Mode27 VAT %

### EnergyZero

- No token — automatic fetch from public API
- Mode29 info link only

### Best charging window (BesteLadenHours)

Hours for **Best charging** tile (default 3). Works with Tibber, Manual, ENTSO-E, EnergyZero.

## Energy hints (Mode20–23)

Display-only context on Status and Daily overview while charging:

| Field | Default | Description |
|-------|---------|-------------|
| **Mode20** | On | Enable hints |
| **Mode21** | Power | P1 meter device name or idx |
| **Mode22** | Zonnepanelen | Solar device name |
| **Mode23** | Sessy | Home battery (empty = off) |

Hints: solar surplus, grid export, battery active, high import.

## Custom icons

- **`Easee_icons_v2.zip`** — 13 icon sets, auto-loaded at startup
- Manual upload if log shows `image_ids: 0/13`
- **Known limitation:** some Energy tiles keep Domoticz default lightning icon

## State file

Runtime state: `easee_state.json` in plugin folder (tokens backup, session data, migrations).

## Best practices

- Poll **60 s** if you see HTTP 429
- Restart hardware item after every upgrade
- Do not commit tokens or passwords to git

Full Dutch reference (legacy sections): [../CONFIGURATION.md](../CONFIGURATION.md).
