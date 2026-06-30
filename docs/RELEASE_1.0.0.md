# Release — v1 **1.0.0** ✅

Branch **`main`**, code version **1.0.0**, tag **`v1.0.0`**. Released **2026-06-30**.

Legacy v10.11.6 is bewaard op branch **`legacy/v10`** (tags `v10.11.6` / `v10.11.6-stable`). Toekomstige v1-ontwikkeling (1.1.x) op branch **`v1`**.

See also [STABLE.md](../STABLE.md), [VERSIONING.md](../VERSIONING.md), [CHANGELOG.md](../CHANGELOG.md).

---

## Checklist

| Item | Status | Notes |
|------|--------|-------|
| v1 line **0.1.0 → 0.6.1** pre-releases tagged | ✅ | GitHub releases `v0.1.0` … `v0.6.1` |
| All price sources implemented | ✅ | Geen, Handmatig, Tibber, ENTSO-E, EnergyZero |
| All price sources tested on live Domoticz | ✅ | Richard setup — ENTSO-E confirmed 2026-06-29 |
| EnergyZero token-free | ✅ | `api.energyzero.nl` |
| Status tile shows prijsbron | ✅ | All Mode9 values |
| Energy hints (P1, solar, thuisbatterij) | ✅ | Mode20–23 |
| 11 tiles + LoadBal layout | ✅ | 2 laders + EQ + pricing |
| Legacy v10 preserved on `legacy/v10` | ✅ | v10.11.6 content + tags intact |
| Public docs synced to 1.0.0 | ✅ | README, INSTALL, STABLE, VERSIONING, … |
| Soak test on production Domoticz | ✅ | Completed 2026-06-30 |
| Tag **`v1.0.0`** + GitHub release | ✅ | Latest release on GitHub |
| Domoticz forum announcement | ⏳ | Draft: [FORUM_POST.md](FORUM_POST.md) |

---

## Release procedure (executed)

```bash
# 1. Preserve legacy
git checkout main
git branch legacy/v10
git push origin legacy/v10

# 2. Version bump + docs on v1, merge to main
git checkout v1
# bump PLUGIN_VERSION to 1.0.0, update docs
git commit -m "release: v1.0.0"
git checkout main
git merge v1
git push origin main v1 legacy/v10

# 3. Tag and release
git tag -a v1.0.0 -m "v1.0.0: first stable v1 release"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --latest
```

---

## Intentionally open after 1.0.0

- Equalizer LB fase-detail refinements
- Domoticz Energy-tegel default bliksem icoon (platform limitation)
- Adaptieve poll-interval bij 429 (research)
- Tibber smart charging / Grid Rewards (no public API — display hints only)

See [ROADMAP.md](ROADMAP.md).
