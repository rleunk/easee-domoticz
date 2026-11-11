# Kopieer patch-bestanden naar je echte projectmap (eenmalig per update).
# Bron: easee-domoticz\sessy-economics-patch\LXC249
# Doel:  ha-sessy-economics\LXC249  (zoals op LXC /opt/sessy-economics-engine)

$ErrorActionPreference = "Stop"
$PatchRoot = $PSScriptRoot
$TargetRoot = Join-Path $env:USERPROFILE "Projects\ha-sessy-economics\LXC249"

if (-not (Test-Path $TargetRoot)) {
    Write-Error "Doelmap ontbreekt: $TargetRoot"
}

# Alleen gewijzigde patch-bestanden (vendor is geen volledige kopie in git).
$files = @(
    "vendor\sessy_economics\economics.py",
    "vendor\sessy_economics\pricing.py",
    "vendor\sessy_economics\p1_accounting.py",
    "vendor\sessy_economics\p1_registers.py",
    "vendor\sessy_economics\api.py",
    "sessy_economics_engine\runner.py",
    "sessy_factuur_web\pdf_parser.py",
    "sessy_factuur_web\p1_month.py"
)
foreach ($rel in $files) {
    $src = Join-Path $PatchRoot $rel
    if (-not (Test-Path $src)) {
        Write-Warning "Ontbreekt in patch: $rel"
        continue
    }
    $dst = Join-Path $TargetRoot $rel
    $parent = Split-Path $dst -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "OK $rel"
}

Write-Host "Klaar. Upload daarna $TargetRoot naar LXC /opt/sessy-economics-engine (vendor + engine + factuur_web)."
