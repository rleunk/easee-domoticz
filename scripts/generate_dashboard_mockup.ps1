# Generate sanitized Domoticz dashboard mockups for README (no real user data).
# Uses P-max photo icons from icons/*.zip — same 48px assets as Easee_icons_v2.zip / domoticz_icons.py.
# Run generate_photo_icon_variants.ps1 first (invoked automatically below) so zips match production.
# Output: docs/screenshot-dashboard.png, docs/screenshot-equalizer.png

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem

$RepoRoot = Split-Path $PSScriptRoot -Parent
$DashboardPath = Join-Path $RepoRoot 'docs\screenshot-dashboard.png'
$EqualizerPath = Join-Path $RepoRoot 'docs\screenshot-equalizer.png'
$IconsDir = Join-Path $RepoRoot 'icons'
$MasterZip = Join-Path $RepoRoot 'Easee_icons_v2.zip'
$PhotoScript = Join-Path $PSScriptRoot 'generate_photo_icon_variants.ps1'
$PluginKey = 'EaseeCloudAutoDiscoveryV1000'

$TileBlue = [Drawing.Color]::FromArgb(255, 44, 151, 222)
$TileGreen = [Drawing.Color]::FromArgb(255, 22, 160, 133)
$TileOrange = [Drawing.Color]::FromArgb(255, 243, 156, 18)
$TileTeal = [Drawing.Color]::FromArgb(255, 0, 150, 136)
$BgDark = [Drawing.Color]::FromArgb(255, 26, 28, 32)
$TitleOrange = [Drawing.Color]::FromArgb(255, 230, 126, 34)
$TextWhite = [Drawing.Color]::FromArgb(255, 245, 246, 247)
$TextMuted = [Drawing.Color]::FromArgb(255, 210, 214, 220)
$ValueGreen = [Drawing.Color]::FromArgb(255, 120, 220, 120)

# README tiles: upscale 48px Domoticz assets for clearer photo detail (native Domoticz uses 48px).
$MockupIconDisplayPx = 72
$EqualizerIconDisplayPx = 80

Write-Host 'Refreshing icon zips via generate_photo_icon_variants.ps1 ...'
& $PhotoScript | Out-Host

if (-not (Test-Path $MasterZip)) {
    throw "Missing master icon zip after refresh: $MasterZip"
}

$script:EaseeIconCache = @{}

function Get-EaseeIconBitmap([string]$Root, [bool]$On = $true) {
    $cacheKey = "${Root}|$On"
    if (-not $script:EaseeIconCache.ContainsKey($cacheKey)) {
        $zipPath = Join-Path $IconsDir "$Root.zip"
        if (-not (Test-Path $zipPath)) {
            throw "Missing icon zip: $zipPath (run generate_photo_icon_variants.ps1)"
        }
        $suffix = if ($On) { '48_On' } else { '48_Off' }
        $entryLeaf = "${PluginKey}${Root}${suffix}.png"
        $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
        try {
            $entry = $zip.Entries | Where-Object {
                $_.FullName -eq $entryLeaf -or $_.Name -eq $entryLeaf
            } | Select-Object -First 1
            if (-not $entry) {
                throw "Entry not found in ${Root}.zip: $entryLeaf"
            }
            $ms = New-Object System.IO.MemoryStream
            $stream = $entry.Open()
            try { $stream.CopyTo($ms) } finally { $stream.Dispose() }
            $ms.Position = 0
            $script:EaseeIconCache[$cacheKey] = [Drawing.Bitmap]::FromStream($ms)
            $ms.Dispose()
            Write-Verbose "Loaded $entryLeaf from icons/$Root.zip ($($script:EaseeIconCache[$cacheKey].Width)px)"
        } finally {
            $zip.Dispose()
        }
    }
    return $script:EaseeIconCache[$cacheKey].Clone()
}

function Save-Png([Drawing.Bitmap]$Bmp, [string]$Path) {
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $Bmp.Save($Path, [Drawing.Imaging.ImageFormat]::Png)
}

