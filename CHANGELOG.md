# Changelog

Alle belangrijke wijzigingen aan dit project worden hier gedocumenteerd.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/).

> **v1 changelog** start bij **0.1.0** op branch `v1`. Legacy v10-geschiedenis staat onder de separator **Legacy v10** hieronder.

## [Unreleased]

## [0.2.1] — 2026-06-27

### Fixed
- **Beste laden venster (uren)** — hardwareveld gebruikt nu `BesteLadenHours` i.p.v. `Extra` (Domoticz `Extra` = plugin-key `EaseeCloudAutoDiscoveryV1000`, waardoor UI *EaseeCloudA* toonde)
- **Parameter-volgorde** — Mode7/Mode8 vóór Prijsbron (Mode9) en Tarief (Mode10); nieuwe params aan het einde van de Tibber-groep (geen verschuiving t.o.v. v10.11.6)
- **Migratie** — leest legacy numerische `Extra` of state-backup; negeert plugin-key / non-numeric waarden; default 3, range 1–12
- Dubbele functiedefinities in `easee_helpers.py` verwijderd

### Notes
- Na upgrade: controleer **Beste laden venster (uren)** (default 3) en Tibber-token indien nodig opnieuw invullen

## [0.2.0] — 2026-06-27

### Added
- **Prijsbron Geen** — geen Tibber API; kosten uit; *Dag overzicht* toont kWh + laaduren; geen sessie/dag-€ op Status; geen *Beste laden*-tegel
- **Prijsbron Handmatig** — vast tarief via hardware **Tarief €/kWh (Mode10)**, default 0,25; kostenberekening kWh×tarief; *Beste laden* toont *Vast tarief €X/kWh*
- **`pricing/ui.py`** — provider-aware UI-helpers (tarief, emoji, laadhints, goedkoopste venster)
- **`easee_helpers.pricing_enabled()`** — kosten actief bij Tibber+token of Handmatig
- **`easee_helpers.manual_rate()`**, **`dag_overzicht_enabled()`**, **`beste_laden_enabled()`**

### Changed
- Kosten-accumulatie en UI via `pricing.get_provider()` / `pricing_ui` i.p.v. directe `tibber_pricing`-aanroepen
- `ManualPricingProvider` en `NoPricingProvider` volledig geïmplementeerd
- Startup-log: *Prijsbron Geen — kosten uitgeschakeld*; Handmatig toont ingesteld tarief
- Versie **0.2.0** in `easee_constants.py` en plugin-metadata

### Notes
- **Prijsbron Tibber** (default) — ongewijzigd t.o.v. 0.1.0 / v10.11.6-stable bij token in Mode7

## [0.1.0] — 2026-06-27

### Added
- **v1 ontwikkelingslijn** op branch `v1` — scaffold; runtime-gedrag gelijk aan **v10.11.6-stable**
- [VERSIONING.md](VERSIONING.md) — beleid v1 vs legacy v10 (geen hernummering v10 → 0.10.x)
- `pricing/` module-skeleton: `base`, `none`, `manual`, `tibber`, `factory`
- Hardware-parameter **Prijsbron** (Mode9): `Geen|Handmatig|Tibber` (default Tibber)

### Notes
- Prijsbron **Geen** — log bij start: *kosten uitgeschakeld (0.2.0)*
- Prijsbron **Handmatig** — log bij start: *nog niet geïmplementeerd (0.2.0)* — geen crash
- Tibber-kosten blijven werken bij default (Prijsbron Tibber + token in Mode7)

---

# Legacy v10

## [10.11.6] — 2026-06-26

### Stable
- **v10.11.6-stable** — huidige aanbevolen productie-baseline (Dag overzicht-migratie fix). Tag `v10.11.5-stable` bewaard op v10.11.5-commit. Zie [STABLE.md](STABLE.md).

### Opgelost
- **Dag overzicht-migratie faalde met `readonly attribute`** — v10.11.5 schreef `dev.Name` / `dev.DeviceID` direct; op nieuwere Domoticz zijn die velden readonly. `migrate_dag_overzicht_core_tile()` hernoemt nu via `Device.Update(Name=…, Used=1, …)`; legacy DeviceID (`EASEE_CORE_COSTS` / `EASEE_CORE_DAG`) blijft behouden en lookup vindt de tegel via legacy naam, legacy DeviceID en canonieke naam.

### Upgrade
- Van **v10.11.5**: `git pull` (of `git checkout v10.11.6-stable`) + hardware herstarten. Tegelnaam wordt automatisch gecorrigeerd.
- Van **v10.11.5-stable** / **v10.11.4-stable**: `git checkout v10.11.6-stable` + hardware herstarten.

## [10.11.5] — 2026-06-26

### Stable
- **v10.11.5-stable** — huidige aanbevolen productie-baseline (Dag overzicht-migratie + idle timer **00:00**). Tag `v10.11.4-stable` bewaard op v10.11.4-commit. Zie [STABLE.md](STABLE.md).

### Opgelost
- **Legacy tegel blijft *Kosten & Samenvatting* heten** — bij upgrade van v10.10.x werd de tegel wel bijgewerkt maar niet hernoemd naar **Dag overzicht** (DeviceID + naam). `migrate_dag_overzicht_core_tile()` hernoemt/repurposet legacy *Kosten & Samenvatting* / *Dagrapport* naar **Easee - Dag overzicht**; dubbele tegels krijgen `Used=0`.
- **Status-timer toont laatste sessieduur bij *Geen auto*** — idle laders (Geen auto, Gereed, …) tonen nu **00:00** op de Status-tegel; alleen actief laden (> 50 W) toont een lopende timer. *Laatste sessie* € blijft zichtbaar.

### Upgrade
- Van **v10.11.4**: `git pull` (of `git checkout v10.11.5-stable`) + hardware herstarten. Tegelnaam wordt automatisch gecorrigeerd.
- Van **v10.11.2-stable** / **v10.11.4-stable**: `git checkout v10.11.5-stable` + hardware herstarten.

## [10.11.4] — 2026-06-25

### Stable
- **v10.11.4-stable** — bewaarde baseline op v10.11.4-commit (truthy-fix); superseded door v10.11.5-stable.

### Opgelost
- **`truthy()` TypeError in laad-timer** — `sync_charging_timer()` en state-normalisatie riepen `easee_helpers.truthy(value)` aan zonder verplichte `plugin`-parameter; Domoticz crashte met `missing 1 required positional argument: 'value'`.

### Upgrade
- Van **v10.11.3**: `git pull` (of `git checkout v10.11.4`) + hardware herstarten.

## [10.11.3] — 2026-06-25

### Opgelost
- **Hardware-thread stopt stil (v10.11.2)** — onverwachte uitzonderingen in de heartbeat/poll-loop (o.a. `sync_charging_timer()`, ontbrekende `charging_active` na upgrade, ongeldige `session_start_ts`) kunnen de Domoticz-thread beëindigen zonder plugin-regels in het log. Elke heartbeat-stap (login, sync, discovery, poll per lader/EQ, UI, state) heeft nu een eigen `try/except` met **`heartbeat exception: …`** op ERROR-niveau; de thread blijft draaien.
- **Laad-timer state na upgrade** — `charging_active` en sessie-flags worden genormaliseerd bij state-load en eenmalige migratie (`migrate_charging_timer_state`); `compute_duration_text()` / `session_elapsed_hours()` tolereren corrupte timestamps.

### Upgrade
- Van **v10.11.2**: `git pull` (of `git checkout v10.11.3`) + hardware herstarten. Bij herhaalde thread-fouten: zoek in het log naar `heartbeat exception:` voor de exacte oorzaak.

## [10.11.2] — 2026-06-24

### Stable
- **v10.11.2-stable** — huidige aanbevolen productie-baseline (Status-timer pauze-fix + compacte 11-tegel UI). Tags `v10.11.1-stable` en `v10.10.8-stable` blijven bewaard voor rollback. Zie [STABLE.md](STABLE.md).

### Opgelost
- **Status-timer blijft lopen bij pauze (Wacht op start, 0 W)** — laadtijd op de Status-tegel liep door zolang de Easee-sessie open stond, ook zonder actief vermogen. Timer telt nu alleen tijdens laden (> 50 W); bij pauze **00:00**, bij hervatting opnieuw vanaf nul. Sessie-kWh op **Laden** en kosten blijven intact.

### Upgrade
- Van **v10.11.1**: `git checkout v10.11.2-stable` (of `git pull` op `main`) + hardware herstarten.

## [10.11.1] — 2026-06-24

### Stable
- **v10.11.1-stable** — was aanbevolen productie-baseline tot v10.11.2-stable (compacte 11-tegel UI). Tag bewaard voor rollback. Zie [STABLE.md](STABLE.md).

### Opgelost
- **Deprecated tegels: `Failed to parse parameters` / `missing required argument 'nvalue'`** — `mark_device_unused()` riep `Update(Used=0)` aan zonder `nValue`/`sValue` (zelfde regressie als v10.9.6 icon-fix). Verouderde tegels (*Dagrapport*, *Kosten & Samenvatting*, *Totaal & Sessie*, *Kosten (Sessie/Dag)*) krijgen nu éénmalig `Update(nValue=…, sValue=…, Used=0)` met huidige waarden; reeds `Used=0` wordt overgeslagen.

