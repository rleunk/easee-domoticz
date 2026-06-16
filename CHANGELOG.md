# Changelog

Alle belangrijke wijzigingen aan dit project worden hier gedocumenteerd.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/).

## [Unreleased]

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
