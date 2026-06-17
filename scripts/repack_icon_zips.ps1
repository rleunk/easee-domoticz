# Repackage Easee_icons_v2.zip with Domoticz plugin-key Base names (no image re-render).
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$RepoRoot = Split-Path $PSScriptRoot -Parent
$SourceZip = Join-Path $RepoRoot 'Easee_icons_v2.zip'
$OutZip = Join-Path $RepoRoot 'Easee_icons_v2.zip'
$IconSetsZipDir = Join-Path $RepoRoot 'icons'
$PluginKey = 'EaseeCloudAutoDiscoveryV1000'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

$roots = @(
    'EaseeCharger', 'EaseeEqualizer', 'EaseePower', 'EaseeStatus', 'EaseeAlert',
    'EaseeLoadBal', 'EaseeCost', 'EaseeOverview',
    'EaseeImport', 'EaseeExport', 'EaseeNet', 'EaseeVoltage'
)

if (-not (Test-Path $SourceZip)) { throw "Missing $SourceZip" }

$extractDir = Join-Path $env:TEMP "easee-repack-src-$([guid]::NewGuid().ToString('N'))"
$masterDir = Join-Path $env:TEMP "easee-repack-master-$([guid]::NewGuid().ToString('N'))"
[System.IO.Compression.ZipFile]::ExtractToDirectory($SourceZip, $extractDir)
New-Item -ItemType Directory -Path $masterDir -Force | Out-Null
if (-not (Test-Path $IconSetsZipDir)) { New-Item -ItemType Directory -Path $IconSetsZipDir -Force | Out-Null }

foreach ($root in $roots) {
    $base = "$PluginKey$root"
    $desc = $root -replace '^Easee', 'Easee '
    $src16 = Join-Path $extractDir "$root.png"
    $src48On = Join-Path $extractDir "${root}48_On.png"
    $src48Off = Join-Path $extractDir "${root}48_Off.png"
    if (-not (Test-Path $src16)) { throw "Missing $src16 in source zip" }

    $setFolder = Join-Path $masterDir $root
    New-Item -ItemType Directory -Path $setFolder -Force | Out-Null
    Copy-Item $src16 (Join-Path $setFolder "$base.png")
    Copy-Item $src48On (Join-Path $setFolder "${base}48_On.png")
    Copy-Item $src48Off (Join-Path $setFolder "${base}48_Off.png")
    [System.IO.File]::WriteAllText(
        (Join-Path $setFolder 'icons.txt'),
        "$base;$root;$desc`n",
        $utf8NoBom
    )

    $miniDir = Join-Path $env:TEMP "easee-mini-$root-$([guid]::NewGuid().ToString('N'))"
    New-Item -ItemType Directory -Path $miniDir -Force | Out-Null
    Copy-Item (Join-Path $setFolder "$base.png") (Join-Path $miniDir "$base.png")
    Copy-Item (Join-Path $setFolder "${base}48_On.png") (Join-Path $miniDir "${base}48_On.png")
    Copy-Item (Join-Path $setFolder "${base}48_Off.png") (Join-Path $miniDir "${base}48_Off.png")
    Copy-Item (Join-Path $setFolder 'icons.txt') (Join-Path $miniDir 'icons.txt')
    $miniZip = Join-Path $IconSetsZipDir "$root.zip"
    if (Test-Path $miniZip) { Remove-Item $miniZip -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($miniDir, $miniZip)
    Remove-Item $miniDir -Recurse -Force
}

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($masterDir, $OutZip)
Remove-Item $extractDir -Recurse -Force
Remove-Item $masterDir -Recurse -Force

Write-Output "Repacked $OutZip and 12 zips in $IconSetsZipDir"
