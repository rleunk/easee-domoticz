# Release — v1 **1.1.5** ✅

Branch **`main`**, code version **1.1.5**, tag **`v1.1.5`**. Released **2026-07-16**.

Volgt op **1.0.0** (2026-06-30). Ontwikkeling 1.1.0–1.1.5 op branch **`v1`**, gemerged naar **`main`**.

Zie ook [STABLE.md](../STABLE.md), [VERSIONING.md](../VERSIONING.md), [CHANGELOG.md](../CHANGELOG.md), [RELEASE_1.0.0.md](RELEASE_1.0.0.md).

---

## Wat is nieuw sinds 1.0.0

| Versie | Hoogtepunten |
|--------|----------------|
| **1.1.0** | Equalizer LB fase-detail (Vrij/Laad/Gemeten), adaptief poll bij HTTP 429, Energy-tegel icoon docs |
| **1.1.1** | Fix equalizer poll crash (`dictionary changed size during iteration`) |
| **1.1.2** | Laad-fallback via laadpaal-fasedata bij Tibber/cloud-LB |
| **1.1.3** | Laad-fallback gebruikt werkelijke stroom (niet LB-limiet-keys) |
| **1.1.4** | **Vrij≈** schatting: `hoofdzekering-limiet − gemeten` per fase |
| **1.1.5** | **Gemeten**-regel hersteld naast Vrij≈ en Laad-fallback |

### Tibber + Equalizer (Richard setup)

- **Vrij≈** — geschatte vrije capaciteit per fase wanneer API geen `availableCurrent*` levert
- **Laad** — per-fase laadstroom uit charger `/state` of vermogen×fase
- **Gemeten** — netstroom L1/L2/L3 uit equalizer (altijd zichtbaar bij Tibber/LB)
- Poll-volgorde: laders vóór equalizer (verse fallback-data)

---

## Checklist

| Item | Status | Notes |
|------|--------|-------|
| v1.1.0–1.1.5 ontwikkeld op branch `v1` | ✅ | 6 commits na 1.0.0 |
| Live test 2× lader + 1× EQ + Tibber | ✅ | Richard — 2026-07-16 |
| Geen heartbeat-crashes na 1.1.1 | ✅ | Soak + laden/idle |
| Public docs synced naar 1.1.5 | ✅ | README, STABLE, VERSIONING, … |
| Tag **`v1.1.5`** + GitHub release | ✅ | Latest release |
| Domoticz forum announcement | ⏳ | Draft: [FORUM_POST.md](FORUM_POST.md) |

---

## Upgrade vanaf 1.0.0

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout main
git pull origin main
sudo systemctl restart domoticz
```

Herstart het Easee hardware-item in Domoticz. Log: `Plugin v1.1.5 gestart`.

---

## Release procedure (executed)

```bash
git checkout main
git merge v1
git push origin main
git tag -a v1.1.5 -m "v1.1.5: LB fase-detail, Tibber Vrij≈/Laad fallbacks, adaptive poll"
git push origin v1.1.5
gh release create v1.1.5 --title "v1.1.5" --latest
git checkout v1 && git merge main && git push origin v1
```

---

## Rollback

```bash
git checkout v1.0.0   # vorige productie
sudo systemctl restart domoticz
```
