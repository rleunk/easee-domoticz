# Troubleshooting Gids

> **Versies:** **v1** branch — **0.6.1** (pre-release) · Legacy **v10.11.6-stable** op `main`  
> Installatie: [INSTALL.md](../INSTALL.md) · Stable-tags: [STABLE.md](../STABLE.md) · Configuratie: [CONFIGURATION.md](CONFIGURATION.md)

## Veelvoorkomende Problemen

### Plugin laadt niet

**Symptoom**: *Easee Domoticz plugin* type niet beschikbaar in Hardware menu

**Oplossing**:

```bash
ls -la /home/root/domoticz/plugins/Easee-Domoticz-plugin/plugin.py
sudo apt install -y python3-requests
sudo systemctl restart domoticz
sudo journalctl -u domoticz -f | grep Easee
```

### Login mislukt

**Symptoom**: *Login mislukt, HTTP 401* in logs

**Oplossing**:
1. Controleer credentials in Domoticz (**Setup → Hardware**)
2. Test inlog in de Easee-app
3. Zet **Debug logging** (Mode6) aan
4. Wacht 5–10 minuten bij rate limit

### Geen devices gemaakt

**Symptoom**: Hardware actief maar geen devices

**Oplossing**:
1. Palen zichtbaar in Easee-app?
2. Verwijder site filter (Mode5) tijdelijk
3. Wacht 1–2 minuten na eerste start
4. Log: `sudo journalctl -u domoticz -f | grep -i "charger\|Discovery"`

### Verkeerd aantal tegels / legacy-tegels

**Symptoom**: Meer dan verwachte tegels, of tegels met namen als *Import*, *Spanning*, *Terug & netto*

