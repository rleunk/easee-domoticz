> **Ready to publish** — Domoticz forum announcement for **v1.1.5** (soak confirmed 2026-08-09). Copy from the `---` line below.

---

**Subject:** Easee EV chargers + Equalizer — Domoticz hardware plugin v1.1.5

Hi all,

We've been building a **Domoticz hardware plugin** for **Easee** EV chargers and **Equalizers** and wanted to share an overview for anyone looking for native Domoticz integration (no MQTT bridge).

**GitHub:** https://github.com/rleunk/easee-domoticz  
**Release:** [**v1.1.5**](https://github.com/rleunk/easee-domoticz/releases/tag/v1.1.5) on branch `main` — production-ready (soak **2026-07-16 → 2026-08-09**, no errors on a live 2-charger + Equalizer + Tibber setup).  
**Legacy:** v10.11.6 preserved on branch `legacy/v10` for existing installs.

---

### How it works with Domoticz

1. Install the plugin in your `plugins` folder  
2. Add **Easee Domoticz plugin v1 (1.1.5)** under **Setup → Hardware** (Easee account email + password)  
3. Restart the hardware item — the plugin connects to the Easee Cloud API  
4. **Auto-discovery** creates Domoticz devices on your dashboard  
5. A poll loop keeps power, status, kWh and optional costs up to date  

Everything shows up as normal Domoticz devices — usable in the web UI, app, notifications and scripts.

---

### What you get (typical dashboard)

**11 tiles + LoadBal switch:**

| Area | Tiles |
|------|--------|
| **Global** | Status · Total charging · Total kWh · Best charging window · Daily overview |
| **Per charger** | Charging power · Status (session/day cost when pricing is on) |
| **Equalizer** | Status (LB, limits, phases) · Power (import/export/net) |
| **Control** | LoadBal switch to toggle Easee load balancing |

Custom icons (13 sets) can be uploaded in Domoticz; the plugin applies them automatically.

---

### Equalizer load balancing — phase detail (v1.1.x)

On the **Equalizer Status** tile you get per-phase info when load balancing is active:

| Label | Meaning |
|-------|---------|
| **Vrij** / **Vrij≈** | Available capacity per phase (L1/L2/L3). **Vrij≈** is estimated when Tibber/cloud-LB does not expose Easee `availableCurrent*` keys |
| **Laad** | Charging current per phase — from charger state when the equalizer API omits it |
| **Gemeten** | Measured grid current L1/L2/L3 from the Equalizer |

Also shown: fuse limits, max import, voltage per phase. Tested with **Tibber-managed load balancing** (403/405 on some Easee cloud-LB endpoints is normal — the plugin uses fallbacks).

**Adaptive polling:** on HTTP 429 the plugin temporarily increases the poll interval (up to 120s) and returns to your configured interval when rate limits clear.

---

### Optional: energy pricing

In hardware settings, group **"Energy price (optional)"**:

| Source | Notes |
|--------|--------|
| **None** | kWh and time only |
| **Manual** | Fixed, day/night, or off-peak/peak tariffs |
| **Tibber** | Dynamic prices via API token (quarter-hourly when available) |
| **ENTSO-E** | Day-ahead spot + configurable markup, tax, VAT — **tested** (e-mail approval + token backup) |
| **EnergyZero** | Public hourly prices — no token needed — **tested** |

The **Status** tile shows the active source (e.g. `EnergyZero €0.17/kWh`).

---

### Optional: energy hints

If you already have P1 meter, solar, or home battery devices in Domoticz, you can point the plugin at them for **context hints** on charger status (export, solar surplus, battery active). Display only — no automatic charge control.

---

### Requirements & limitations

- Domoticz with Python plugin support  
- Easee account + internet access  
- Does **not** replace the Easee app for full configuration  
- Tibber smart charging / Grid Rewards **cannot be controlled** from Domoticz (display hints only, e.g. “Probably Grid Rewards”)  
- ENTSO-E / EnergyZero prices are **estimates**, not exact bill amounts  
- Optional API **403/405** on cloud load-balancing endpoints is expected with third-party LB (Tibber) — not a plugin fault  

---

### Install (new)

```bash
cd /home/USER/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout main
sudo systemctl restart domoticz
# Setup → Hardware → Add "Easee Domoticz plugin v1 (1.1.5)" → restart hardware item
```

### Upgrade (existing v1 or v10)

```bash
cd /path/to/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main && git pull origin main   # v1.1.5 productie
# legacy v10 rollback: git checkout legacy/v10
sudo systemctl restart domoticz
# Restart the Easee hardware item — log should show: Plugin v1.1.5 gestart
```

Docs: [README](https://github.com/rleunk/easee-domoticz/blob/main/README.md) · [INSTALL](https://github.com/rleunk/easee-domoticz/blob/main/INSTALL.md) · [RELEASE 1.1.5](https://github.com/rleunk/easee-domoticz/blob/main/docs/RELEASE_1.1.5.md) · [Troubleshooting](https://github.com/rleunk/easee-domoticz/blob/main/docs/TROUBLESHOOTING.md)

---

**v1.1.5** is the current stable v1 release — five price sources, Equalizer LB phase detail with Tibber fallbacks, and ~3 weeks production soak without plugin errors. Feedback from other Domoticz + Easee users is very welcome — [GitHub Issues](https://github.com/rleunk/easee-domoticz/issues).
