# Easee iconen — regeneratie

De plugin gebruikt **`Easee_icons_v2.zip`** in de repo-root als enige iconenarchief.

## Wat zit erin?

- **P-max laadpaal** — productfoto (Easee Charge), maximale tegelvulling, verticale LED-strip in functiekleur
- **Equalizer-max puck** — vector squircle (v10.5.15-stijl), maximale tegelvulling
- **13 icon sets** — Charger, Power, Status, StatusGlobal, Cost, Alert, Overview, Equalizer, LoadBal, Import, Export, Net, Voltage (16×16 + 48×48 On/Off)
- **Functie-badges** — subtiele hoekmarkering: W, i, €, !, Σ, E, L (Charger heeft geen badge)

Preview: [`../icon-preview-v2.png`](../icon-preview-v2.png).

## Opnieuw genereren

Vanuit de repo-root (Windows PowerShell):

```powershell
.\scripts\generate_photo_icon_variants.ps1
```

Vereist: `docs/icon-options/source/easee-charge-front-gray.png` en `easee-charge-front-red.png` (script downloadt ze indien ontbrekend).

Optioneel voor experimentele varianten (niet in repo):

```powershell
.\scripts\generate_photo_icon_variants.ps1 -IncludeVariants
```

Vector Equalizer-tekenlogica staat in `scripts/generate_icons.ps1` (wordt dot-sourced door het photo-script).

## Domoticz upload

Na upgrade: upload **`Easee_icons_v2.zip`** via **Instellingen → Meer opties → Aangepaste pictogrammen** (Domoticz cached iconen).

Zie [README.md](../../README.md#custom-iconen) en [INSTALL.md](../../INSTALL.md#custom-iconen-handmatig-uploaden).