**Verwacht (referentie):** bij **2 laadpalen + 1 Equalizer + Tibber** hoort **11 actieve tegels + LoadBal** (12 devices) — zie [CONFIGURATION.md — Verwachte tegels](CONFIGURATION.md#verwachte-tegels-referentie).

**Verouderde v10.10-tegels** (*Kosten & Samenvatting*, *Dagrapport*, *Totaal & Sessie*, *Kosten (Sessie/Dag)*): na upgrade naar v10.11.x worden deze verborgen (`Used=0`) of hernoemd naar **Dag overzicht** (v10.11.5+; fix in v10.11.6). Data staat op **Dag overzicht**, **Laden** (Description) en **Status**. Handmatig verwijderen mag.

**Legacy-tegels die er níet horen:** *Import*, *Spanning*, *Terug & netto*, *Netto*, *Teruglevering*, losse *Load balancing* (Equalizer). Die komen uit v10.8.0 of v10.9.0. Verwijder ze handmatig in Domoticz (**Setup → Devices**).

**Heb je 11 tegels + LoadBal** (zonder legacy-namen)? Dan is alles in orde — geen actie nodig.

### Custom iconen ontbreken

**Symptoom**: Generieke Text-iconen; log toont `image_ids: 0/13`

**Oorzaken (historisch, opgelost in v10.9.7+):**
- v10.9.2–v10.9.5: ongeldige `UpdateProperties`-parameter
- v10.9.6: `Device.Update(Image=…)` zonder `nValue`/`sValue`
- v10.9.4: zip-pad verdubbeling; v10.9.5: plugin-key-prefix ontbrak (1/12 sets)

**Oplossing** (v10.9.28+):
1. **Verwijder oude Easee custom icons** via **Instellingen → Aangepaste pictogrammen**
2. Controleer `Easee_icons_v2.zip` en map `icons/` (13 mini-zips) in pluginmap
3. `git pull` of `git checkout v10.11.6-stable` en herstart hardware-item
4. Log controleren:
   - `Custom icons geladen: 13 sets`
   - `image_ids: 13/13 sets`
5. Mislukt automatisch laden? Upload `Easee_icons_v2.zip` handmatig, herstart hardware-item

**Energy-tegels** (*Laden*, *Totaal Laden*): sommige Domoticz-versies tonen altijd het bliksem-icoon — **bekende beperking**, geen plugin-bug.

Zie [INSTALL.md — Custom iconen](../INSTALL.md#custom-iconen-handmatig-uploaden).

### Verkeerd icoon op tegel

**Symptoom**: Laadpaal Status toont Equalizer-puck, of globale Status mist combo-icoon

**Oplossing** (v10.9.10+):
- Upgrade naar **v10.9.28+**
- Upload **`Easee_icons_v2.zip` opnieuw** (bevat `EaseeStatusGlobal`)
- Verwacht mapping:
  - *Easee - Status* → combo (`EaseeStatusGlobal`)
  - *Garage - Status* / *Voordeur - Status* → laadpaal-only (`EaseeStatus`)
  - *Meterkast - Status* / *Vermogen* → Equalizer-puck (`EaseeEqualizer`)

### Meterkast - Import blijft bestaan (legacy)

**Symptoom**: Tegel heet *Import* met Energy W/kWh i.p.v. Text *Vermogen*

**Oplossing** (v10.9.2+): herstart hardware-item — plugin maakt Text *Vermogen* opnieuw aan. Log: `legacy Import Energy → Text Vermogen`. Blijft *Import* bestaan na herstart? Verwijder de tegel handmatig.

### Equalizer Vermogen blijft 0/0/0

**Symptoom**: Vermogen-tegel toont 0 na Domoticz-herstart of na enkele polls

**Oplossing** (v10.9.11–v10.9.28):
1. Upgrade naar **v10.9.28+** (`git pull`, herstart hardware-item)
2. Controleer log op `HTTP 429` — zie [HTTP 429 rate limit](#http-429-rate-limit-easee-api) hieronder
3. Zet **Debug logging** (Mode6) aan; zoek naar `power via equalizer.state` of `obs 40/41`
4. Handmatig **Equalizer ID** in IP-veld als auto-discovery faalt

Sinds v10.9.17 blijft de laatste geldige waarde op de tegel staan bij een mislukte poll (sticky power). Sinds v10.9.28 is Vandaag kWh op de Laden-tegel betrouwbaar na middernacht-upgrade.

### HTTP 429 rate limit (Easee API)

**Symptoom**: Logregels met `HTTP 429`, `rate limit`, of Equalizer/charger-data ontbreekt tijdelijk

**Oorzaak**: Te veel API-aanroepen naar Easee binnen korte tijd (meerdere laders + Equalizer + discovery).

**Oplossing**:
1. Zet **Poll interval (Mode1)** op **60 seconden**:
   - **Setup → Hardware** → klik je Easee hardware-item
   - Wijzig **Poll interval (sec)** van `30` naar `60`
   - Klik **Save**
2. Wacht enkele minuten — Easee rate limit verloopt vanzelf
3. Blijven 429-waarschuwingen? Probeer **90–120 sec** (zie [CONFIGURATION.md](CONFIGURATION.md))

**Niet nodig:** Domoticz of server herstarten alleen voor 429 — verhoog het poll-interval.

Sinds v10.9.13 blokkeert 429 de hardware-thread niet meer. Sinds v10.9.17 blokkeert een charger-429 de Equalizer-poll niet meer.

### Optionele API 403/404/405/429 (normaal — alleen Debug)

**Symptoom** (alleen bij **Debug logging**, Mode6 = *Debug*): regels als `GET /equalizers/…/state optioneel mislukt (HTTP 403)`, `GET /chargers/…/sessions/ongoing optioneel: HTTP 404`, of `GET /chargers/…/config optioneel: rate limit (429, charger)`

**Oorzaak**: veel Easee-accounts hebben **geen API-toegang** tot bepaalde optionele endpoints, of de plugin raakt een tijdelijke rate limit op optionele charger-calls. De plugin valt terug op observations, `siteStructure` en `/chargers/{id}/state`.

| Endpoint | HTTP | Verwacht gedrag |
|----------|------|-----------------|
| `/equalizers/{id}/state` | 403 | Observations + sticky power; 403-cache 5 min |
| `/cloud-loadbalancing/…` | 403 | Limiet uit siteStructure/site.state |
| `/equalizers/{id}/loadbalancing/…` | 403 | Idem |
| `/equalizers` (lijst) | 403 | Discovery via `/accounts/products` |
| `/sites/{id}/circuits` | 405 | Embedded circuits in site/state |
| `/chargers/{id}/sessions/ongoing` | 404 | Geen actieve sessie; fallback op `/state` sessionEnergy |
| `/chargers/{id}/config`, `/sessions/ongoing` | 429 | Rate limit; overslaan tot volgende poll; state blijft bron |

**Oplossing**: geen actie nodig. Zet Debug uit (Mode6 = *Normal*) als je deze regels niet wilt zien. **HTTP 429 op verplichte endpoints** (bijv. `/chargers/{id}/state`) blijft WARNING — verhoog dan het poll-interval.

Zie ook [ROADMAP — Gepland / onderzoek](ROADMAP.md#gepland--onderzoek) (Equalizer fase-detail, API rate limit).

### Geen Equalizer gevonden

1. Debug logging aan (Mode6)
2. Herstart hardware-item
3. Handmatig **Equalizer ID** in IP-veld
4. Equalizer zichtbaar in Easee-app?

Zonder Equalizer werkt de plugin volledig; Status toont `Geen EQ`.

### Prijsbron & kosten (v1 — branch `v1`)

De plugin ondersteunt vijf **Prijsbron**-waarden (Mode9): **Geen**, **Handmatig**, **Tibber**, **ENTSO-E**, **EnergyZero**. Kosten-tegels (*Dag overzicht*, *Beste laden*, sessie/dag-€ op laadpaal-**Status**) zijn alleen actief bij een prijsbron die kosten berekent.

| Prijsbron | Vereist | Startup-log (INFO) |
|-----------|---------|-------------------|
| **Geen** | — | `Prijsbron Geen — kosten uitgeschakeld` |
| **Handmatig** | Mode10–19 naar type | Handmatig tarief zichtbaar |
| **Tibber** | Mode7 token | `Tibber actief — kosten na eerste poll` |
| **ENTSO-E** | Mode24 token + toeslagen | `ENTSO-E actief — kosten na eerste poll` |
| **EnergyZero** | Niets (geen token) | `EnergyZero actief — kosten na eerste poll` |

**Globale Status-tegel (v0.6.1+)** toont de actieve prijsbron, bijv. `Tibber €0,23/kWh` of `EnergyZero €0,17/kWh`.

#### Kosten blijven €0,00

1. Controleer **Prijsbron (Mode9)** — staat die op **Geen**?
2. Bij **Tibber**: Mode7 ingevuld? Log: `Tibber uit (Mode7 leeg)` → token invullen of backup in `easee_state.json`
3. Bij **ENTSO-E**: Mode24 ingevuld en token goedgekeurd? Zie [ENTSO-E unauthorized](#entso-e-unauthorized--geen-token-menu)
4. Bij **Handmatig**: Mode10 (Vast) of Mode11–19 (Dag/nacht / Dal-piek) correct?
5. Bij **EnergyZero**: geen token nodig — wacht 1–2 polls na start; controleer internettoegang naar `api.energyzero.nl`
6. Herstart hardware-item; controleer **Dag overzicht** en laadpaal-**Status** (niet legacy *Kosten (Sessie/Dag)*)

#### ENTSO-E unauthorized / geen token-menu

**Symptoom:** Log `ENTSO-E API mislukt (401/403)` of *Unauthorized*; in ENTSO-E-portaal geen menu *Web API Security Token*

**Oorzaak:** ENTSO-E verleent API-toegang pas na handmatige goedkeuring per e-mail.

**Oplossing:**
1. Registreer op [transparency.entsoe.eu](https://transparency.entsoe.eu/)
2. E-mail **transparency@entsoe.eu** — onderwerp **`Restful API access`**, vermeld je account-e-mail
3. Wacht ~**3 werkdagen** op goedkeuringsmail
4. Daarna: **My Account** → **Web API Security Token** → kopieer naar **Mode24**
5. Vul toeslagen in (Mode25–27) naar jouw contract

Zolang goedkeuring uitstaat: schakel tijdelijk naar **Tibber**, **EnergyZero** of **Handmatig**.

#### EnergyZero — geen prijzen / lege tegel

**Symptoom:** *Dag overzicht* toont geen tarief; log geen `EnergyZero actief`

**Oplossing:**
1. **Prijsbron** = **EnergyZero** (Mode9) — geen Mode24/Mode7 nodig
2. Controleer dat de server `https://api.energyzero.nl` kan bereiken (firewall/DNS)
3. Morgen-prijzen verschijnen meestal rond ~14:00–15:00 CET — tot die tijd alleen vandaag
4. Prijzen zijn **indicatief** (incl. BTW via API) — kunnen afwijken van jouw leverancier

#### Geen *Beste laden*-tegel

Verschijnt alleen bij **Tibber** (met token), **Handmatig**, **ENTSO-E** of **EnergyZero**. Bij **Geen** ontbreekt deze tegel — verwacht gedrag.

#### Token verloren na hardware-opslaan (Tibber / ENTSO-E)

Domoticz wist wachtwoordvelden soms bij *Opslaan*. Sinds v0.5.0/v10.9.30 bewaart de plugin backups in `easee_state.json` (`tibber_token_backup`, `entsoe_token_backup`). Log: *token hersteld uit state-backup*. Zonder backup: opnieuw invullen in Mode7 resp. Mode24.

### Tibber / kosten-tegels (legacy v10 — alleen Tibber)

Op branch **`main`** / tag **v10.11.6-stable** geldt alleen Tibber voor kosten. Op branch **`v1`** zie [Prijsbron & kosten](#prijsbron--kosten-v1--branch-v1) hierboven.

- **Tibber-token (Mode7) is verplicht** voor kosten op legacy v10 — zonder token worden *Dag overzicht*, *Beste laden* en sessie/dag-€ op laadpaal-**Status** niet bijgewerkt. Bij start zie je `Tibber uit (Mode7 leeg)`.
- **Token verloren na hardware-opslag?** Sinds v10.9.30 bewaart de plugin een backup in `easee_state.json`. Na `git pull` + herstart zou Tibber automatisch actief moeten blijven (log: *token hersteld uit state-backup*). Zonder backup: token opnieuw invullen in Mode7.
- Met Tibber: token op [developer.tibber.com](https://developer.tibber.com/settings/access-token). Bij start: `Tibber actief — kosten-tegels worden bijgewerkt na eerste poll`.
- Kosten *0 €* terwijl Tibber actief is: herstart hardware-item; controleer of laadpaal-**Status** en **Dag overzicht** bestaan (niet de verouderde *Kosten (Sessie/Dag)* / *Kosten & Samenvatting*).

### Sessie-kWh / Totaal & Sessie (v10.10.x — superseded in v10.11)

Sinds **v10.11** staat sessie/vandaag/totaal kWh op de **Laden**-tegel (Description), niet meer op *Totaal & Sessie*. Problemen met *Totaal & Sessie header 0 kWh* (v10.10.4–10.10.8) zijn opgelost in v10.10.8 maar die tegel is **verouderd** — upgrade naar **v10.11.6-stable** en kijk op **Laden**.

### Logniveaus

| Niveau | Wanneer | Voorbeelden |
|--------|---------|-------------|
| INFO | Altijd (Mode6 = Normal) | Plugin gestart, prijsbron actief/uit (Tibber/ENTSO-E/EnergyZero/Geen), `image_ids: 13/13`, state migratie |
| DEBUG | Alleen Mode6 = *Debug* | `Poll voltooid`, kosten-tegel bijgewerkt, siteStructure, verwachte optionele API 403/404/405/429 |
| WARNING | Altijd | Kosten-tegel niet gevonden, HTTP 429 op verplichte endpoints, iconen ontbreken |
| ERROR | Altijd | Login mislukt, zip laden mislukt |

Laat Debug op *Normal* staan tenzij je troubleshoott.

### Devices dubbel na herstart

1. Stop hardware-item
2. Verwijder dubbele devices
3. Start opnieuw

## Debug Mode

1. **Setup → Hardware** → Easee-item → **Debug logging** (Mode6) = *Debug*
2. Logs: `sudo journalctl -u domoticz -f | grep "Easee v"`

## Performance

- Poll interval (Mode1) verhogen naar **60 sec** bij 429-waarschuwingen of hoog CPU
- Debug op *Normal* als je niet troubleshoott

## Reset state

```bash
sudo systemctl stop domoticz
rm /home/root/domoticz/plugins/Easee-Domoticz-plugin/easee_state.json
sudo systemctl start domoticz
```

## Support

- **GitHub Issues**: https://github.com/rleunk/easee-domoticz/issues
- **Installatie**: [INSTALL.md](../INSTALL.md)
- **Configuratie**: [CONFIGURATION.md](CONFIGURATION.md)

Bij een issue: pluginversie **v0.6.1** (v1) of **v10.11.6-stable** (legacy), Domoticz-versie, **Prijsbron (Mode9)** indien van toepassing, en logregels `[Easee v…]` (geen wachtwoorden/tokens).