function Draw-DomoticzTile(
    [Drawing.Graphics]$G,
    [int]$X, [int]$Y, [int]$W, [int]$H,
    [Drawing.Color]$Bg,
    [Drawing.Bitmap]$Icon,
    [string]$Title,
    [string]$Value,
    [string]$Mode = 'large',
    [int]$IconDisplayPx = $MockupIconDisplayPx
) {
    $tileBrush = New-Object System.Drawing.SolidBrush $Bg
    $G.FillRectangle($tileBrush, $X, $Y, $W, $H)
    $tileBrush.Dispose()

    $iconSize = [math]::Min($IconDisplayPx, [int]($W * 0.36))
    $iconX = $X + [int](($W - $iconSize) / 2)
    $iconY = $Y + [int]($H * 0.06)
    $G.DrawImage($Icon, $iconX, $iconY, $iconSize, $iconSize)

    $titleFont = New-Object System.Drawing.Font ('Segoe UI', 8.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $titleBrush = New-Object System.Drawing.SolidBrush $TextMuted
    $titleRect = New-Object System.Drawing.RectangleF ([single]($X + 6)), ([single]($Y + $H * 0.44)), ([single]($W - 12)), ([single]($H * 0.14))
    $titleSf = New-Object System.Drawing.StringFormat
    $titleSf.Alignment = [Drawing.StringAlignment]::Center
    $titleSf.LineAlignment = [Drawing.StringAlignment]::Near
    $titleSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
    $G.DrawString($Title, $titleFont, $titleBrush, $titleRect, $titleSf)
    $titleFont.Dispose(); $titleBrush.Dispose(); $titleSf.Dispose()

    if ($Mode -eq 'multiline') {
        $valueFont = New-Object System.Drawing.Font ('Segoe UI', 7.2, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
        $valueBrush = New-Object System.Drawing.SolidBrush $ValueGreen
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + 5)), ([single]($Y + $H * 0.58)), ([single]($W - 10)), ([single]($H * 0.40))
        $valueSf = New-Object System.Drawing.StringFormat
        $valueSf.Alignment = [Drawing.StringAlignment]::Near
        $valueSf.LineAlignment = [Drawing.StringAlignment]::Near
        $G.DrawString($Value, $valueFont, $valueBrush, $valueRect, $valueSf)
        $valueFont.Dispose(); $valueBrush.Dispose(); $valueSf.Dispose()
    } else {
        $valueFont = New-Object System.Drawing.Font ('Segoe UI', 15, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
        $valueBrush = New-Object System.Drawing.SolidBrush $TextWhite
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + 4)), ([single]($Y + $H * 0.64)), ([single]($W - 8)), ([single]($H * 0.28))
        $valueSf = New-Object System.Drawing.StringFormat
        $valueSf.Alignment = [Drawing.StringAlignment]::Center
        $valueSf.LineAlignment = [Drawing.StringAlignment]::Near
        $valueSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
        $G.DrawString($Value, $valueFont, $valueBrush, $valueRect, $valueSf)
        $valueFont.Dispose(); $valueBrush.Dispose(); $valueSf.Dispose()
    }
}

