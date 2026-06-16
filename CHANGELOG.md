# Changelog

Alle belangrijke wijzigingen aan dit project worden hier gedocumenteerd.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/).

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
