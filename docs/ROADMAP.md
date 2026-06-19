# Roadmap

Kort overzicht — **v10.9.28** is de huidige *stable testing* functionele release; **v10.9.29** = logging-opruiming. Pauze in actieve ontwikkeling.

## Afgerond — v10.9.x stable testing (2026-06)

- **v10.9.19–v10.9.28** — Kosten-tegels: legacy DeviceID lookup, stale sessionEnergy, dag-tracking, Vandaag kWh (middernacht-baseline + lifetime Counter), Tibber (Mode7) vereist. Getest door Richard (19-06-2026).
- **v10.9.29** — Logging opgeschoond: per-poll INFO → DEBUG; icon-diagnostiek 1× per start.
- **v10.9.11–v10.9.17** — Equalizer Vermogen betrouwbaarheid: poll na herstart, fallback-keten, 429 fail-fast, sticky power, per-endpoint rate limits, observations URL-fix, discovery-throttle.
- **v10.9.10** — Status combo-icoon (`EaseeStatusGlobal`); 13 icon sets.
- **v10.9.0–v10.9.1** — Equalizer geconsolideerd naar 2 tegels (Status + Vermogen).
- **v10.7.x** — Wrapper-cleanup en regressiefixes in modulaire codebase.

Zie [CHANGELOG.md](../CHANGELOG.md) voor details.

## Getest scenario

2× Charge Lite, 1× Equalizer, Tibber (Mode7) — **15 tegels** (zie [CONFIGURATION.md](CONFIGURATION.md#verwachte-tegels-referentie)). Kosten-tegels en Vandaag kWh bevestigd werkend (Richard, 19-06-2026).

## Toekomst (indicatief, geen planning)

- Equalizer stap 2+ (uitbreidingen buiten huidige stap-1 scope)
- Verdere stabilisatie op basis van bugreports via [Issues](https://github.com/rleunk/easee-domoticz/issues)