### Upgrade
- Van **v10.11.0**: `git pull` + hardware herstarten. Geen handmatige tegel-actie nodig; logspam bij deprecated tegels verdwijnt.
- Van **v10.10.x**: `git checkout v10.11.1-stable` (of `git pull` op `main`) + hardware herstarten. Oude tegels worden verborgen (`Used=0`); sessie-kWh staat op **Laden** (Description), kosten op **Status** en **Dag overzicht**.

## [10.11.0] — 2026-06-24

### Gewijzigd — compacte tegels (16 → 11 bij 2 laders + EQ + Tibber)
- **Dag overzicht** — kern-tegel merge van *Kosten & Samenvatting* + *Dagrapport*: kWh vandaag, € vandaag, laaduren, goedkoopste kwartier/uur, tarief, energy/belasting-split.
- **Laden** (per laadpaal) — merge met *Totaal & Sessie*: Energy-tegel (243/29) ongewijzigd voor grafieken (`sValue` = `vermogen;counter_wh`); sessie/vandaag/totaal kWh in `Description`.
- **Status** (per laadpaal) — merge met *Kosten (Sessie/Dag)*: laadtoestand, timer, laadhint (Grid Rewards / duur tarief) + sessie € + dag € in één regel.

### Verouderd (niet verwijderd — veiligheid Domoticz)
- Kern: **Kosten & Samenvatting**, **Dagrapport** — niet meer aangemaakt/bijgewerkt; bestaande tegels krijgen `Used=0` (INFO-log eenmalig).
- Per laadpaal: **Totaal & Sessie**, **Kosten (Sessie/Dag)** — idem; data staat op **Laden** resp. **Status**.

### Upgrade
- `git pull` + hardware herstarten. Oude tegels blijven staan maar worden verborgen (`Used=0`); handmatig verwijderen mag.

### Stable (promoted in v10.11.1)
- **v10.11.1-stable** — user-testing afgerond; zie [10.11.1] stable-sectie.

## [10.10.8] — 2026-06-20

### Stable
- **v10.10.8-stable** — was aanbevolen productie-baseline tot v10.11.1-stable; tag bewaard voor rollback. Tags `v10.11.1-stable` en `v10.9.32-stable` blijven eveneens bewaard. Zie [STABLE.md](STABLE.md).

### Opgelost
- **Sessie-kWh absurd hoog (bijv. 34 kWh bij 12,7 kWh vandaag)** — `display_session_kwh()` nam het maximum van `session_kwh`, `day_delta`, `power×timer` en API; een verouderde API-starttijd (sessie vanaf ochtend) gaf `power×timer` ≫ `day_kwh`. Mid-session herstart zette `session_start_day_kwh` op `0` of `unstick` forceerde baseline `0`, waardoor `day_delta` of ongecapped timer won. Fix: voorkeur voor `day_kwh − session_start_day_kwh` bij geldige baseline; `power×timer` alleen als schatting ≤ `day_kwh`; `display_kwh = min(display_kwh, day_kwh)`; mid-session baseline via `day_kwh − timer×vermogen` (nooit `0`). Garage 3,3 vs dag 2,7 wordt ook gecapped. v10.10.7 numerieke `sValue` blijft intact. Totaal & Sessie INFO-log → DEBUG.

## [10.10.7] — 2026-06-20

### Opgelost
- **Totaal & Sessie header blijft 0 kWh (v10.10.4–6)** — echte oorzaak: Domoticz Custom Sensor (243/31) toont de tegel-header uit **numerieke `sValue`**, niet uit `nValue`. De plugin stuurde emoji-tekst (`🔋 Deze sessie: 2.573 kWh | …`) in `sValue`; Domoticz kon dat niet parsen → header `0 kWh`. **Totaal kWh** werkte wel (sValue `"4075"`). Fix: `_custom_kwh_svalue()` zet numerieke sValue; detailtekst in `Description`. INFO-log per poll bij Totaal & Sessie-update; WARNING als tegel niet gevonden. **`track_session_kwh_zero_polls`** had omgekeerde logica in v10.10.6 (reset bij 0 i.p.v. increment) — gecorrigeerd.

## [10.10.6] — 2026-06-20

### Opgelost
- **Totaal & Sessie header blijft 0 kWh na herstart (v10.10.5)** — `maybe_recalibrate_session_start_day_kwh()` had een 2-minuten gate na herstart en liep niet bij delta >0,001 kWh; `session_kwh_zero_warned` blokkeerde INFO-log na eerdere sessie; display-fallback gebruikte geen `day_kwh`-vloer terwijl CustomkWh-header `int(round(kWh))` waarden <0,5 kWh als 0 toont. Baseline-repair via `unstick_session_day_baseline()` (geen tijdsgate, stuck-detectie); `display_session_kwh()` deelt één waarde voor header én sValue (vloer `day_kwh` wanneer header 0 zou zijn); API-starttijd hersteld bij resume; WARNING na 3 polls; migratie reset stuck `session_start_day_kwh` bij actieve sessie.

## [10.10.5] — 2026-06-20

### Opgelost
- **Totaal & Sessie header blijft 0 kWh (v10.10.4 regressie)** — `session_start_day_kwh` kon gelijk aan `day_kwh` worden vastgezet (baseline delta altijd 0) wanneer `session_start_ts` pas in dezelfde poll op *now* werd gezet vóór de baseline-berekening, of bij mis-detectie als nieuwe sessie mid-charge. Baseline gebruikt nu API-starttijd vóór clock-fallback; stuck baseline wordt direct gecorrigeerd via `maybe_recalibrate_session_start_day_kwh()`; power×timer-fallback in `resolve_session_kwh()`; CustomkWh `nValue` volgt weer `int(round(kWh))` zoals Totaal kWh (Options-dict parsing). INFO-log eenmalig bij sessie-kWh=0 terwijl `day_kwh>0` en laden actief.

## [10.10.4] — 2026-06-20

### Opgelost
- **Totaal & Sessie header blijft 0 kWh tijdens laden** — `resolve_session_kwh()` gebruikte lifetime-delta (`session_start_kwh` = `total_kwh`, terwijl lifetimeEnergy tijdens een actieve sessie niet beweegt) en vermogensintegratie die na upgrade/herstart op 0 stond. Sessie-kWh volgt nu dezelfde `day_kwh`-tracker als de Laden-tegel via `session_start_day_kwh`; mid-session upgrade schat baseline uit timer×vermogen. `sessionEnergy=0` uit API wordt genegeerd; CustomkWh-header `nValue` volgt device-Options-schaal (`Custom: 1;kWh` → `int(round(kWh))`).

## [10.10.3] — 2026-06-20

### Opgelost
- **CustomkWh Update()-fout na v10.10.2** — `Totaal & Sessie` en `Totaal kWh` gaven `Failed to parse parameters` / `TypeError: 'float' object cannot be interpreted as an integer` doordat `nValue` als float werd doorgegeven. Alle Custom/kWh-updates gebruiken nu `int()`; sessie-header via `nvalue=int(round(session_kwh * 10))` (1 decimaal, conform `Custom: 1;kWh`).

## [10.10.2] — 2026-06-20

### Opgelost
- **Totaal & Sessie toont 0 kWh** — CustomkWh-tegel kreeg `nValue=0`; header toont nu sessie-kWh (API → lifetime-delta → vermogen×tijd fallback).
- **Laadtimer blijft 00:00** — `session_start_ts` wordt gezet wanneer laden actief is maar timestamp ontbrak (persisted state).
- **Kosten sessie > dag / stale sessiekosten** — `is_session_resume` gebruikte achtergebleven `session_cost_total` na sessie-einde; sessiekosten worden na afloop gewist; dagwisseling reset sessiekosten bij doorlopend laden.
- **Energy €0,00 | Belasting €X** — Tibber-prijs normaliseert energy/tax wanneer energy ontbreekt (`energy = total − tax`).
- **EQ Fase-data vs Stroom contradictie** — LB-fase regel valt terug op gemeten L1/L2/L3-stroom wanneer available/equalized keys ontbreken.

## [10.10.1] — 2026-06-20

### Opgelost
- **Hardware-thread stopt bij API-timeout** — Netwerk/timeouts tijdens discovery of polling beëindigen de Domoticz-thread niet meer. `api_get` vangt connectie/timeouts af (30s timeout), discovery behoudt de bestaande cache bij fouten, en `onHeartbeat` heeft extra foutafhandeling zodat de poll-loop blijft draaien.

## [10.10.0] — 2026-06-19

### Toegevoegd
- **Dagrapport-tegel** — dagelijkse samenvatting: kWh, €, laaduren, goedkoopste kwartier/uur (Tibber).
- **Laadhints op Status-tegel** — inferentie *Laden bij duur tarief* / *Waarschijnlijk Grid Rewards* uit vermogen + Tibber-prijs.
- **Status "Tibber stuurt"** — globale Status wanneer EQ load balancing uit is maar er geladen wordt via Tibber.
- **Tibber kwartierprijzen** — `priceInfo(resolution: QUARTER_HOURLY)` met fallback naar uurprijzen; gebruikt voor kosten en Beste laden.
- **Beste laden configureerbaar** — vensterlengte via hardwareveld *Beste laden venster (uren)* (Extra, default 3).
- **Teruglevering hint** — Vermogen-tegel toont *Teruglevering actief* bij export > 0 W.

