# Copy Tibber/P1 fix into local ha-sessy-economics\LXC249 (Windows).
# Run from easee-domoticz (branch cursor/sessy-p1-tibber-match-368d):

$ErrorActionPreference = "Stop"
$SrcRoot = Join-Path $PSScriptRoot "LXC249"
$DstRoot = "C:\Users\Richard\Projects\ha-sessy-economics\LXC249"

if (-not (Test-Path $DstRoot)) {
    Write-Error "Target missing: $DstRoot"
}

$maps = @(
    @{ Src = "vendor\sessy_economics"; Dst = "vendor\sessy_economics" },
    @{ Src = "sessy_economics_engine"; Dst = "sessy_economics_engine" },
    @{ Src = "sessy_factuur_web"; Dst = "sessy_factuur_web" }
)

foreach ($m in $maps) {
    $from = Join-Path $SrcRoot $m.Src
    $to = Join-Path $DstRoot $m.Dst
    if (-not (Test-Path $from)) {
        Write-Warning "Skip missing source: $from"
        continue
    }
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Copy-Item -Path (Join-Path $from "*") -Destination $to -Recurse -Force
    Write-Host ("OK: " + $m.Dst)
}

Write-Host ""
Write-Host ("Done. Files are in " + $DstRoot)
Write-Host "Next: deploy LXC249 to 192.168.10.249 and run docker compose up -d --build"
