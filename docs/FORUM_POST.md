> **Draft for Domoticz forum — use at 1.0.0 go-live**

---

**Subject:** Easee EV chargers + Equalizer — Domoticz hardware plugin

Hi all,

We've been building a **Domoticz hardware plugin** for **Easee** EV chargers and **Equalizers** together and wanted to share an overview for anyone looking for native Domoticz integration (no MQTT bridge).

**GitHub:** https://github.com/rleunk/easee-domoticz  
**Status:** Active development on branch `v1` (currently v0.6.1 pre-release). Legacy v10 remains on `main` for existing installs.

---

### How it works with Domoticz

1. Install the plugin in your `plugins` folder  
2. Add **Easee** under **Setup → Hardware** (Easee account email + password)  
3. Restart the hardware item — the plugin connects to the Easee Cloud API  
4. **Auto-discovery** creates Domoticz devices on your dashboard  
5. A poll loop keeps power, status, kWh and optional costs up to date  

Everything shows up as normal Domoticz devices — usable in the web UI, app, notifications and scripts.

---

### What we built (typical dashboard)

**11 tiles + LoadBal switch:**

- **Global:** Status · Total charging · Total kWh · Best charging window · Daily overview  
- **Per charger:** Charging power · Status (with session/day cost when pricing is on)  
- **Equalizer:** Status (fuse, phases, load balancing) · Power (import/export/net)  
- **LoadBal switch** to toggle Easee load balancing  

Custom icons can be uploaded in Domoticz; the plugin applies them automatically.

---

### Optional: energy pricing

In hardware settings, group **"Energy price (optional)"**:

| Source | Notes |
|--------|--------|
| **None** | kWh and time only |
| **Manual** | Fixed, day/night, or off-peak/peak tariffs |
| **Tibber** | Dynamic prices via API token (quarter-hourly when available) |
| **ENTSO-E** | Day-ahead spot + configurable markup, tax, VAT |
| **EnergyZero** | Public hourly prices — no token needed |

The **Status** tile shows the active source (e.g. `EnergyZero €0.17/kWh`).

---

### Optional: energy hints

If you already have P1 meter, solar, or home battery devices in Domoticz, you can point the plugin at them for **context hints** on charger status (export, solar surplus, battery active). Display only — no automatic charge control.

---

### Requirements & limitations

- Domoticz with Python plugin support  
- Easee account + internet access  
- Does **not** replace the Easee app for full configuration  
- Tibber smart charging / Grid Rewards cannot be controlled from Domoticz  
- ENTSO-E / EnergyZero prices are **estimates**, not exact bill amounts  

---

### Quick install

```bash
cd /path/to/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout v1
# Restart Domoticz → Setup → Hardware → Add Easee → restart hardware
```

---

We're still working toward a **1.0.0 stable** release. Feedback from other Domoticz + Easee users is very welcome — issues and suggestions on GitHub.