### Gewijzigd
- **Totaal & Sessie** — duidelijker onderscheid *Deze sessie* vs *Vandaag* vs totaal.
- **Equalizer Status** — bij LB uit + Tibber actief: *Load balancing: Tibber* i.p.v. foutachtig *Uit*; betere fallback-labels (n/b, nog niet beschikbaar).
- **Verwachte tegels** — 16 met Tibber (was 15); tag `v10.9.32-stable` bewaard.

## [10.9.32] — 2026-06-19

### Gewijzigd
- **Optionele API 404/429 → DEBUG** — Geen actieve sessie (`/chargers/…/sessions/ongoing` HTTP 404) en charger rate limit (429 op optionele charger-endpoints, o.a. ongoing/config) worden niet meer als WARNING gelogd; plugin valt terug op state/observations. WARNING blijft voor onverwachte optionele fouten en kritieke endpoints (o.a. `/chargers/{id}/state`).

## [10.9.31] — 2026-06-19

### Gewijzigd
- **Optionele API 403/405 → DEBUG** — Verwachte mislukkingen op equalizer state, cloud-loadbalancing, `/equalizers` en site circuits worden niet meer als WARNING gelogd; HTTP 429 blijft WARNING.
- **Documentatie** — ROADMAP (Equalizer stap 1 vs 2+, Tibber slim laden gesloten), TROUBLESHOOTING (normale 403/405), README-mockups verfijnd.

## [10.9.30] — 2026-06-19

### Bugfix
- **Tibber-token (Mode7) blijft bewaard** — Domoticz wist wachtwoordvelden vaak bij hardware-opslaan of plugin-update; zonder opnieuw invullen verscheen `Tibber uit (Mode7 leeg)`. Token wordt nu gekopieerd naar `easee_state.json` (`tibber_token_backup`); bij lege Mode7 valt de plugin terug op die backup. Tokenwaarde wordt nooit gelogd.

## [10.9.29] — 2026-06-19

### Gewijzigd
- **Logging opgeschoond** — diagnostische regels uit troubleshooting-periode terug naar DEBUG: per-poll `Poll voltooid`, succesvolle `Kosten-tegel bijgewerkt` / `Kern-tegel bijgewerkt`, siteStructure-dumps, per-tegel icon-updates. WARNING/ERROR bij mislukte lookup of update blijven.
- **Icon-startup** — volledige icon-diagnostiek maximaal 1× per plugin-start (geen dubbele dump bij onStart + initiële sync); `image_ids: X/13 sets` en samenvatting blijven INFO.
- **Documentatie** — README/INSTALL/docs bijgewerkt naar v10.9.28 stable testing + v10.9.29; logniveaus uitgelegd voor niet-technische gebruikers; Tibber (Mode7) als vereiste voor kosten-tegels benadrukt.

## [10.9.28] — 2026-06-19

### Bugfix
- **Domoticz init toonde 10.9.26 terwijl logs 10.9.27 zeiden** — `plugin.xml` `<Version>` / `<name>` stond nog op 10.9.26; `PLUGIN_VERSION` in `easee_constants.py` was al 10.9.27. Alle versievelden gesynchroniseerd; startup-log meldt nu expliciet `Plugin v{PLUGIN_VERSION} gestart`.
- **Kosten-tegels vast op €0,00 / timestamp 00:04** — Stale `sessionEnergy` uit `/state` werd nog gebruikt als `/sessions/ongoing` leeg terugkwam (geen actieve sessie in API maar wel laden op vermogen). `prev_session_kwh` wordt nu alleen gezaaid bij echte ongoing-data; `nValue` wisselt elke poll (ook buiten sessie) zodat timestamp meeloopt; lookup gebruikt `charger_names` + naam-scan zonder display; aparte `cost_track_version`-migratie reset `prev_session_kwh`.
- **State-/kosten-migratie bij upgrade** — State wordt direct na migratie opgeslagen; aparte `cost_track_version`-migratie (log: *Kosten-tracking gemigreerd*) reset `prev_session_kwh` zonder dag-kWh opnieuw te wissen.

## [10.9.27] — 2026-06-19

### Bugfix
- **Negatieve Vandaag kWh (v10.9.26-regressie)** — Domoticz berekent *Vandaag* als `Counter − Counter@middernacht`. v10.9.26 stuurde dag-only Wh (~3 kWh) terwijl Domoticz de middernacht-baseline nog op lifetime stond (~2718 kWh) → negatieve *Vandaag* (~−2715 kWh). Counter is weer **middernacht-baseline + dag-Wh** (lifetime-stijl); dagtracking via vermogensintegratie blijft behouden.
- **Kosten blijven €0,00 tijdens laden** — kWh-delta voor kosten geeft tijdens actief laden nu voorrang aan `day_track`/vermogen×tijd boven stale `lifetimeEnergy`; stale `sessionEnergy` uit `/state` wordt niet meer als `prev_session_kwh` gezaaid zonder `/sessions/ongoing`.
- **State-migratie bij upgrade** — eenmalige reset bij upgrade vanaf v10.9.26 (log: *State gemigreerd naar 10.9.27 lifetime Counter*).

## [10.9.26] — 2026-06-19

### Bugfix
- **Vandaag kWh ~3 kWh i.p.v. werkelijk dagverbruik** — `sessionEnergy` in `/state` bleef ~3 kWh staan (gisteren); die waarde schoof in `day_kwh` via `lifetimeEnergy`-sprongen tijdens laden. Ongoing-session gaat vóór state; tijdens laden telt vermogen×tijd i.p.v. lifetime-sprongen. Domoticz Counter is nu **dag-only Wh** (0 na middernacht), niet meer lifetime-baseline + dag.
- **Kosten-tegels vast op €0,00 / timestamp 00:04** — Verouderde `sessionEnergy` werd als `prev_session_kwh` gezet (delta bleef 0); tegel-Update ververste timestamp niet bij ongewijzigd bedrag. `prev_session_kwh` wordt niet meer gevoed bij sessie-hervatting met stale API-waarde; kosten vallen terug op `day_track`/vermogen. `nValue` wisselt elke poll zodat timestamp meeloopt; INFO-log per kosten-update.
- **State-migratie bij upgrade** — Dag-kWh-teller en `prev_session_kwh` worden eenmalig gereset bij upgrade naar v10.9.26 (log: *State gemigreerd*).

## [10.9.25] — 2026-06-19

### Bugfix
- **Vandaag kWh blijft gisteren tonen na middernacht** — Bij dagwisseling werd `display_wh` niet gereset; de monotonic guard blokkeerde een daling, waardoor *Vandaag* op de Laden-tegel het vorige dagtotaal bleef tonen (~1,8 kWh i.p.v. ~0). `display_wh` wordt nu bij middernacht opnieuw gezet en de monotonic guard wordt één poll overgeslagen.

## [10.9.24] — 2026-06-19

### Bugfix
- **Vandaag kWh op Laden-tegel klopt niet (midnight / stale sessionEnergy)** — Domoticz berekende *Vandaag* uit `lifetimeEnergy`, dat tijdens een sessie vaak niet beweegt; bij herstart werd verouderde `sessionEnergy` (>0) ten onrechte gezien als “sessie hervatten”, waardoor laadtijd op 00:02 bleef staan terwijl *Vandaag* ~1,8 kWh toonde. De plugin houdt nu een middernacht-baseline bij (`day_baseline_kwh` + vermogensintegratie) en stuurt een dagcumulatief naar de Energy-tegel; *Vandaag* volgt daarmee het werkelijke dagverbruik.
- **Kosten blijven €0,00 + verouderde timestamp op kosten-tegels** — `prev_session_kwh` werd elke poll op stale `sessionEnergy` gezet (delta=0); fallback via dag-tracking (`day_track`) en vermogen×tijd is aangescherpt. Kosten-tegels gebruiken `nValue` tijdens laden zodat Domoticz de timestamp ververst ook als het bedrag nog €0,00 toont (korte sessie / afronding op 2 decimalen).
- **Sessie-hervatting** — alleen na echte plugin-herstart midden in een sessie (opgeslagen `session_start_ts` / kosten), niet op stale `sessionEnergy` alleen; laadtijd komt uit `firstEnergyTransferPeriodStart` / `sessionStart` van `/sessions/ongoing` wanneer beschikbaar.

## [10.9.23] — 2026-06-18

### Bugfix
- **Kosten blijven €0,00 tijdens laden (429 / herstart)** — `sessionEnergy` in `/state` kan verouderd blijven als `/sessions/ongoing` 429 geeft; de plugin gebruikte dan alleen die delta (0) en sloeg `lifetimeEnergy`- en vermogensintegratie-fallback over. Kostenaccumulatie probeert nu achtereenvolgens sessionEnergy → lifetimeEnergy → vermogen×tijd. Bij herstart midden in een sessie worden bestaande sessiekosten behouden en wordt `prev_session_kwh` niet meer op de huidige waarde gezet (geen eeuwig delta=0).
- **Totaal & Sessie toont 0 kWh sessie** — sessie-kWh onder 0,5 kWh werd afgerond naar 0; weergave gebruikt nu 3 decimalen (bijv. `Sessie: 0.310 kWh`).

## [10.9.22] — 2026-06-18

