# Stable releases

Dit project gebruikt **annotated git-tags** met het suffix `-stable` voor aanbevolen productie-baselines. Gewone versietags (`v10.11.6`, `v10.11.5`, `v10.11.4`, `v10.11.2`, …) markeren releases; `-stable` geeft aan welke release Richard als **huidige stabiele baseline** aanbeveelt.

## Huidige stable

| Tag | Commit | Status |
|-----|--------|--------|
| **`v10.11.6-stable`** | zelfde als `v10.11.6` | **Aanbevolen** — Dag overzicht-migratie fix; idle timer **00:00**; compacte UI (**11 tegels** bij 2 laders + EQ + Tibber) |
| `v10.11.5-stable` | zelfde als `v10.11.5` | **Bewaard** — rollback-baseline (Dag overzicht-migratie met readonly-fout, v10.11.5) |
| `v10.11.4-stable` | zelfde als `v10.11.4` | **Bewaard** — rollback-baseline (truthy-fix, v10.11.4) |
| `v10.11.2-stable` | zelfde als `v10.11.2` | **Bewaard** — rollback-baseline (Status-timer pauze-fix, v10.11.2) |
| `v10.11.1-stable` | zelfde als `v10.11.1` | **Bewaard** — rollback-baseline (v10.11.1, compacte 11-tegel UI) |
| `v10.10.8-stable` | zelfde als `v10.10.8` | **Bewaard** — rollback-baseline (v10.10.x, 16 tegels) |
| `v10.9.32-stable` | zelfde als `v10.9.32` | **Bewaard** — oudere rollback (v10.9.x stable testing line) |

## Installeren of upgraden naar stable

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.6-stable
sudo systemctl restart domoticz
```

Of blijf op `main` volgen (`git pull`) — `main` wijst doorgaans naar dezelfde commit als de huidige stable.

**Na elke upgrade:** herstart het Easee hardware-item in Domoticz (**Setup → Hardware**).

## Rollback naar v10.11.5

Alleen als v10.11.6 problemen geeft:

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.5-stable
sudo systemctl restart domoticz
```

De tag `v10.11.5-stable` blijft op GitHub staan; er wordt niets verwijderd.

## Rollback naar v10.11.4

Alleen als v10.11.5/v10.11.6 problemen geeft:

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.4-stable
sudo systemctl restart domoticz
```

De tag `v10.11.4-stable` blijft op GitHub staan; er wordt niets verwijderd.

## Rollback naar v10.11.2

Alleen als v10.11.4/v10.11.5/v10.11.6 problemen geeft en je terug wilt naar de vorige stable (zelfde 11-tegel layout, zonder Dag overzicht-migratie):

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.11.2-stable
sudo systemctl restart domoticz
```

De tag `v10.11.2-stable` blijft op GitHub staan; er wordt niets verwijderd.

## Rollback naar v10.10.8

Alleen als v10.11.x problemen geeft en je terug wilt naar de v10.10.x stable (16-tegel layout):

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.10.8-stable
sudo systemctl restart domoticz
```

De tag `v10.10.8-stable` blijft op GitHub staan; er wordt niets verwijderd.

## Rollback naar v10.9.32

Alleen als v10.10.x óók problemen geeft:

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git fetch --tags origin
git checkout v10.9.32-stable
sudo systemctl restart domoticz
```

## Releases

- [v10.11.6](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.6) — huidige stable (aanbevolen)
- [v10.11.5](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.5) — vorige stable (rollback)
- [v10.11.4](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.4) — oudere rollback
- [v10.11.2](https://github.com/rleunk/easee-domoticz/releases/tag/v10.11.2) — oudere rollback
- [v10.10.8](https://github.com/rleunk/easee-domoticz/releases/tag/v10.10.8) — oudere rollback
- [v10.9.32](https://github.com/rleunk/easee-domoticz/releases/tag/v10.9.32) — oudere rollback

Zie [CHANGELOG.md](CHANGELOG.md) en [README.md](README.md) voor details per versie.
