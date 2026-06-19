# Troubleshooting Gids

> **Huidige versie:** v10.9.31 (stable testing; functioneel v10.9.28) · Volledige installatie: [INSTALL.md](../INSTALL.md)

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

**Verwacht (referentie):** bij **2 laadpalen + 1 Equalizer + Tibber** hoort **exact 15 tegels** — zie [CONFIGURATION.md — Verwachte tegels](CONFIGURATION.md#verwachte-tegels-referentie).

**Legacy-tegels die er níet horen:** *Import*, *Spanning*, *Terug & netto*, *Netto*, *Teruglevering*, losse *Load balancing* (Equalizer). Die komen uit v10.8.0 of v10.9.0. Verwijder ze handmatig in Domoticz (**Setup → Devices**).

**Heb je precies 15 tegels** (zonder legacy-namen)? Dan is alles in orde — geen actie nodig.

### Custom iconen ontbreken

**Symptoom**: Generieke Text-iconen; log toont `image_ids: 0/13`

**Oorzaken (historisch, opgelost in v10.9.7+):**
- v10.9.2–v10.9.5: ongeldige `UpdateProperties`-parameter
- v10.9.6: `Device.Update(Image=…)` zonder `nValue`/`sValue`
- v10.9.4: zip-pad verdubbeling; v10.9.5: plugin-key-prefix ontbrak (1/12 sets)

**Oplossing** (v10.9.28+):
1. **Verwijder oude Easee custom icons** via **Instellingen → Aangepaste pictogrammen**
2. Controleer `Easee_icons_v2.zip` en map `icons/` (13 mini-zips) in pluginmap
3. `git pull` naar v10.9.30 en herstart hardware-item
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

### Optionele API 403/405 (normaal — alleen Debug)

**Symptoom** (alleen bij **Debug logging**, Mode6 = *Debug*): regels als `GET /equalizers/…/state optioneel mislukt (HTTP 403)` of `GET /sites/…/circuits optioneel: HTTP 405`

**Oorzaak**: veel Easee-accounts hebben **geen API-toegang** tot bepaalde optionele endpoints. De plugin probeert ze voor extra fuse/LB-data; bij mislukking valt hij terug op observations en `siteStructure`.

| Endpoint | HTTP | Verwacht gedrag |
|----------|------|-----------------|
| `/equalizers/{id}/state` | 403 | Observations + sticky power; 403-cache 5 min |
| `/cloud-loadbalancing/…` | 403 | Limiet uit siteStructure/site.state |
| `/equalizers/{id}/loadbalancing/…` | 403 | Idem |
| `/equalizers` (lijst) | 403 | Discovery via `/accounts/products` |
| `/sites/{id}/circuits` | 405 | Embedded circuits in site/state |

**Oplossing**: geen actie nodig. Zet Debug uit (Mode6 = *Normal*) als je deze regels niet wilt zien. **HTTP 429** blijft WARNING — dat wijst op te veel polling.

Zie ook [ROADMAP — Equalizer stap 2+](ROADMAP.md#equalizer--stap-1-afgerond-vs-stap-2-beperkt-door-account-api).

### Geen Equalizer gevonden

1. Debug logging aan (Mode6)
2. Herstart hardware-item
3. Handmatig **Equalizer ID** in IP-veld
4. Equalizer zichtbaar in Easee-app?

Zonder Equalizer werkt de plugin volledig; Status toont `Geen EQ`.

### Tibber / kosten-tegels

- **Tibber-token (Mode7) is verplicht** voor kosten-tegels — zonder token worden per-lader kosten en kern-tegels *Kosten & Samenvatting* / *Beste laden* niet bijgewerkt. Bij start zie je `Tibber uit (Mode7 leeg)`.
- **Token verloren na hardware-opslag?** Sinds v10.9.30 bewaart de plugin een backup in `easee_state.json`. Na `git pull` + herstart zou Tibber automatisch actief moeten blijven (log: *token hersteld uit state-backup*). Zonder backup: token opnieuw invullen in Mode7.
- Met Tibber: token op [developer.tibber.com](https://developer.tibber.com/settings/access-token). Bij start: `Tibber actief — kosten-tegels worden bijgewerkt na eerste poll`.
- Kosten *0 €* terwijl Tibber actief is: verwijder **Kosten (Sessie/Dag)**-tile en herstart hardware-item; controleer of `Kosten-tegel niet gevonden` in log staat (WARNING).

### Logniveaus

| Niveau | Wanneer | Voorbeelden |
|--------|---------|-------------|
| INFO | Altijd (Mode6 = Normal) | Plugin gestart, Tibber actief/uit, `image_ids: 13/13`, state migratie |
| DEBUG | Alleen Mode6 = *Debug* | `Poll voltooid`, kosten-tegel bijgewerkt, siteStructure, verwachte optionele API 403/405 |
| WARNING | Altijd | Kosten-tegel niet gevonden, HTTP 429 (sessions/ongoing e.d.), iconen ontbreken |
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

Bij een issue: pluginversie **v10.9.31**, Domoticz-versie en logregels `[Easee v…]` (geen wachtwoorden/tokens).