### Bugfix
- **Kosten-diagnostiek na hardware-herstart** — `_COST_*`-sets werden niet gereset bij `onStart()`; na hardware-herstart (zonder volledige Domoticz-restart) verschenen *Kosten-tegel bijgewerkt* / *niet gevonden* niet opnieuw. Sets worden nu gewist bij elke plugin-start.
- **Poll-zichtbaarheid** — `Poll voltooid` is INFO i.p.v. DEBUG, zodat je in normale logs ziet wanneer een poll-cyclus klaar is (handig met 16 laders).

### Gewijzigd
- **Tibber-status bij start** — INFO-regel of Tibber actief is (Mode7) of uit; zonder Tibber worden per-lader kosten-tegels niet bijgewerkt en verschijnen er geen kosten-diagnostiekregels.

## [10.9.21] — 2026-06-18

### Bugfix
- **Kosten-tegels vast (legacy DeviceID)** — v10.9.20 zocht alleen op `cid|label`-hash; oude tegels met naam-gebaseerde DeviceID (`make_device_id`) of hernoemde tegels werden gemist of een ghost-unit kreeg updates. Lookup probeert nu eerst naam/hash-varianten (incl. `short_id Kosten`), daarna pas `EASEE_CHG_`-hash; Tibber-kern-tegels idem.
- **Diagnostiek kosten** — eenmalige INFO/WARNING per sessie wanneer kosten-tegel wordt bijgewerkt of lookup faalt (met lijst geprobeerde DeviceIDs).

## [10.9.20] — 2026-06-18

### Bugfix
- **Kosten-tegel DeviceID (legacy)** — tegels met naam *Kosten (Sessie/Dag)* maar oude DeviceID uit *Kosten* (v9.x/v10.x) werden door v10.9.19 nog niet gevonden als de naam al was hernoemd; lookup probeert nu ook het legacy DeviceID vóór naamlfallback.
- **Kosten-label tijdens laden** — sessielabel op de kosten-tegel gebruikt nu dezelfde `session_active`-logica als Status (vermogen > 50 W), niet alleen de opgeslagen state-vlag.

## [10.9.19] — 2026-06-18

### Bugfix
- **Kosten-tegel (legacy)** — oude per-lader tegels met naam *Kosten* (v9.x/v10.x) werden niet meer bijgewerkt na hernoeming naar *Kosten (Sessie/Dag)*; lookup valt nu terug op legacy namen.

### Docs
- README-dashboardmockup: grijze sterren, multi-line kostentegels, LoadBal-tegel, realistischere verhoudingen (12 demo-tegels).

## [10.9.18] — 2026-06-18

### Gewijzigd
- **EaseeStatusGlobal combo-icoon** — Equalizer-puck iets groter linksonder (46%/50% schaal @48/16 px); laadpaal iets kleiner rechtsboven (70%/72% schaal); overlap behouden met laadpaal bovenop (z-order); **i**-badge ongewijzigd.

### Changed (EN)
- EaseeStatusGlobal combo icon: larger equalizer puck bottom-left, smaller charger top-right, overlap preserved with charger on top; info badge unchanged.

## [10.9.17] — 2026-06-18

### Opgelost
- **Equalizer Vermogen werkt één poll, daarna 0** — Charger-429 op `/sessions/ongoing` zette een globale rate-limit vlag waardoor equalizer observations (`/state/{id}/observations?ids=40,41`) op volgende polls werden overgeslagen terwijl `/equalizers/{id}/state` HTTP 403 blijft (normaal voor dit account). Fix: aparte rate-limit timers per categorie (`charger_rate_limited_until` vs `equalizer_rate_limited_until`); observations draaien tenzij equalizer zelf 429 kreeg. **Sticky power**: laatste geldige import/export blijft op tegel staan bij mislukte poll (DEBUG toont leeftijd).
- **Geen 0 overschrijven** — Mislukte poll (403 state + overgeslagen obs) reset Vermogen niet meer naar 0/0/0 als eerdere poll geldige waarden had.

### Fixed (EN)
- Equalizer power intermittent zero: per-category rate limits (charger 429 no longer blocks equalizer obs); sticky last-good import/export on failed polls; obs always attempted unless equalizer-specific 429.

## [10.9.16] — 2026-06-18

### Opgelost
- **Equalizer Vermogen 0 door API-druk (429)** — Elke heartbeat deed volledige discovery (~6 calls) vóór poll; daarna 2× lader (state+config+ongoing) vóór equalizer state/obs. Bij 429 op `/sessions/ongoing` (Retry-After 110–180s) faalden `/equalizers/{id}/state` en observations stil (`api_get_optional` → `None`). Fix: discovery max 1× per 5 min (10× poll-interval); equalizer vóór laders; state als eerste call; obs overgeslagen na state-429; ongoing/config overgeslagen tijdens rate limit; fuse-probes lichtgewicht via `siteStructure` cache. `api_get_optional` logt nu WARNING met HTTP-status (incl. 429).
- **Observations URL** — Easee observations staan op `https://api.easee.com/state/{id}/observations` (zonder `/api`-prefix). Plugin riep `/api/state/…` aan → HTTP 404 → `obs 40/41 ontbreken | filtered=geen response`. Routing via `DEVICE_STATE_URL` herstelt power/ fase-obs.

### Gewijzigd
- Poll-volgorde: equalizer → laders (state/obs krijgen voorrang boven optionele charger-endpoints).

### Fixed (EN)
- Equalizer power 0 from API rate pressure: throttle discovery, poll equalizer before chargers, prioritize state, skip obs after 429, defer ongoing/config; WARNING logs on optional HTTP failures. Observations routed to correct host path (no /api prefix).

## [10.9.15] — 2026-06-18

### Opgelost
- **Equalizer Vermogen blijft 0/0/0** — Volledige observations-call miste verplichte `ids`-parameter (HTTP 400 → lege response → `beschikbare ids: geen`). State-power wordt nu direct na `/equalizers/{id}/state` geëxtraheerd via alias-scan (`activePowerImport`, `consumptionPower`, …); nul-waarden uit observations overschrijven niet langer ontbrekende power. Hergebruik state-payload in fallback (minder 429). INFO-log bij succes: `power via equalizer.state: import=…W`; bij 0: beschikbare state-keys + obs API-diagnostiek.

### Fixed (EN)
- Equalizer power: fix observations URL (required `ids`), alias-aware state merge, skip zero obs pollution, reuse cached state, diagnostic logging.

## [10.9.14] — 2026-06-18

### Opgelost
- **onHeartbeat crash** — `_power_from_phases` unpackte `phase_voltage_keys()` (3 voltage-aliassen per fase) als `(curr, volt)` paar; nu `zip(phase_current, phase_voltage_keys())`. Traceback toegevoegd aan onHeartbeat-foutlog.

### Fixed (EN)
- Heartbeat unpack regression in phase I×V power fallback; onHeartbeat logs full traceback on error.

## [10.9.13] — 2026-06-18

### Opgelost
- **429 rate limit blokkeerde hardware-thread** — v10.9.12 sliep tot 283s (Easee `Retry-After` header) in `api_get`, waardoor Domoticz meldde *thread ended unexpectedly*. Bij 429 nu fail-fast: WARNING-log en `None`; volgende poll (±30s) probeert opnieuw. Geen `time.sleep` meer in de heartbeat-pad.
- **Ongoing sessions optioneel** — `/chargers/{id}/sessions/ongoing` en config via `api_get_optional`; 429 op die endpoints blokkeert equalizer/charger poll niet meer.

### Fixed (EN)
- HTTP 429 no longer blocks the plugin thread with Retry-After sleep; defer to next heartbeat. Ongoing session endpoint treated as optional.

## [10.9.12] — 2026-06-18

### Opgelost
- **Equalizer Vermogen 0/0/0** — Robuuste fallback-keten voor import/export W: `/equalizers/{id}/state` (primary), dedicated obs 40/41 query, volledige observations, site state scan, fase I×V en cumulatief-delta. Observations met waarde 0/null overschrijven niet langer geldige state-waarden. Observation-id parsing gefixt (int-coercie). INFO-log toont beschikbare observation-ids bij ontbrekende power; DEBUG met detail.
- **429 rate limit** — `api_get` retry met exponential backoff (max 3) bij HTTP 429 op o.a. `/api/chargers`.

### Gewijzigd
- **Icon log spam** — `Icoon OK` regels naar DEBUG; post-sync icon re-apply van 3 naar 1 heartbeat.

### Fixed (EN)
- Equalizer power fallback chain (state → obs 40/41 → site → phase I×V → cumulative rate); smart merge prevents stale zero obs overwriting state; 429 retry with backoff.

## [10.9.11] — 2026-06-18

### Opgelost
- **Equalizer poll na Domoticz-herstart** — Als `initial_sync()` slaagde maar icon-apply of state-save daarna faalde, bleef `sync_done` onwaar. Elke heartbeat herhaalde discovery (charger + equalizer INFO-regels) zonder ooit `poll_all()` te draaien; Vermogen bleef op 0/0/0 tot hardware-item herstart. `sync_done` wordt nu gezet direct na geslaagde `initial_sync()`; icon-apply/state-save blokkeren poll niet meer. `initial_sync_done` voorkomt herhaalde volledige sync-loops.
- **Equalizer power observations** — Fallback naar volledige `/state/{id}/observations` wanneer gefilterde query obs 40/41 (import/export) mist; INFO-log per poll-cycle en bij ontbrekende power-data.

### Fixed (EN)
- Equalizer poll blocked after Domoticz restart when post-initial-sync steps failed before `sync_done=True`; decouple poll gate from icon apply; observation power fallback.

