# Kopieer patch-bestanden naar je echte projectmap (eenmalig per update).
# Bron: easee-domoticz\sessy-economics-patch\LXC249
# Doel:  ha-sessy-economics\LXC249  (zoals op LXC /opt/sessy-economics-engine)

$ErrorActionPreference = "Stop"
$PatchRoot = $PSScriptRoot
$TargetRoot = Join-Path $env:USERPROFILE "Projects\ha-sessy-economics\LXC249"

if (-not (Test-Path $TargetRoot)) {
    Write-Error "Doelmap ontbreekt: $TargetRoot"
}

$dirs = @("vendor", "sessy_economics_engine", "sessy_factuur_web")
foreach ($d in $dirs) {
    $src = Join-Path $PatchRoot $d
    if (-not (Test-Path $src)) { continue }
    $dst = Join-Path $TargetRoot $d
    Write-Host "Copy $src -> $dst"
    Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
}

Write-Host "Klaar. Upload daarna $TargetRoot naar LXC /opt/sessy-economics-engine (vendor + engine + factuur_web)."
