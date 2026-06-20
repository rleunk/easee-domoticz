# Roadmap

Kort overzicht — **v10.10.8-stable** is de huidige stabiele baseline; **v10.9.32-stable** blijft bewaard voor rollback. Zie [STABLE.md](../STABLE.md).

## Afgerond — v10.10.x stable (2026-06)

- **v10.10.0** — Tibber kwartierprijzen, Dagrapport, laadhints, configureerbaar Beste laden, **16 tegels** met Tibber.
- **v10.10.1** — API-timeout crasht hardware-thread niet meer.
- **v10.10.2–v10.10.8** — Sessie-kWh, timer, kosten, EQ fase-weergave; Totaal & Sessie numerische Custom sValue; sessie-kWh cap op dagtotaal.
- **Stable release** — tag `v10.10.8-stable` (aanbevolen productie-baseline).

## Afgerond — v10.10.0 (2026-06-19)

- **Dagrapport-tegel** — kWh, €, laaduren, goedkoopste kwartier (Tibber).
- **Tibber kwartierprijzen** — kosten + Beste laden op 15-min resolutie.
- **Laadhints** — duur tarief / Grid Rewards op laadpaal-Status.
- **Tibber stuurt** — globale Status + EQ *Load balancing: Tibber*.
- **16 tegels** met Tibber (2 laders + EQ); tag `v10.9.32-stable` bewaard als vorige stable.

## Afgerond — v10.9.x stable testing (2026-06)

- **v10.9.19–v10.9.28** — Kosten-tegels: legacy DeviceID lookup, stale sessionEnergy, dag-tracking, Vandaag kWh (middernacht-baseline + lifetime Counter), Tibber (Mode7) vereist. Getest door Richard (19-06-2026).
- **v10.9.29** — Logging opgeschoond: per-poll INFO → DEBUG; icon-diagnostiek 1× per start.
- **v10.9.30** — Tibber-token backup in `easee_state.json` (Mode7 leeg na hardware-opslaan/plugin-update).
- **v10.9.31** — Optionele API 403/405 (equalizer state, loadbalancing, `/equalizers`, circuits) alleen DEBUG; 429 blijft WARNING. README-mockups dichter bij echte Domoticz-tegels.
- **v10.9.11–v10.9.17** — Equalizer Vermogen betrouwbaarheid: poll na herstart, fallback-keten, 429 fail-fast, sticky power, per-endpoint rate limits, observations URL-fix, discovery-throttle.
- **v10.9.10** — Status combo-icoon (`EaseeStatusGlobal`); 13 icon sets.
- **v10.9.0–v10.9.1** — Equalizer geconsolideerd naar 2 tegels (Status + Vermogen).
- **v10.9.7.x** — Wrapper-cleanup en regressiefixes in modulaire codebase.

Zie [CHANGELOG.md](../CHANGELOG.md) voor details.

## Getest scenario

2× Charge Lite, 1× Equalizer, Tibber (Mode7) — **16 tegels** (zie [CONFIGURATION.md](CONFIGURATION.md#verwachte-tegels-referentie)). Kosten-tegels, Dagrapport en Vandaag kWh bevestigd werkend (Richard, 19-06-2026). v10.10.8-stable sessie-kWh fixes getest (20-06-2026).

## Afgerond — geen plugin-plan

### Tibber slim laden / Grid Rewards

**Status: gesloten** — niet via API, alleen Easee/Tibber-app.

De Tibber GraphQL-API levert **alleen dynamische stroomprijzen** (gebruikt voor kosten-tegels). *Slim laden*, *Grid Rewards* en load-balancing-programma's zijn **app-only**; Easee biedt geen publieke API-endpoints daarvoor. Geen Domoticz-tegel of automatisering gepland tenzij Tibber of Easee dit later via API openstelt.

## Equalizer — stap 1 (afgerond) vs stap 2+ (beperkt door account-API)

### Stap 1 — wat nu werkt (v10.9.x)

| Onderdeel | Bron | Status |
|-----------|------|--------|
| Discovery | `/accounts/products`, `/sites`, detailed site | Werkt |
| Vermogen (import/terug/netto W) | Observations 40/41, fase I×V, cumulatief, sticky power | Werkt (fallback-keten) |
| Status (online, LB aan/uit/Tibber, fase-detail) | Observations + siteStructure | Werkt; LB **Tibber** wanneer EQ LB uit en Tibber actief (v10.10) |
| Limieten (eMobility, hoofd, ingestelde limiet) | `siteStructure`, `site.state`, circuit-fuse uit embedded data | Werkt wanneer data in observations/siteStructure zit |
| 2 compacte tegels | Status + Vermogen | Afgerond sinds v10.9.1 |

### Wat HTTP 403/405 blokkeert (normaal voor veel accounts)

Deze optionele probes falen vaak met **403 Forbidden** of **405 Method Not Allowed**. Sinds v10.9.31 alleen zichtbaar op **Debug** (Mode6); geen actie nodig.

| Endpoint | HTTP | Gevolg |
|----------|------|--------|
| `/equalizers/{id}/state` | 403 | Plugin cached 403 (5 min), valt terug op observations + siteStructure |
| `/cloud-loadbalancing/equalizer/{id}/…` | 403 | Geen LB-config uit cloud API; limiet uit andere bronnen |
| `/equalizers/{id}/loadbalancing/…` | 403 | Idem |
| `/equalizers` (lijst) | 403 | Discovery via `/accounts/products` i.p.v. lijst-endpoint |
| `/sites/{id}/circuits` | 405 | Circuit-lijst niet via deze methode; embedded circuits in site/state gebruikt |

**Eerlijk:** LB-configuratie en surplus-energy via Easee cloud-loadbalancing-API werkt **mogelijk nooit** voor dit account — dat is een account-/rechtenlimiet van Easee, geen plugin-bug. De Status-tegel toont LB **Uit** wanneer de API geen actieve LB-state levert (ook als de app iets anders suggereert).

### Stap 2+ — realistische vervolg (indicatief)

Alleen zinvol als Easee API-toegang verbetert of bugreports nieuwe haakjes tonen:

- Betere fuse-limiet uit `siteStructure` wanneer cloud-loadbalancing 403 blijft (geen fantasy LB-config-tegel)
- Verfijning LB-weergave wanneer observations 230–232 wél data geven maar state-endpoint 403 blijft
- Verdere stabilisatie op basis van [Issues](https://github.com/rleunk/easee-domoticz/issues)

**Niet gepland** (zolang API 403/405 blijft): LB-config lezen/schrijven via API, aparte cloud-LB-tegel, surplus-energy automatisering in Domoticz.

## Toekomst (indicatief, geen planning)

- Verdere stabilisatie op basis van bugreports via [Issues](https://github.com/rleunk/easee-domoticz/issues)