## v10.9.x overzicht (stable testing line)

| Versie | Hoofdthema |
|--------|------------|
| **10.9.28** | Kosten-tegels + Vandaag kWh + Tibber; versies gesynchroniseerd |
| **10.9.27** | Negatieve Vandaag kWh-fix; lifetime Counter |
| **10.9.24–10.9.26** | Dag-kWh middernacht-baseline; kosten timestamp/delta |
| **10.9.19–10.9.23** | Legacy kosten DeviceID; 429/herstart fallback |
| **10.9.18** | Combo-icoon `EaseeStatusGlobal`: EQ groter linksonder, laadpaal kleiner rechtsboven |
| **10.9.17** | Sticky power; per-endpoint rate limit (charger 429 ≠ equalizer blok) |
| **10.9.16** | Discovery-throttle; equalizer vóór laders; observations URL-fix |
| **10.9.15** | Equalizer Vermogen: obs ids-fix, state alias-merge, diagnostiek |
| **10.9.14** | onHeartbeat unpack-fix in fase I×V fallback |
| **10.9.13** | 429 fail-fast (geen thread-blok); ongoing sessions optioneel |
| **10.9.12** | Equalizer Vermogen fallback-keten; 429 retry |
| **10.9.11** | Equalizer poll na Domoticz-herstart; obs 40/41 fallback |
| **10.9.10** | Status combo-icoon alleen globaal; `EaseeStatusGlobal` (13 sets) |
| **10.9.9** | Combo-icoon op Status (later gesplitst in 10.9.10) |
| **10.9.8** | Icon mapping: laadpaal Status → `EaseeStatus`, EQ Vermogen → `EaseeEqualizer` |
| **10.9.3–10.9.7** | Icon loading/apply fixes (zip-pad, plugin-key, `Device.Update` API) |
| **10.9.1** | Equalizer: 2 tegels (Status + Vermogen) |
| **10.9.0** | Equalizer: 3 tegels (vervangen door 2 in 10.9.1) |

Getest met 2× Charge Lite, 1× Equalizer, Tibber. Zie [README.md](README.md).

## [10.9.10] — 2026-06-18

### Opgelost
- **Combo-icoon alleen op globale Status** — Het gecombineerde pictogram (laadpaal + Equalizer-puck + **i**-badge) hoort alleen op *Easee - Status* (`EASEE_CORE_STATUS`). Laadpaal Status-tegels (*Easee - Voordeur - Status*, *Easee - Garage - Status*, `EASEE_CHG_*`) gebruiken weer het laadpaal-only pictogram met **i**-badge (geen EQ-puck). Nieuwe iconenset `EaseeStatusGlobal` voor de globale tegel; `EaseeStatus` terug naar charger-only.

### Fixed (EN)
- Split status icons: `EaseeStatusGlobal` (combo) for global plugin status only; `EaseeStatus` reverted to charger photo + info badge for per-charger status tiles. Updated `image_root()` DeviceID rules; regenerated `Easee_icons_v2.zip` (13 sets) and mini-zips.

## [10.9.9] — 2026-06-18

### Gewijzigd
- **EaseeStatus combo-icoon** — Status-tegel (laadpaal *Easee - Status*) toont nu een gecombineerd pictogram: P-max foto-laadpaal (blauwe LED) + Equalizer-max puck linksonder (40% schaal, subtiele schaduw) + **i**-badge rechtsonder (ongewijzigde badge-stijl). Ontwerp leesbaar op 48 px Domoticz-tegel.

### Changed (EN)
- EaseeStatus icon: charger photo + equalizer puck overlay (bottom-left) + info badge (bottom-right); regenerated `Easee_icons_v2.zip` and `icons/EaseeStatus.zip`.

## [10.9.8] — 2026-06-18

### Opgelost
- **Icon mapping laadpaal vs equalizer** — `EASEE_CHG_*` Status-tegels (bijv. Garage, Voordeur) kregen per ongeluk `EaseeEqualizer` (sinds v10.5.19); nu weer `EaseeStatus` (laadpaal-pictogram). Equalizer *Vermogen* (`EASEE_EQ_*`, bijv. Meterkast) kreeg `EaseeImport`; nu `EaseeEqualizer` (equalizer-puck). Equalizer *Status* blijft `EaseeEqualizer`.

### Fixed (EN)
- Icon mapping: charger Status tiles → `EaseeStatus`; equalizer Vermogen → `EaseeEqualizer` (DeviceID-based rules in `image_root()`).

## [10.9.7] — 2026-06-18

### Opgelost
- **Icon-regressie v10.9.6** — `Device.Update(Image=…)` zonder `nValue`/`sValue` faalt op sommige Domoticz-builds (Debian) met `TypeError: function missing required argument 'nvalue'`. Icon-updates gebruiken nu altijd de huidige tegelwaarden: `Update(nValue=…, sValue=…, Image=…)`.

### Fixed (EN)
- Icon apply regression: always pass current `nValue` and `sValue` with `Image=` on `Device.Update()` (required on some Domoticz builds).

## [10.9.6] — 2026-06-17

### Opgelost
- **Kritische icon-regressie (v10.9.2–v10.9.5)** — `apply_images_to_devices()` riep `Device.Update(UpdateProperties=True)` aan; die parameter bestaat niet in de Domoticz Python API. Alle icon-updates mislukten met `TypeError: 'updateproperties' is an invalid keyword argument`. Iconen worden nu gezet met alleen geldige parameters: `Update(Image=…)`.

### Fixed (EN)
- Icon apply regression: removed invalid `UpdateProperties` kwarg from `Device.Update()`; icon-only updates use `Update(Image=)` only.

## [10.9.5] — 2026-06-17

### Opgelost
- **Kritische icon-bug (1/12 sets)** — `Easee_icons_v2.zip` gebruikte korte `Base`-namen (`EaseeCharger`) zonder plugin-key-prefix. Domoticz Python-plugins laden alleen iconen in de `Images`-dict wanneer `Base` begint met de XML plugin-key (`EaseeCloudAutoDiscoveryV1000`). Zip opnieuw gegenereerd met prefixed bases + per-set folders; extra 12 mini-zips in `icons/` voor betrouwbare `Image().Create()` per set.
- **Per-set fallback** — na master-zip worden ontbrekende sets individueel geladen uit `icons/EaseeCharger.zip` enz.
- **Diagnostiek** — logt nu alle Easee `Images`-keys en volledige `image_ids` mappings (niet alleen samples).

### Gewijzigd
- **Handmatige upload** — verwijder oude Easee custom icons vóór her-upload van `Easee_icons_v2.zip` (Instellingen → Aangepaste pictogrammen) om conflicten met oude short-name bases te voorkomen.

### Fixed (EN)
- Icon zip Base names must start with plugin key for Python `Images` dict; regenerated zip + per-set mini-zips; full diagnostic logging.

## [10.9.4] — 2026-06-17

### Opgelost
- **Zip pad verdubbeling** — `Image().Create()` kreeg het volledige absolute pad; Domoticz voegt zelf `plugin_dir` toe, waardoor het zip-bestand niet gevonden werd (`Error opening zip file`). Alleen nog bestandsnaam (`Easee_icons_v2.zip`); INFO-log toont exact argument aan `Create()`.

### Fixed (EN)
- Domoticz prepends plugin dir to `Image().Create()` path — pass filename only, not absolute path (fixes doubled path on Linux).

## [10.9.3] — 2026-06-17

### Opgelost
- **Icon refresh bug (v10.9.2 regressie)** — dubbele `refresh_images_dict()` overschreef de werkende implementatie; aanroep zonder `plugin_globals` deed niets, waardoor `Images` niet ververst werd en `image_ids` leeg bleef.
- **Zip auto-load op Linux** — `Image().Create()` probeert nu het volledige pad (`/home/root/domoticz/plugins/.../Easee_icons_v2.zip`) naast relatieve bestandsnaam.
- **Icon lookup** — fuzzy match op alle `Images`-keys (case-insensitive, suffix-match) naast vaste kandidaten (`EaseeCharger`, `EaseeCloudAutoDiscoveryV1000EaseeCharger`, …).
- **Timing** — custom iconen worden vóór `initial_sync()` geladen zodat nieuwe tegels meteen `Image=` bij `Device.Create()` krijgen.
- **Update verificatie** — na `Device.Update(Image=…)` wordt gecontroleerd of `Image` daadwerkelijk gewijzigd is; `UpdateProperties` eerst (Domoticz 2024.4+).

### Gewijzigd
- **Startup diagnostiek (INFO)** — zip pad/grootte, `Create()` resultaat, aantal `Images`-keys, Easee-key sample, `image_ids` count + eerste 3 mappings; ERROR met upload-instructie als `image_ids` leeg.
- **Per-tegel icon log** — elke Easee-tegel logt gezet / overgeslagen / mislukt met reden.
- **Status-tegel waarschuwing** — `⚠️ Upload Easee_icons_v2.zip (Instellingen)` zolang iconen ontbreken.

### Fixed (EN)
- Duplicate refresh_images_dict regression; full-path zip Create; fuzzy Images key lookup; icons before initial_sync; UpdateProperties-first with post-update verification; INFO diagnostics and Status tile upload warning.

## [10.9.2] — 2026-06-17

