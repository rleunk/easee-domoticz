# Generate sanitized Domoticz dashboard mockups for README (no real user data).
# Output: docs/screenshot-dashboard.png, docs/screenshot-equalizer.png

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$RepoRoot = Split-Path $PSScriptRoot -Parent
$DashboardPath = Join-Path $RepoRoot 'docs\screenshot-dashboard.png'
$EqualizerPath = Join-Path $RepoRoot 'docs\screenshot-equalizer.png'

$global:EaseeIconsDotSourceOnly = $true
. (Join-Path $PSScriptRoot 'generate_icons.ps1')

$TileBlue = [Drawing.Color]::FromArgb(255, 44, 151, 222)
$TileGreen = [Drawing.Color]::FromArgb(255, 22, 160, 133)
$TileOrange = [Drawing.Color]::FromArgb(255, 243, 156, 18)
$TileTeal = [Drawing.Color]::FromArgb(255, 0, 150, 136)
$BgDark = [Drawing.Color]::FromArgb(255, 26, 28, 32)
$TitleOrange = [Drawing.Color]::FromArgb(255, 230, 126, 34)
$TextWhite = [Drawing.Color]::FromArgb(255, 245, 246, 247)
$TextMuted = [Drawing.Color]::FromArgb(255, 210, 214, 220)
$ValueGreen = [Drawing.Color]::FromArgb(255, 120, 220, 120)

$BlueAccent = [Drawing.Color]::FromArgb(255, 33, 150, 243)
$GreenAccent = [Drawing.Color]::FromArgb(255, 46, 160, 67)
$YellowAccent = [Drawing.Color]::FromArgb(255, 255, 193, 7)
$OrangeAccent = [Drawing.Color]::FromArgb(255, 255, 152, 0)
$TealAccent = [Drawing.Color]::FromArgb(255, 0, 150, 136)

function Get-StatusGlobalChargerOverlayScale([int]$Size) {
    if ($Size -le 16) { return 0.72 }
    if ($Size -le 48) { return 0.70 }
    return 0.68
}

function Get-EqualizerPuckOverlayScale([int]$Size) {
    if ($Size -le 16) { return 0.50 }
    if ($Size -le 48) { return 0.46 }
    return 0.44
}

