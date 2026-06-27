# Roadmap

Kort overzicht — **v1** ontwikkeling op branch `v1`; legacy **v10.11.6-stable** blijft productie op `main`. Zie [STABLE.md](../STABLE.md) en [VERSIONING.md](../VERSIONING.md).

## v1 (branch `v1`) — indicatief

| Versie | Status | Inhoud |
|--------|--------|--------|
| **0.1.0** | Scaffold (afgerond) | Versienummering, docs, `pricing/` skeleton, Prijsbron-parameter (stub Geen/Handmatig) |
| **0.2.0** | Afgerond | Prijsbron Geen (kosten uit) en Handmatig (vast tarief); Tibber via `pricing/` refactor |
| **0.3.0** | Afgerond | Handmatig Dag/nacht |
| **0.4.0** | Afgerond (huidig) | Handmatig Dal/piek; P1/zon/Sessy hints |
| **1.0.0** | Gepland | Eerste publieke stable v1 |

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

- **Equalizer fase-detail** — verdere verfijning LB-weergave
- **Domoticz Energy-tegel icoon-beperking** — documentatie/alternatief
- **API rate limit** — adaptieve poll-interval bij 429

## Testomgeving Richard

2× Charge Lite, 1× Equalizer, Tibber (Mode7) — **11 actieve tegels** (zie [CONFIGURATION.md](CONFIGURATION.md#verwachte-tegels-referentie)). v10.11.0 tegel-merge getest en goedgekeurd (24-06-2026); v10.10.8-stable sessie-kWh fixes getest (20-06-2026); v10.11.6 Dag overzicht-migratie fix getest (26-06-2026).

## Oudere milestones (samenvatting)

| Periode | Thema |
|---------|-------|
| v10.9.x | Modulaire refactor, custom iconen v2, Equalizer 2-tegel, kosten-fixes |
| v10.8.x | Tibber integratie, laadhints prototype |
| v10.7.x | State persistence, load balancing |
| v10.6.x | Module split (13 Python-bestanden) |

Zie [CHANGELOG.md](../CHANGELOG.md) voor volledige release-notes.