### Opgelost
- **Custom iconen op bestaande tegels** — `Images`-dict wordt na zip-`Create()` ververst; `apply_images_to_devices()` gebruikt `Update(Image=…)` met `UpdateProperties`-fallback (Domoticz 2024.4+); iconen worden opnieuw toegepast na sync en op de eerste 3 heartbeats.
- **Icoon-log per tegel** — INFO-regel `Icoon {naam} -> {icon_set}` bij elke succesvolle toepassing.
- **Legacy Import Energy → Vermogen Text** — oude *Import*-Energy-tegel (bijv. *Meterkast - Import* met W/kWh) wordt verwijderd en opnieuw aangemaakt als Text *Vermogen*; naam met *Import* wordt geforceerd hernoemd.

### Gewijzigd
- **Icon lookup** — dubbele sleutel (`EaseeCharger` / `EaseeCloudAutoDiscoveryV1000EaseeCharger`) blijft actief; alleen Easee-device(s) krijgen icon-updates.

### Documentatie
- Troubleshooting: iconen na reinstall, Energy-tegels (bliksem), handmatige zip-upload.

### Fixed (EN)
- Icons refresh Images dict after zip Create; UpdateProperties fallback; re-apply on 3 heartbeats post-sync; legacy Import Energy tile recreated as Text Vermogen.

## [10.9.1] — 2026-06-17

### Opgelost
- **Custom iconen na hardware remove/re-add** — `apply_images_to_devices()` draait nu opnieuw na `initial_sync()` zodat nieuw aangemaakte tegels (Status, Vermogen) meteen het juiste pictogram krijgen; WARNING in log als `image_ids` leeg blijft.
- **Icon zip diagnostiek** — mislukte of ontbrekende zip → WARNING i.p.v. INFO.

### Gewijzigd
- **Equalizer: 2 tegels** — **Status** + **Vermogen** (Text) per Equalizer; import/terug/netto W en vandaag import/netto kWh op één **Vermogen**-tegel.
- **Import → Vermogen** — naam terug naar origineel Nederlands; legacy *Import*, *Terug & netto*, *Netto*, *Teruglevering* migreren naar *Vermogen* (DeviceID-lookup).
- **Vermogen icoon** — `EaseeImport` (geel ↓).

### Verwijderd (als aparte tegels)
- *Import* (Energy) en *Terug & netto* — niet meer aangemaakt; wees-tegels uit v10.9.0 handmatig verwijderen.

### Fixed (EN)
- Icons applied after device creation on fresh hardware add; WARNING when image_ids empty.
- Two Equalizer tiles: Status + Vermogen text (all power metrics merged); legacy Import/Terug & netto → Vermogen rename.

## [10.9.0] — 2026-06-17

### Gewijzigd
- **Equalizer tegels geconsolideerd** — drie tegels per Equalizer: **Status**, **Import**, **Terug & netto** (was zes tegels in v10.8.0).
- **Status-tegel** — gegroepeerde secties: verbinding, load balancing (fase-detail Vrij/Laad), limieten (eMobility | Hoofd | Limiet), max import, stroom L1/L2/L3, spanning L1/L2/L3.
- **Terug & netto** — gecombineerde teksttegel: import W, terug W, netto W, vandaag netto kWh (of totaal netto kWh).
- **Icon mapping** — Status/spanning/LB → `EaseeEqualizer`; Terug & netto → `EaseeNet` (geen nieuwe zip nodig).

### Verwijderd (als aparte tegels)
- Spanning, Teruglevering (standalone), Netto (standalone), Load balancing (detail) — niet meer aangemaakt.

### Legacy / upgrade
- Bestaande *Netto*- of *Teruglevering*-tegel wordt hernoemd naar *Terug & netto* (DeviceID-lookup).
- *Spanning* en *Load balancing* wees-tegels uit v10.8.0 blijven staan tot handmatige verwijdering.

### Changed (EN)
- Equalizer tiles consolidated to three: Status (grouped LB/voltage/limits/currents), Import (unchanged), Terug & netto (export+net text); legacy Netto/Teruglevering devices migrate to combined tile.

## [10.8.0] — 2026-06-17

### Toegevoegd
- **Equalizer Proposal C (Meterkast)** — zes tegels per Equalizer: Status, Import, Teruglevering, Netto, Spanning, Load balancing.
- **Import / Teruglevering** — aparte Energy-tegels voor obs. 40/45 (import) en 41/46 (export) met Vandaag kWh.
- **Netto-tegel** — netto vermogen (W) en totaal netto kWh (import − export).
- **Spanning-tegel** — L1/L2/L3 spanning (V) uit `/equalizers/{id}/state` of obs. 34–36.
- **Load balancing detail** — vrij beschikbare stroom en gelijkstroom per fase uit state (obs. 230–232 fallback).
- **Icon sets** — EaseeImport (↓), EaseeExport (↑), EaseeNet (Σ), EaseeVoltage (V); zip bevat nu 12 sets.

### Gewijzigd
- **Status-tegel** — huisvermogen-regel verwijderd (verplaatst naar Import-tegel).
- **Vermogen → Import** — bestaande *Meterkast - Vermogen* devices worden automatisch hernoemd via legacy DeviceID-lookup.
- **Observations query** — uitgebreid met spanning (34–36) en beschikbare stroom (230–232).

### Added (EN)
- Equalizer Proposal C: six tiles per equalizer; separate import/export energy tiles; net/voltage/LB detail text tiles; four new icon sets in `Easee_icons_v2.zip`.

## [10.7.2] — 2026-06-17

### Opgelost
- **onHeartbeat crash** — `equalizer_logic` gebruikte nog `plugin.is_main_limit_key`, `plugin.is_fuse_limit_key` en `plugin.is_emobility_key` als callbacks na verwijdering van passthrough-wrappers in v10.7.0; omgezet naar directe module-aanroepen via lambda.

### Fixed (EN)
- **onHeartbeat crash** — `equalizer_logic` still passed removed wrapper attrs `plugin.is_main_limit_key` / `is_fuse_limit_key` / `is_emobility_key` to `deep_scan_amp_keys`; now uses direct module lambdas.

## [10.7.1] — 2026-06-17

### Opgelost
- **onHeartbeat crash** — `poll_charger` gebruikte lokale variabelen `power_emoji` en `status_emoji` met dezelfde namen als module-functies; Python zag ze als unassigned locals (regressie na wrapper-verwijdering in v10.7.0).

### Fixed (EN)
- **onHeartbeat crash** — `poll_charger` assigned locals named `power_emoji`/`status_emoji` that shadowed module functions; call helpers directly in the status f-string.

## [10.7.0] — 2026-06-17

### Gewijzigd
- **Code cleanup** — alle passthrough-wrappers (~150 methodes) verwijderd uit `plugin.py`; modules roepen elkaar direct aan met `plugin` als eerste argument.
- **plugin.py** — verkleind tot lifecycle- en orchestratiehub (~340 regels incl. XML-docstring); geen functionele wijzigingen.
- **easee_api.py** — WARNING-log als `api_get` langer dan 5 seconden duurt.

### Changed (EN)
- **Code cleanup** — removed ~150 passthrough wrappers from `plugin.py`; direct module calls with `plugin` as first arg; no behavior change.
- **easee_api.py** — logs WARNING when `api_get` takes longer than 5 seconds.

## [10.6.5] — 2026-06-17

### Toegevoegd
- **Equalizer Vermogen — Vandaag kWh** — observation 45 (`CumulativeActivePowerImport`) wordt opgehaald en als cumulatieve teller (Wh) naar de Domoticz Energy-tegel geschreven; Domoticz berekent **Vandaag:** uit het verschil sinds middernacht (zelfde patroon als laadpaal `lifetimeEnergy`).
- **Fallback** — als observation 45 ontbreekt, wordt vermogen geïntegreerd via `power_integrated_kwh` met state in `easee_state.json`; DEBUG-log toont bron (cumulative vs integrated).

### Changed (EN)
- **Equalizer Vermogen tile** — fetches obs 45 cumulative import kWh, writes Wh counter for Domoticz daily delta; integrated power fallback when obs 45 is absent.

## [10.6.4] — 2026-06-17

### Gewijzigd
- **plugin.py** — initiële sync losgekoppeld van poll-interval (Mode1): vaste startup-vertraging (3s), readiness-check op geladen Domoticz Devices (bestaande Easee-devices, stabiele device-count of Devices > 0), fallback-sync na 60s met WARNING; poll-interval geldt alleen na `sync_done`.

### Changed (EN)
- **plugin.py** — decoupled initial sync from Mode1 poll interval: 3s startup delay, Domoticz Devices readiness checks, 60s forced fallback with WARNING; poll interval applies only after initial sync completes.

## [10.6.3] — 2026-06-17

### Gewijzigd
- **easee_api_keys.py** — nieuwe module met gecentraliseerde API-veldnamen: `FUSE_KEYS`, `EQUALIZER_KEYS`, `CHARGER_KEYS`, `SITE_STRUCTURE_KEYS`, `OBSERVATION_KEYS`, `TIBBER_KEYS`.
- **equalizer_logic.py, charger_logic.py, easee_helpers.py, tibber_pricing.py** — magic strings vervangen door gedeelde constanten; enkele bron van waarheid voor fuse/eMobility-sleutels.

### Changed (EN)
- **easee_api_keys.py** — centralized API field name constants for fuse, equalizer, charger, site structure, observations, and Tibber pricing.
- Core logic modules refactored to use shared key dicts instead of duplicated inline strings.