function Add-FunctionBadge([Drawing.Graphics]$G, [int]$Size, [string]$Glyph, [Drawing.Color]$Accent, [bool]$Dim) {
    $badge = if ($Size -le 16) { 8 } else { 17 }
    $margin = if ($Size -le 16) { 0 } else { 1 }
    $bx = $Size - $badge - $margin
    $by = $Size - $badge - $margin
    $fill = if ($Dim) {
        [Drawing.Color]::FromArgb(220, [math]::Max(0, [int]($Accent.R * 0.55 + 40)), [math]::Max(0, [int]($Accent.G * 0.55 + 40)), [math]::Max(0, [int]($Accent.B * 0.55 + 40)))
    } else { $Accent }
    $brush = New-Object System.Drawing.SolidBrush $fill
    $G.FillEllipse($brush, $bx, $by, $badge, $badge)
    $brush.Dispose()
    $fontSize = if ($Size -le 16) { 5.5 } else { 11.0 }
    $font = New-Object System.Drawing.Font ('Segoe UI', [single]$fontSize, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $textBrush = New-Object System.Drawing.SolidBrush ([Drawing.Color]::White)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [Drawing.StringAlignment]::Center
    $sf.LineAlignment = [Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF ([single]$bx), ([single]$by), ([single]$badge), ([single]$badge)
    $G.DrawString($Glyph, $font, $textBrush, $rect, $sf)
    $font.Dispose(); $textBrush.Dispose(); $sf.Dispose()
}

function New-StatusGlobalComboIcon([int]$Size, [bool]$Dim = $false) {
    $bmp = New-Object System.Drawing.Bitmap $Size, $Size, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.Clear([Drawing.Color]::Transparent)

    $margin = if ($Size -le 16) { 0 } else { 1 }
    $eqSize = [math]::Max(6, [int][math]::Round($Size * (Get-EqualizerPuckOverlayScale $Size)))
    $eqIcon = New-EaseeIconV2 $eqSize $BlueAccent 'equalizer' $Dim $true
    $g.DrawImage($eqIcon, $margin, $Size - $eqSize - $margin, $eqSize, $eqSize)
    $eqIcon.Dispose()

    $chSize = [math]::Max(6, [int][math]::Round($Size * (Get-StatusGlobalChargerOverlayScale $Size)))
    $chIcon = New-EaseeIconV2 $chSize $BlueAccent 'status' $Dim
    $g.DrawImage($chIcon, $Size - $chSize - $margin, $margin, $chSize, $chSize)
    $chIcon.Dispose()

    Add-FunctionBadge $g $Size 'i' $BlueAccent $Dim | Out-Null
    $g.Dispose()
    return $bmp
}

function New-ChargerStatusIcon([int]$Size, [bool]$Dim = $false) {
    $bmp = New-EaseeIconV2 $Size $BlueAccent 'status' $Dim
    $out = $bmp.Clone()
    $bmp.Dispose()
    $g = [Drawing.Graphics]::FromImage($out)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    Add-FunctionBadge $g $Size 'i' $BlueAccent $Dim | Out-Null
    $g.Dispose()
    return $out
}

function New-BadgedIcon([int]$Size, [string]$Kind, [Drawing.Color]$Color, [string]$Badge, [bool]$Dim = $false, [bool]$EqMax = $false) {
    $bmp = New-EaseeIconV2 $Size $Color $Kind $Dim $EqMax
    $out = $bmp.Clone()
    $bmp.Dispose()
    if ($Badge) {
        $g = [Drawing.Graphics]::FromImage($out)
        $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
        Add-FunctionBadge $g $Size $Badge $Color $Dim | Out-Null
        $g.Dispose()
    }
    return $out
}

function Measure-TextBlock([Drawing.Graphics]$G, [string]$Text, [Drawing.Font]$Font, [int]$MaxWidth) {
    $sizeF = New-Object System.Drawing.SizeF $MaxWidth, 10000
    return $G.MeasureString($Text, $Font, $sizeF)
}

function Draw-DomoticzTile(
    [Drawing.Graphics]$G,
    [int]$X, [int]$Y, [int]$W, [int]$H,
    [Drawing.Color]$Bg,
    [Drawing.Bitmap]$Icon,
    [string]$Title,
    [string]$Value,
    [string]$Mode = 'large'
) {
    $tileBrush = New-Object System.Drawing.SolidBrush $Bg
    $G.FillRectangle($tileBrush, $X, $Y, $W, $H)
    $tileBrush.Dispose()

    $iconSize = [math]::Min(52, [int]($W * 0.28))
    $iconX = $X + [int](($W - $iconSize) / 2)
    $iconY = $Y + [int]($H * 0.08)
    $G.DrawImage($Icon, $iconX, $iconY, $iconSize, $iconSize)

    $titleFont = New-Object System.Drawing.Font ('Segoe UI', 8.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $titleBrush = New-Object System.Drawing.SolidBrush $TextMuted
    $titleRect = New-Object System.Drawing.RectangleF ([single]($X + 6)), ([single]($Y + $H * 0.42)), ([single]($W - 12)), ([single]($H * 0.14))
    $titleSf = New-Object System.Drawing.StringFormat
    $titleSf.Alignment = [Drawing.StringAlignment]::Center
    $titleSf.LineAlignment = [Drawing.StringAlignment]::Near
    $titleSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
    $G.DrawString($Title, $titleFont, $titleBrush, $titleRect, $titleSf)
    $titleFont.Dispose(); $titleBrush.Dispose(); $titleSf.Dispose()

    if ($Mode -eq 'multiline') {
        $valueFont = New-Object System.Drawing.Font ('Segoe UI', 7.2, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
        $valueBrush = New-Object System.Drawing.SolidBrush $ValueGreen
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + 5)), ([single]($Y + $H * 0.56)), ([single]($W - 10)), ([single]($H * 0.40))
        $valueSf = New-Object System.Drawing.StringFormat
        $valueSf.Alignment = [Drawing.StringAlignment]::Near
        $valueSf.LineAlignment = [Drawing.StringAlignment]::Near
        $G.DrawString($Value, $valueFont, $valueBrush, $valueRect, $valueSf)
        $valueFont.Dispose(); $valueBrush.Dispose(); $valueSf.Dispose()
    } else {
        $valueFont = New-Object System.Drawing.Font ('Segoe UI', 15, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
        $valueBrush = New-Object System.Drawing.SolidBrush $TextWhite
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + 4)), ([single]($Y + $H * 0.62)), ([single]($W - 8)), ([single]($H * 0.30))
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
    $g.Clear($BgDark)

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 14, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerBrush = New-Object System.Drawing.SolidBrush $TitleOrange
    $g.DrawString('Easee - Domoticz dashboard', $headerFont, $headerBrush, [single]$pad, [single]($pad - 2))
    $headerFont.Dispose(); $headerBrush.Dispose()

    $icons = @{
        statusGlobal = New-StatusGlobalComboIcon 48 $false
        power        = New-BadgedIcon 48 'power' $YellowAccent 'W'
        overview     = New-BadgedIcon 48 'overview' $TealAccent ([char]0x03A3)
        cost         = New-BadgedIcon 48 'cost' $OrangeAccent ([char]0x20AC)
        best         = New-BadgedIcon 48 'overview' $TealAccent ([char]0x03A3)
        charger      = New-EaseeIconV2 48 $GreenAccent 'charger' $false
        chStatus     = New-ChargerStatusIcon 48 $false
        chCost       = New-BadgedIcon 48 'cost' $OrangeAccent ([char]0x20AC)
        eqStatus     = New-BadgedIcon 48 'equalizer' $BlueAccent 'E' $false $true
        eqPower      = New-BadgedIcon 48 'equalizer' $BlueAccent 'E' $false $true
    }

    $Euro = [char]0x20AC
    $Dash = [char]0x2014
    $tiles = @(
        @{ Title = 'Easee - Status'; Value = ('Online | EQ: 1 | LB actief | Tibber actief' + [Environment]::NewLine + '2026-12-31 00:00:00'); Bg = $TileBlue; Icon = $icons.statusGlobal; Mode = 'multiline' }
        @{ Title = 'Easee - Totaal Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.power; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Easee - Totaal kWh'; Value = '0 kWh'; Bg = $TileGreen; Icon = $icons.overview; Mode = 'large' }
        @{ Title = 'Kosten & Samenvatting'; Value = ('EUR' + [Environment]::NewLine + ('Kosten: {0}0.00 | Tarief: {0}0.00/kWh' -f $Euro) + [Environment]::NewLine + ('Energy: {0}0.00 | Belasting: {0}0.00' -f $Euro)); Bg = $TileOrange; Icon = $icons.cost; Mode = 'multiline' }
        @{ Title = 'Beste laden'; Value = ('00:00 - 00:00 | {0}0.00/kWh' -f $Euro); Bg = $TileTeal; Icon = $icons.best; Mode = 'multiline' }
        @{ Title = 'Garage - Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.charger; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Garage - Totaal & Sessie'; Value = '0 kWh | Sessie: 0 kWh'; Bg = $TileGreen; Icon = $icons.power; Mode = 'multiline' }
        @{ Title = 'Garage - Status'; Value = 'Geen auto | 00:00'; Bg = $TileBlue; Icon = $icons.chStatus; Mode = 'multiline' }
        @{ Title = 'Garage - Kosten (Sessie/Dag)'; Value = ('Sessie: {0}0.00 | Dag: {0}0.00' -f $Euro); Bg = $TileOrange; Icon = $icons.chCost; Mode = 'multiline' }
        @{ Title = 'Voordeur - Laden'; Value = '0 W'; Bg = $TileBlue; Icon = $icons.charger; Mode = 'large'; Sub = 'Vandaag: 0.000 kWh' }
        @{ Title = 'Voordeur - Totaal & Sessie'; Value = '0 kWh | Sessie: 0 kWh'; Bg = $TileGreen; Icon = $icons.power; Mode = 'multiline' }
        @{ Title = 'Voordeur - Status'; Value = 'Geen auto | 00:00'; Bg = $TileBlue; Icon = $icons.chStatus; Mode = 'multiline' }
        @{ Title = 'Voordeur - Kosten (Sessie/Dag)'; Value = ('Sessie: {0}0.00 | Dag: {0}0.00' -f $Euro); Bg = $TileOrange; Icon = $icons.chCost; Mode = 'multiline' }
        @{ Title = 'Meterkast - Status'; Value = ('Equalizer online' + [Environment]::NewLine + 'Load balancing: Uit' + [Environment]::NewLine + ('   Vrij: {0} / {0} / {0} A  |  Laad: {0} / {0} / {0} A' -f $Dash) + [Environment]::NewLine + 'eMobility: 0 A | Hoofd: 0 A | Limiet: 0 A' + [Environment]::NewLine + 'Spanning L1/L2/L3: 0 V / 0 V / 0 V'); Bg = $TileBlue; Icon = $icons.eqStatus; Mode = 'multiline' }
        @{ Title = 'Meterkast - Vermogen'; Value = ('Import: 0 W | Terug: 0 W' + [Environment]::NewLine + 'Netto: 0 W' + [Environment]::NewLine + 'Vandaag import: 0.000 kWh | netto: +0.000 kWh'); Bg = $TileBlue; Icon = $icons.eqPower; Mode = 'multiline' }
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
    $iconSize = 64
    $canvasW = 760
    $canvasH = $pad + 36 + 3 * $rowH + $pad

    $bmp = New-Object System.Drawing.Bitmap $canvasW, $canvasH
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.Clear($BgDark)

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 14, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerBrush = New-Object System.Drawing.SolidBrush $TitleOrange
    $g.DrawString('Equalizer & Status-iconen (demo)', $headerFont, $headerBrush, [single]$pad, [single]($pad - 2))
    $headerFont.Dispose(); $headerBrush.Dispose()

    $Dash = [char]0x2014
    $rows = @(
        @{
            Label = 'EaseeStatusGlobal - combo v10.9.18 (EQ linksonder, laadpaal rechtsboven, badge i)'
            Icon = New-StatusGlobalComboIcon 48 $false
            Value = 'Online | EQ: 1 | 2026-12-31 00:00:00'
        }
        @{
            Label = 'Meterkast - Status - load balancing uit, fase-detail'
            Icon = New-BadgedIcon 48 'equalizer' $BlueAccent 'E' $false $true
            Value = ('Load balancing: Uit | Vrij/Laad: {0} / {0} / {0}' -f $Dash) + [Environment]::NewLine + 'Spanning: 0 V / 0 V / 0 V'
        }
        @{
            Label = 'Meterkast - Vermogen - import/terug/netto W + vandaag kWh'
            Icon = New-BadgedIcon 48 'equalizer' $BlueAccent 'E' $false $true
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

Write-Output "Created $DashboardPath"
Write-Output "Created $EqualizerPath"
