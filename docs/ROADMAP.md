# Roadmap

Kort overzicht — **v1** ontwikkeling op branch `v1`; legacy **v10.11.6-stable** blijft productie op `main`. Zie [STABLE.md](../STABLE.md) en [VERSIONING.md](../VERSIONING.md).

## v1 (branch `v1`) — indicatief

| Versie | Status | Inhoud |
|--------|--------|--------|
| **0.6.1** | **Huidig pre-release** | Status-tegel toont actieve prijsbron (Geen/Handmatig/Tibber/ENTSO-E/EnergyZero) |
| **0.6.0** | Afgerond | Prijsbron **EnergyZero** — publieke NL uurprijzen, geen token |
| **0.5.0** | Afgerond | Prijsbron **ENTSO-E** — day-ahead spot NL + toeslagen (Mode24–27) |
| **0.4.1** | Afgerond | Thuisbatterij-labels (generiek i.p.v. Sessy) |
| **0.4.0** | Afgerond | Handmatig Dal/piek; P1/zon/thuisbatterij hints (Mode20–23) |
| **0.3.0** | Afgerond | Handmatig Dag/nacht; Energieprijs UI-reorder |
| **0.2.1** | Afgerond | BesteLadenHours fix; parameter-volgorde |
| **0.2.0** | Afgerond | Prijsbron Geen/Handmatig/Tibber; `pricing/` end-to-end |
| **0.1.0** | Afgerond | Scaffold; Tibber-only runtime gelijk aan v10.11.6-stable |
| **1.0.0** | Gepland | Eerste publieke stable v1 — checklist [RELEASE_1.0.0.md](RELEASE_1.0.0.md) |

### Prijsbronnen (v0.6.1)

| Prijsbron | Mode | Token / config |
|-----------|------|----------------|
| Geen | Mode9 | — |
| Handmatig | Mode9 + Mode10–19 | Vast / Dag-nacht / Dal-piek |
| Tibber | Mode9 + Mode7 | Tibber PAT |
| ENTSO-E | Mode9 + Mode24–27 | ENTSO-E API token (na e-mail goedkeuring) |
| EnergyZero | Mode9 | Geen token (`api.energyzero.nl`) |

## Afgerond — v10.11.x stable (legacy, 2026-06)

- **v10.11.0** — Compacte UI: **11 tegels** (2 laders + EQ + Tibber). Merge *Kosten & Samenvatting* + *Dagrapport* → **Dag overzicht**; *Totaal & Sessie* → **Laden**; *Kosten (Sessie/Dag)* → **Status**.
- **v10.11.1** — Fix deprecated-tegel `Used=0`-update; user-testing afgerond → **v10.11.1-stable**.
- **v10.11.2** — Status-timer pauze-fix; user-testing afgerond → **v10.11.2-stable**.
- **v10.11.4** — truthy()-fix laad-timer → **v10.11.4-stable**.
- **v10.11.6** — Dag overzicht-migratie fix (`Device.Update`); user-testing afgerond → **v10.11.6-stable** (aanbevolen productie-baseline).
- **v10.11.5** — Dag overzicht-migratie + idle timer **00:00**; → **v10.11.5-stable** (rollback-baseline; readonly-fout op nieuwere Domoticz).

## Afgerond — v10.10.x stable (2026-06)

- **v10.10.0** — Tibber kwartierprijzen, Dagrapport, laadhints, configureerbaar Beste laden, **16 tegels** met Tibber (v10.10.x).
- **v10.10.1** — API-timeout crasht hardware-thread niet meer.
- **v10.10.2–v10.10.8** — Sessie-kWh, timer, kosten, EQ fase-weergave; Totaal & Sessie numerieke Custom sValue; sessie-kWh cap op dagtotaal.
- **Stable release** — tag `v10.10.8-stable` (rollback-baseline sinds v10.11.1).

## Afgerond — v10.10.0 (2026-06-19)

- **Dagrapport-tegel** — kWh, €, laaduren, goedkoopste kwartier (Tibber). *(Samengevoegd in **Dag overzicht** sinds v10.11.)*
- **Laadhints** — dynamische hints op Status-tegel (Tibber + load balancing).
- **Beste laden** — configureerbaar venster (Mode8).
- **16 tegels** — volledige layout met Tibber (2 laders + EQ).

## Gepland / onderzoek

- **1.0.0-stable** — volgende milestone; soak test op productie-Domoticz, daarna tag + forum post — zie [RELEASE_1.0.0.md](RELEASE_1.0.0.md)
- **Equalizer fase-detail** — verdere verfijning LB-weergave
- **Domoticz Energy-tegel icoon-beperking** — documentatie/alternatief
- **API rate limit** — adaptieve poll-interval bij 429

## Afgerond — prijsbronnen v1 (2026-06)

- **ENTSO-E (0.5.0)** — day-ahead spot + toeslagen; token via e-mail naar transparency@entsoe.eu; backup in `easee_state.json` — **getest 2026-06-29**
- **EnergyZero (0.6.0)** — token-vrij; publieke uurprijzen — getest
- **Geen / Handmatig / Tibber** — sinds 0.2.0–0.4.0 — getest

## Testomgeving Richard

2× Charge Lite, 1× Equalizer — **11 actieve tegels + LoadBal** (zie [CONFIGURATION.md](CONFIGURATION.md#verwachte-tegels-referentie)).

| Datum | Wat |
|-------|-----|
| 24-06-2026 | v10.11.0 tegel-merge goedgekeurd |
| 20-06-2026 | v10.10.8-stable sessie-kWh fixes |
| 26-06-2026 | v10.11.6 Dag overzicht-migratie |
| 27-06-2026 | v1 **0.2.0–0.6.0** prijsbronnen (incl. EnergyZero) |
| 29-06-2026 | v1 **0.5.0 / 0.6.1** ENTSO-E bevestigd (token + backup) |

**Soak test:** v0.6.1 op branch `v1` — ongoing tot 1.0.0-stable tag.

## Oudere milestones (samenvatting)

| Periode | Thema |
|---------|-------|
| v10.9.x | Modulaire refactor, custom iconen v2, Equalizer 2-tegel, kosten-fixes |
| v10.8.x | Tibber integratie, laadhints prototype |
| v10.7.x | State persistence, load balancing |
| v10.6.x | Module split (13 Python-bestanden) |

Zie [CHANGELOG.md](../CHANGELOG.md) voor volledige release-notes.