## [10.6.2] — 2026-06-17

### Gewijzigd
- **domoticz_devices.py** — `ensure_device_once` logt bij mislukte `Device.Create()` de exacte (gesanitiseerde) kwargs, exception-samenvatting en expliciete retry zonder `Image`; bij definitieve fout ERROR met volledige kwargs.

### Changed (EN)
- **domoticz_devices.py** — `ensure_device_once` logs sanitized kwargs, exception summary, and explicit Image-less retry on `Device.Create()` failure; final failure logged at ERROR.

## [10.6.1] — 2026-06-17

### Gewijzigd
- **easee_state.py** — atomisch opslaan via `easee_state.json.tmp` + `os.replace`; voorkomt corrupt state-bestand bij crash; opruimen van `.tmp` bij mislukte save; save-fouten via `easee_logging.error`.

### Changed (EN)
- **easee_state.py** — atomic state writes via `.tmp` + `os.replace`; cleanup on failure; save errors logged at ERROR level.

## [10.6.0] — 2026-06-17

### Toegevoegd
- **easee_logging.py** — centrale logging met vaste formatter `[Easee v10.6.0][LEVEL][module][context] message`; niveaus DEBUG, INFO, WARNING, ERROR. DEBUG alleen bij Debug-modus of `ULTRA_DEBUG`. WARNING via Domoticz.Log met ⚠, ERROR via Domoticz.Error.
- **State-migratie** — runtime state hernoemd van `easee_v9_0_state.json` naar `easee_state.json`; automatische rename bij eerste load na upgrade.

### Gewijzigd
- **plugin.py** — `log`/`debug`/`error`/`warning` delegeren naar `easee_logging`; poll-samenvatting in debug-modus.
- **easee_api.py, charger_logic.py, equalizer_logic.py** — kernpaden (login, discovery, errors, poll) migreren naar centrale logger.
- **Easee_icons_v2.zip** — functie-badges ~30% groter (16px: 6→8px, 48px: 13→17px); lettergrootte mee opgeschaald.
- **docs/icon-preview-v2.png** — bijgewerkt.

### Aanbevolen upgrade
- `git pull` in de pluginmap, **upload `Easee_icons_v2.zip` opnieuw** via **Instellingen → Meer opties → Aangepaste pictogrammen**, herstart het hardware-item. State migreert automatisch (`easee_v9_0_state.json` → `easee_state.json`).

### Added (EN)
- **easee_logging.py** — central logging with `[Easee v10.6.0][LEVEL][module][context]` format; DEBUG gated by debug mode or `ULTRA_DEBUG`.
- **State migration** — auto-rename `easee_v9_0_state.json` → `easee_state.json` on first load.

### Changed (EN)
- Plugin delegates and core modules use shared logger; function badges ~30% larger on icons; version v10.6.0.

---

## [10.5.18] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — definitieve iconenset: P-max productfoto laadpaal met per-functie LED-stripkleuren, Equalizer-max puck (max tegelvulling), subtiele functie-badges (W, i, €, !, Σ, E, L).
- **plugin.py** — laadt alleen nog `Easee_icons_v2.zip` (geen v1-fallback); versie v10.5.18.
- **scripts/generate_photo_icon_variants.ps1** — canonieke iconengenerator; `generate_icon_variants.ps1`, `generate_photo_equalizer_variants.ps1` en `generate_icons.py` verwijderd.
- **Documentatie** — README, INSTALL, icon-secties bijgewerkt; experimentele variant-mappen en `Easee_icons.zip` verwijderd.

### Verwijderd
- `Easee_icons.zip` (legacy v1)
- Experimentele icon-varianten (A–U, EQ-A–F) en dubbele preview-zips uit de repo

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. **Upload `Easee_icons_v2.zip` opnieuw** via **Instellingen → Meer opties → Aangepaste pictogrammen** — Domoticz cached iconen.

---

## [10.5.17] — 2026-06-16

### Gewijzigd
- **plugin.py** — Laadpaal Status-tegels (`EASEE_CHG_*`, label `Status`) gebruiken nu het Equalizer-pictogram (`EaseeEqualizer`) i.p.v. het blauwe status-pictogram; geldt voor beide laadpalen (bijv. Garage, Voordeur). Core Status (`EASEE_CORE_STATUS`) blijft `EaseeStatus`.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. Geen icon zip opnieuw uploaden nodig.

---

## [10.5.16] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — Equalizer-puck vergroot op tegel: squircle-marge 10→7 px (28→34 px breed, ~21% groter), hoekradius 8→9, binnenste cirkel 12→13 px; LoadBal-puck niet meer verkleind (scale 0.82→1.0).
- **plugin.py** — Equalizer-tegels krijgen via `DeviceID` (`EASEE_EQ_*`) het juiste pictogram: Status→`EaseeEqualizer`, Vermogen→`EaseePower`; core LoadBal→`EaseeLoadBal`; equalizer-naamheuristiek vóór generieke status-regel.
- **scripts/generate_icons.py / .ps1** — equalizer-geometrie en LoadBal-schaal bijgewerkt.
- **docs/icon-preview-v2.png** — bijgewerkt.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. **Upload `Easee_icons_v2.zip` opnieuw** via **Instellingen → Meer opties → Aangepaste pictogrammen** — Domoticz cached iconen.

---

## [10.5.15] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — Equalizer-silhouet verfijnd naar echte hardware: witte squircle puck met zachte 3D-gradiënt, prominent vlak binnenste cirkelvlak, subtiel lowercase **e**-logo (48px), gekleurde status-LED onderaan het cirkelvlak.
- **scripts/generate_icons.py / .ps1** — nieuwe equalizer-geometrie (outer/inner face, inset shadow, logo, LED-positie); Charge-iconen ongewijzigd.
- **docs/icon-preview-v2.png** — bijgewerkt.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. **Upload `Easee_icons_v2.zip` opnieuw** via **Instellingen → Meer opties → Aangepaste pictogrammen** — Domoticz cached iconen.

---

## [10.5.14] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — Charge-silhouet onderkant: afgerond schildpunt met zichtbare zwarte vleugels (geen scherpe V-inkeping); subtiele kabelaansluiting onderaan; LED-strip iets groter (~2px × ~15px bij 48px, ~80% opacity).
- **scripts/generate_icons.py / .ps1** — ellips-onderpunt, bredere wing-taper (16–32 bij y=39), verfijnde LED-geometrie (~2×16px).
- **docs/icon-preview-v2.png** — bijgewerkt.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. **Upload `Easee_icons_v2.zip` opnieuw** via **Instellingen → Meer opties → Aangepaste pictogrammen** — Domoticz cached iconen.

---

## [10.5.13] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — Charge-silhouet verfijnd naar Easee Charge Lite: twee-toon zwarte vleugels + grijs middenpaneel, dunnere subtielere LED-strip (~1px), betere schild-taper, statusdot boven strip, kabelaansluiting onderaan.
- **scripts/generate_icons.py / .ps1** — nieuwe shield/panel-geometrie en zachtere LED-opaciteit (~70%).
- **docs/icon-preview-v2.png** — bijgewerkt.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item. Als iconen niet veranderen: upload `Easee_icons_v2.zip` opnieuw via **Instellingen → Meer opties → Aangepaste pictogrammen**.

---

## [10.5.12] — 2026-06-16

### Gewijzigd
- **Easee_icons_v2.zip** — verticale LED-strip op het Charge-silhouet toont nu statuskleur (groen=online, geel=laden, blauw=status, oranje=kosten, rood=fout, teal=overzicht); Off-varianten met gedimde strip en lichter lichaam.
- **Equalizer-iconen** — witte squircle puck met gekleurde statusdot onderaan (zelfde kleurlogica).
- **scripts/generate_icons.py / .ps1** — gekleurde LED-strip tekenlogica; preview toont On/Off rijen.
- **docs/icon-preview-v2.png** — bijgewerkt met kleurvarianten.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item; controleer logregel `Custom icons geladen: 8 sets (Easee_icons_v2.zip)`.

---

## [10.5.11] — 2026-06-16

### Toegevoegd
- **Easee_icons_v2.zip** — nieuwe Domoticz-tegeliconen gebaseerd op Easee Charge (donker tap-toon silhouet) en Equalizer (witte squircle puck); 16×16 en 48×48 On/Off varianten.
- **docs/icon-preview-v2.png** — preview van alle acht v2-iconen.

### Gewijzigd
- **load_custom_images()** — probeert eerst `Easee_icons_v2.zip`, daarna `Easee_icons.zip` als fallback.
- **scripts/generate_icons.py / .ps1** — v2-tekenstijl (charger, equalizer, power, status, cost, overview, loadbal, alert).

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item; controleer logregel `Custom icons geladen: 8 sets (Easee_icons_v2.zip)`.

---

## [10.5.10] — 2026-06-16

### Toegevoegd
- **GitHub issue templates** — Nederlandstalige formulieren voor bugmeldingen en featurevoorstellen (`.github/ISSUE_TEMPLATE/`); lege issues uitgeschakeld; README-sectie *Problemen melden*.
- **GitHub labels** — `bug` en `enhancement` voor issue templates.

### Gewijzigd
- **Repository** — openbaar op GitHub; documentatie bijgewerkt (geen verwijzingen meer naar privé-repo).
- **INSTALL.md** — zip-methode: `easee-domoticz-main.zip`, kopieer `plugin.py` en `Easee_icons.zip`; handmatige icon-upload als alternatief.
- **docs/GIT_SETUP.md** — mapstructuur inclusief `Easee_icons.zip`; fouttabel voor openbare repo.