function New-DashboardMockup {
    $tileW = 210
    $tileH = 168
    $cols = 3
    $rows = 5
    $gap = 10
    $pad = 18
    $headerH = 42
    $canvasW = $pad * 2 + $cols * $tileW + ($cols - 1) * $gap
    $canvasH = $pad + $headerH + $rows * $tileH + ($rows - 1) * $gap + $pad

    $bmp = New-Object System.Drawing.Bitmap $canvasW, $canvasH
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear($BgDark)

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 14, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerBrush = New-Object System.Drawing.SolidBrush $TitleOrange
    $g.DrawString('Easee - Domoticz dashboard', $headerFont, $headerBrush, [single]$pad, [single]($pad - 2))
    $headerFont.Dispose(); $headerBrush.Dispose()

    # Icon roots match domoticz_icons.image_root() for each tile name/device type.
    $icons = @{
        statusGlobal = Get-EaseeIconBitmap 'EaseeStatusGlobal'
        power        = Get-EaseeIconBitmap 'EaseePower'
        cost         = Get-EaseeIconBitmap 'EaseeCost'
        overview     = Get-EaseeIconBitmap 'EaseeOverview'
        charger      = Get-EaseeIconBitmap 'EaseeCharger'
        chStatus     = Get-EaseeIconBitmap 'EaseeStatus'
        chCost       = Get-EaseeIconBitmap 'EaseeCost'
        eqEqualizer  = Get-EaseeIconBitmap 'EaseeEqualizer'
    }

    $Euro = [char]0x20AC
    $Dash = [char]0x2014
    $tiles = @(
        @{ Title = 'Easee - Status'; Value = ('Online | EQ: 1 | LB actief | Tibber actief' + [Environment]::NewLine + '2026-12-31 00:00:00'); Bg = $TileBlue; Icon = $icons.statusGlobal; Mode = 'multiline' }
        @{ Title = 'Easee - Totaal Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.power; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Easee - Totaal kWh'; Value = '0 kWh'; Bg = $TileGreen; Icon = $icons.power; Mode = 'large' }
        @{ Title = 'Kosten & Samenvatting'; Value = ('EUR' + [Environment]::NewLine + ('Kosten: {0}0.00 | Tarief: {0}0.00/kWh' -f $Euro) + [Environment]::NewLine + ('Energy: {0}0.00 | Belasting: {0}0.00' -f $Euro)); Bg = $TileOrange; Icon = $icons.cost; Mode = 'multiline' }
        @{ Title = 'Beste laden'; Value = ('00:00 - 00:00 | {0}0.00/kWh' -f $Euro); Bg = $TileTeal; Icon = $icons.overview; Mode = 'multiline' }
        @{ Title = 'Garage - Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.charger; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Garage - Totaal & Sessie'; Value = '0 kWh | Sessie: 0 kWh'; Bg = $TileGreen; Icon = $icons.power; Mode = 'multiline' }
        @{ Title = 'Garage - Status'; Value = 'Geen auto | 00:00'; Bg = $TileBlue; Icon = $icons.chStatus; Mode = 'multiline' }
        @{ Title = 'Garage - Kosten (Sessie/Dag)'; Value = ('Sessie: {0}0.00 | Dag: {0}0.00' -f $Euro); Bg = $TileOrange; Icon = $icons.chCost; Mode = 'multiline' }
        @{ Title = 'Voordeur - Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.charger; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Voordeur - Totaal & Sessie'; Value = '0 kWh | Sessie: 0 kWh'; Bg = $TileGreen; Icon = $icons.power; Mode = 'multiline' }
        @{ Title = 'Voordeur - Status'; Value = 'Geen auto | 00:00'; Bg = $TileBlue; Icon = $icons.chStatus; Mode = 'multiline' }
        @{ Title = 'Voordeur - Kosten (Sessie/Dag)'; Value = ('Sessie: {0}0.00 | Dag: {0}0.00' -f $Euro); Bg = $TileOrange; Icon = $icons.chCost; Mode = 'multiline' }
        @{ Title = 'Meterkast - Status'; Value = ('Equalizer online' + [Environment]::NewLine + 'Load balancing: Uit' + [Environment]::NewLine + ('   Vrij: {0} / {0} / {0} A  |  Laad: {0} / {0} / {0} A' -f $Dash) + [Environment]::NewLine + 'eMobility: 0 A | Hoofd: 0 A | Limiet: 0 A' + [Environment]::NewLine + 'Spanning L1/L2/L3: 0 V / 0 V / 0 V'); Bg = $TileBlue; Icon = $icons.eqEqualizer; Mode = 'multiline' }
        @{ Title = 'Meterkast - Vermogen'; Value = ('Import: 0 W | Terug: 0 W' + [Environment]::NewLine + 'Netto: 0 W' + [Environment]::NewLine + 'Vandaag import: 0.000 kWh | netto: +0.000 kWh'); Bg = $TileBlue; Icon = $icons.eqEqualizer; Mode = 'multiline' }
    )

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $col = $i % $cols
        $row = [math]::Floor($i / $cols)
        $x = $pad + $col * ($tileW + $gap)
        $y = $pad + $headerH + $row * ($tileH + $gap)
        $tile = $tiles[$i]
        Draw-DomoticzTile $g $x $y $tileW $tileH $tile.Bg $tile.Icon $tile.Title $tile.Value $tile.Mode
        if ($tile.Sub -and $tile.Mode -eq 'large') {
            $subFont = New-Object System.Drawing.Font ('Segoe UI', 8, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
            $subBrush = New-Object System.Drawing.SolidBrush $ValueGreen
            $subRect = New-Object System.Drawing.RectangleF ([single]($x + 4)), ([single]($y + $tileH - 28)), ([single]($tileW - 8)), ([single]20)
            $subSf = New-Object System.Drawing.StringFormat
            $subSf.Alignment = [Drawing.StringAlignment]::Center
            $g.DrawString($tile.Sub, $subFont, $subBrush, $subRect, $subSf)
            $subFont.Dispose(); $subBrush.Dispose(); $subSf.Dispose()
        }
    }

    foreach ($icon in $icons.Values) { $icon.Dispose() }
    $g.Dispose()
    return $bmp
}

