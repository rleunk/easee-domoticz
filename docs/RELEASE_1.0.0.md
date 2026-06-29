# Release readiness — v1 **1.0.0-stable**

Branch **`v1`**, code version **0.6.1** (pre-release). This document tracks what is done and what remains before tagging **`1.0.0-stable`** and promoting the GitHub release from pre-release.

Legacy productie stays on **`main`** / [**v10.11.6-stable**](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6-stable) until v1 is explicitly promoted.

See also [STABLE.md](../STABLE.md), [VERSIONING.md](../VERSIONING.md), [CHANGELOG.md](../CHANGELOG.md).

---

## Checklist

| Item | Status | Notes |
|------|--------|-------|
| v1 line **0.1.0 → 0.6.1** pre-releases tagged | ✅ | GitHub releases `v0.1.0` … `v0.6.1` |
| All price sources implemented | ✅ | Geen, Handmatig, Tibber, ENTSO-E, EnergyZero |
| All price sources tested on live Domoticz | ✅ | Richard setup — ENTSO-E confirmed 2026-06-29 (e-mail approval + token backup) |
| EnergyZero token-free | ✅ | `api.energyzero.nl` |
| Status tile shows prijsbron (0.6.1) | ✅ | All Mode9 values |
| Energy hints (P1, solar, thuisbatterij) | ✅ | Mode20–23 |
| 11 tiles + LoadBal layout | ✅ | 2 laders + EQ + pricing |
| Legacy v10 frozen on `main` | ✅ | v10.11.6-stable |
| Public docs synced to 0.6.1 | ✅ | README, INSTALL, CONFIGURATION, TROUBLESHOOTING, … |
| Soak test on production Domoticz | ⏳ | Richard — ongoing on v0.6.1; no critical regressions required before tag |
| Tag **`1.0.0-stable`** + GitHub release | ⏳ | After soak sign-off; promote from last pre-release |
| Domoticz forum announcement | ⏳ | Draft: [FORUM_POST.md](FORUM_POST.md) |

---

## Soak-test criteria (before tag)

Use this as the gate for **1.0.0-stable** — adjust duration if you want a longer burn-in:

1. **Branch `v1`**, version **0.6.1** (or final pre-release commit) on the production Domoticz server.
2. **Minimum soak period** — e.g. 7–14 days continuous operation without hardware-thread crashes (`heartbeat exception` in log).
3. **Core behaviour** — login, poll loop, laadpalen + Equalizer tiles update; `image_ids: 13/13` after start (or handmatige zip).
4. **Pricing** — at least one full day with your chosen **Prijsbron**; *Dag overzicht* and laadpaal-**Status** show plausible € (not stuck at €0,00).
5. **Optional checks** — switch Prijsbron once (e.g. Tibber ↔ EnergyZero) and confirm Status tile label updates; ENTSO-E/ Tibber token survives hardware *Save* (state backup).
6. **No open P0/P1 issues** on GitHub for v1 scope.

---

## Tag procedure (when ready)

Do **not** run until soak sign-off:

```bash
cd /home/root/domoticz/plugins/Easee-Domoticz-plugin
git fetch origin
git checkout v1
git pull origin v1
# Bump PLUGIN_VERSION to 1.0.0 in easee_constants.py + plugin.xml if not done in a prior commit
git tag -a 1.0.0-stable -m "v1 stable: all price sources, docs complete"
git push origin v1
git push origin 1.0.0-stable
```

On GitHub: create release **1.0.0-stable** from tag, mark as **latest** for v1, copy notes from CHANGELOG. Post [FORUM_POST.md](FORUM_POST.md) on the Domoticz forum.

---

## Intentionally open after 1.0.0

- Equalizer LB fase-detail refinements
- Domoticz Energy-tegel default bliksem icoon (platform limitation)
- Adaptieve poll-interval bij 429 (research)
- Tibber smart charging / Grid Rewards (no public API — display hints only)

See [ROADMAP.md](ROADMAP.md).