### Aanbevolen upgrade
- Alleen documentatie/GitHub — geen functionele wijzigingen t.o.v. v10.5.9. Optioneel: `git pull` en herstart hardware-item.

---

## [10.5.9] — 2026-06-16

### Gewijzigd
- **Documentatie** — `RELEASE_NOTES.md` verwijderd; release-informatie staat alleen nog in `CHANGELOG.md`.
- **Custom icon zip** — `load_custom_images()` zoekt alleen nog `Easee_icons.zip` (verouderde fallback-bestandsnamen verwijderd).

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item of Domoticz.

---
## [10.5.8] — 2026-06-16

### Gewijzigd
- **Pluginweergavenaam** — Type en beschrijving tonen nu **Easee Domoticz plugin v10.5.8** (kleine *p* in *plugin*); versienummer in `<h2>` bij product-URL.
- **externallink** — wijst naar [github.com/rleunk/easee-domoticz](https://github.com/rleunk/easee-domoticz).
- **Documentatie** — README, INSTALL, CHANGELOG en docs/ gesynchroniseerd; verouderde *Easee AutoDiscovery Compact*-verwijzingen verwijderd.

### Aanbevolen upgrade
- `git pull` in de pluginmap en herstart het hardware-item of Domoticz.
- Als iconen na upgrade nog ontbreken: upload `Easee_icons.zip` eenmalig via **Instellingen → Meer opties → Aangepaste pictogrammen**.

---

## [10.5.7] — 2026-06-16

### Opgelost
- **Custom icon zip laden** — `Easee_icons.zip` gebruikt weer v8-stijl namen (`EaseeCharger` i.p.v. `EaseeCloudAutoDiscoveryV1000EaseeCharger`). Domoticz `Image().Create()` faalt vaak stil bij prefixed namen; handmatig geüploade iconen worden nu herkend.
- **Icon lookup** — plugin zoekt iconen op zowel korte naam als PLUGIN_KEY-prefix (backward compatible met oudere uploads).

### Gewijzigd
- **Icon generator** — `generate_icons.py` / `generate_icons.ps1` schrijven eenvoudige bestandsnamen en UTF-8 zonder BOM.
- **Handmatige upload** — duidelijke logmelding en documentatie als automatisch laden mislukt.

### Aanbevolen upgrade
- `git pull` in de pluginmap (controleert `Easee_icons.zip`) en herstart het hardware-item of Domoticz.
- Als iconen na upgrade nog ontbreken: upload `Easee_icons.zip` eenmalig via **Instellingen → Meer opties → Aangepaste pictogrammen**.

---

## [10.5.6] — 2026-06-16

### Opgelost
- **Custom icon zip laden** — Domoticz registreert iconen onder de `Base`-waarde uit `icons.txt` (`EaseeCloudAutoDiscoveryV1000EaseeCharger`), niet onder de korte naam (`EaseeCharger`). De plugin zocht op de verkeerde sleutel in `Images`, waardoor `Create()` wel kon slagen maar `image_ids` leeg bleef en ten onrechte "geen custom icon zip gevonden" verscheen.

### Gewijzigd
- **Icon zip diagnostiek** — onderscheid tussen zip ontbreekt vs. zip aanwezig maar laden mislukt; logt `plugin_dir`, poging tot laden, en `Create()`-fouten op normaal logniveau.

### Aanbevolen upgrade
- `git pull` in de pluginmap (controleer daarna `ls -la Easee_icons.zip`) en herstart het hardware-item of Domoticz.

---

## [10.5.5] — 2026-06-16

### Opgelost
- **Custom icon zip laden** — `Easee_icons.zip` bevatte een UTF-8 BOM in `icons.txt`, waardoor Domoticz PNG-bestanden niet kon vinden (`Icon File: …48_Off.png is not present`). Icon generator schrijft nu UTF-8 zonder BOM; zip opnieuw gegenereerd.

### Aanbevolen upgrade
- `git pull` (haalt `Easee_icons.zip` op) en herstart het hardware-item of Domoticz.

---

## [10.5.4] — 2026-06-16

### Toegevoegd
- **Custom iconen in repo** — `Easee_icons.zip` bevat acht Easee-tegeliconen (Charger, Equalizer, Power, Status, Alert, LoadBal, Cost, Overview) en wordt automatisch geladen uit de pluginmap.
- **`apply_images_to_devices()`** — bestaande tegels krijgen na pluginherstart de juiste iconen zonder devices te verwijderen.

### Gewijzigd
- **Pluginweergavenaam** — In Domoticz Hardware staat het type nu **Easee Domoticz Plugin v10.5.4** (versienummer weer zichtbaar).

### Aanbevolen upgrade
- `git pull` (haalt `plugin.py` + `Easee_icons.zip` op) en herstart het hardware-item of Domoticz. Geen schone installatie nodig.

---

## [10.5.3] — 2026-06-16

### Opgelost
- **Laatste sessiekosten na laden** — na afloop van een laadsessie blijft de kosten-tegel de sessiekosten tonen als **Laatste sessie: €X.XX | Dag: €Y.YY** in plaats van **Sessie: €0.00**. Sessie-einde wordt nu na de laatste kostenberekening opgeslagen, zodat de volledige sessiekosten bewaard blijven.

### Aanbevolen upgrade
- Upgrade vanaf v10.5.2: vervang alleen `plugin.py` en herstart het hardware-item.

---

## [10.5.2] — 2026-06-16

### Gewijzigd
- **Pluginweergavenaam** — In Domoticz Hardware staat het type nu **Easee Domoticz Plugin** (was *Easee AutoDiscovery Compact*). Plugin-key (`EaseeCloudAutoDiscoveryV1000`) is ongewijzigd; bestaande installaties blijven werken.

### Aanbevolen upgrade
- Upgrade vanaf v10.5.1: vervang alleen `plugin.py` en herstart het hardware-item.

---

## [10.5.1] — 2026-06-16

### Opgelost
- **Kosten tijdens laden na schone installatie** — sessie- en dagkosten bleven €0,00 omdat alleen `lifetimeEnergy`-delta's werden gebruikt; die waarde verandert tijdens een actieve sessie vaak niet in de state-API. Kosten en sessie-kWh gebruiken nu `sessionEnergy` (state/ongoing session) met fallback op vermogensintegratie.

### Aanbevolen upgrade
- Upgrade vanaf v10.5.0: vervang alleen `plugin.py` en herstart het hardware-item.

---

## [10.5.0] — 2026-06

### Toegevoegd
- **Mode4** — Extra laadpaalnamen (komma-gescheiden) voor lader 3 en verder, bijv. `Carport, Werf`.
- Documentatie: ondersteunde scenario's (1/2/N laders, met/zonder Equalizer, met/zonder Tibber) en public release checklist in README.
- Auto-detectie van **nieuwe laadpalen** tijdens polling (zelfde patroon als Equalizer).

### Gewijzigd
- Mode4 is herbestemd van ongebruikt prefix-veld naar extra laadpaalnamen; hardwarenaam in Domoticz blijft het prefix op tegels.

### Aanbevolen upgrade
- Upgrade vanaf v10.4.0: vervang alleen `plugin.py` en herstart het hardware-item. State en devices blijven behouden.

---

## [10.4.0] — 2026-06

### Opgelost
- **Kosten & Samenvatting** toont nu het actuele Tibber-tarief (zelfde bron als **Beste laden**).
- Per-lader **Kosten (Sessie/Dag)** toont weer echte sessie- en dagkosten tijdens het laden.

### Aanbevolen upgrade
- Upgrade vanaf v10.3.4: vervang alleen `plugin.py` en herstart het hardware-item. State en devices blijven behouden.

---

## [10.3.4] — 2026

### Verbeterd
- Stabiliteit van kostenberekening en sessie-tracking.
- Verfijningen aan Equalizer-weergave en fuse/limiet-detectie.

---

## [10.3.0] — 2026

### Toegevoegd
- Verdere Equalizer-ondersteuning: load balancing, hoofdzekering en eMobility-limieten in status-tiles.
- Verbeterde auto-discovery van Equalizer via meerdere Easee API-paden.

### Verbeterd
- Compactere device-namen en emoji-indicatoren in statusweergave.

---

## [10.2.0] — 2026

### Toegevoegd
- Equalizer (meterkast) discovery — stap 1: detectie, status en vermogen.
- Optionele handmatige Equalizer ID via hardwareveld **IP**.
- Aangepaste Equalizer-naam via veld **Address**.

### Verbeterd
- Site-filter (Mode5) en debug-logging voor troubleshooting.

---

## [10.1.0] — 2026

### Toegevoegd
- Eerste stabiele **AutoDiscovery Compact**-release.
- Automatische detectie van Easee-laadpalen.
- Tibber-integratie: actueel stroomtarief, goedkoopste laadvenster en kosten per sessie/dag.
- Aangepaste laadpaalnamen via **Mode2** en **Mode3**.
- Kern-tiles: Status, Totaal Laden, Totaal kWh, LoadBal, Kosten & Samenvatting, Beste laden.

### Vereisten
- Domoticz met Python 3 en `python3-requests`.
- Easee-account (gebruikersnaam + wachtwoord).