function New-EqualizerCloseupMockup {
    $pad = 18
    $rowH = 92
    $iconSize = $EqualizerIconDisplayPx
    $canvasW = 760
    $canvasH = $pad + 36 + 3 * $rowH + $pad

    $bmp = New-Object System.Drawing.Bitmap $canvasW, $canvasH
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear($BgDark)

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 14, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerBrush = New-Object System.Drawing.SolidBrush $TitleOrange
    $g.DrawString('Equalizer & Status-iconen (demo)', $headerFont, $headerBrush, [single]$pad, [single]($pad - 2))
    $headerFont.Dispose(); $headerBrush.Dispose()

    $Dash = [char]0x2014
    $rows = @(
        @{
            Label = 'EaseeStatusGlobal - combo v10.9.18 (EQ linksonder, laadpaal rechtsboven, badge i)'
            Icon = Get-EaseeIconBitmap 'EaseeStatusGlobal'
            Value = 'Online | EQ: 1 | 2026-12-31 00:00:00'
        }
        @{
            Label = 'Meterkast - Status - load balancing uit, fase-detail'
            Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Value = ('Load balancing: Uit | Vrij/Laad: {0} / {0} / {0}' -f $Dash) + [Environment]::NewLine + 'Spanning: 0 V / 0 V / 0 V'
        }
        @{
            Label = 'Meterkast - Vermogen - import/terug/netto W + vandaag kWh'
            Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Value = 'Import: 0 W | Terug: 0 W | Netto: 0 W' + [Environment]::NewLine + 'Vandaag import: 0.000 kWh | netto: +0.000 kWh'
        }
    )

    $labelFont = New-Object System.Drawing.Font ('Segoe UI', 9.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $valueFont = New-Object System.Drawing.Font ('Segoe UI', 8.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $labelBrush = New-Object System.Drawing.SolidBrush $TextMuted
    $valueBrush = New-Object System.Drawing.SolidBrush $ValueGreen

    for ($i = 0; $i -lt $rows.Count; $i++) {
        $y = $pad + 36 + $i * $rowH
        $tileBrush = New-Object System.Drawing.SolidBrush $TileBlue
        $g.FillRectangle($tileBrush, $pad, $y, $iconSize + 8, $iconSize + 8)
        $tileBrush.Dispose()
        $g.DrawImage($rows[$i].Icon, $pad + 4, $y + 4, $iconSize, $iconSize)

        $textX = $pad + $iconSize + 24
        $g.DrawString($rows[$i].Label, $labelFont, $labelBrush, [single]$textX, [single]($y + 4))
        $valueRect = New-Object System.Drawing.RectangleF ([single]$textX), ([single]($y + 28)), ([single]($canvasW - $textX - $pad)), ([single]($rowH - 30))
        $g.DrawString($rows[$i].Value, $valueFont, $valueBrush, $valueRect)
        $rows[$i].Icon.Dispose()
    }

    $labelFont.Dispose(); $valueFont.Dispose(); $labelBrush.Dispose(); $valueBrush.Dispose()
    $g.Dispose()
    return $bmp
}

$dashboard = New-DashboardMockup
Save-Png $dashboard $DashboardPath
$dashboard.Dispose()

$equalizer = New-EqualizerCloseupMockup
Save-Png $equalizer $EqualizerPath
$equalizer.Dispose()

foreach ($cached in $script:EaseeIconCache.Values) { $cached.Dispose() }

Write-Output "Created $DashboardPath"
Write-Output "Created $EqualizerPath"
