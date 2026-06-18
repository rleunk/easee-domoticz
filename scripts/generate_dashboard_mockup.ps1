# Generate sanitized Domoticz dashboard mockups for README (no real user data).
# Domoticz-faithful tile chrome: navy page, light-blue header bar, white body (icon left / text right),
# footer buttons [Log] [Aanpassen] [Notificaties], yellow favourite star bottom-left.
# Uses P-max photo icons from icons/*.zip — same 48px assets as Easee_icons_v2.zip / domoticz_icons.py.
# Run generate_photo_icon_variants.ps1 first (invoked automatically below).
# Output: docs/screenshot-dashboard.png (11 tiles), docs/screenshot-equalizer.png

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

# Domoticz dark-theme palette
$BgNavy = [Drawing.Color]::FromArgb(255, 35, 44, 54)
$TileBorder = [Drawing.Color]::FromArgb(255, 60, 68, 78)
$HeaderBlue = [Drawing.Color]::FromArgb(255, 72, 158, 214)
$HeaderBlueDark = [Drawing.Color]::FromArgb(255, 58, 138, 196)
$BodyWhite = [Drawing.Color]::FromArgb(255, 248, 248, 248)
$BodyTextColor = [Drawing.Color]::FromArgb(255, 55, 58, 62)
$BodyTextMuted = [Drawing.Color]::FromArgb(255, 100, 105, 112)
$ButtonBlue = [Drawing.Color]::FromArgb(255, 51, 122, 183)
$ButtonBlueHover = [Drawing.Color]::FromArgb(255, 40, 96, 144)
$ButtonText = [Drawing.Color]::FromArgb(255, 255, 255, 255)
$StarYellow = [Drawing.Color]::FromArgb(255, 255, 193, 7)
$StarOutline = [Drawing.Color]::FromArgb(255, 200, 150, 0)

$TileIconDisplayPx = 56
$EqualizerIconDisplayPx = 56

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

function Draw-RoundedRect([Drawing.Graphics]$G, [Drawing.Brush]$Brush, [single]$X, [single]$Y, [single]$W, [single]$H, [single]$R) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc($X, $Y, $R * 2, $R * 2, 180, 90)
    $path.AddArc($X + $W - $R * 2, $Y, $R * 2, $R * 2, 270, 90)
    $path.AddArc($X + $W - $R * 2, $Y + $H - $R * 2, $R * 2, $R * 2, 0, 90)
    $path.AddArc($X, $Y + $H - $R * 2, $R * 2, $R * 2, 90, 90)
    $path.CloseFigure()
    $G.FillPath($Brush, $path)
    $path.Dispose()
}

function Draw-Star([Drawing.Graphics]$G, [single]$Cx, [single]$Cy, [single]$OuterR, [Drawing.Color]$Fill, [Drawing.Color]$Outline) {
    $points = New-Object System.Drawing.PointF[] 10
    for ($i = 0; $i -lt 10; $i++) {
        $angle = [math]::PI / 2 + $i * [math]::PI / 5
        $r = if ($i % 2 -eq 0) { $OuterR } else { $OuterR * 0.42 }
        $points[$i] = [Drawing.PointF]::new(
            $Cx + [single]([math]::Cos($angle) * $r),
            $Cy - [single]([math]::Sin($angle) * $r)
        )
    }
    $fillBrush = New-Object System.Drawing.SolidBrush $Fill
    $outlinePen = New-Object System.Drawing.Pen $Outline, 0.8
    $G.FillPolygon($fillBrush, $points)
    $G.DrawPolygon($outlinePen, $points)
    $fillBrush.Dispose(); $outlinePen.Dispose()
}

function Draw-DomoticzFooterButton(
    [Drawing.Graphics]$G,
    [single]$X, [single]$Y, [single]$W, [single]$H,
    [string]$Label
) {
    $brush = New-Object System.Drawing.SolidBrush $ButtonBlue
    Draw-RoundedRect $G $brush $X $Y $W $H 2.5
    $brush.Dispose()

    $font = New-Object System.Drawing.Font ('Segoe UI', 7.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $textBrush = New-Object System.Drawing.SolidBrush $ButtonText
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [Drawing.StringAlignment]::Center
    $sf.LineAlignment = [Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF $X, $Y, $W, $H
    $G.DrawString($Label, $font, $textBrush, $rect, $sf)
    $font.Dispose(); $textBrush.Dispose(); $sf.Dispose()
}

function Draw-DomoticzTile(
    [Drawing.Graphics]$G,
    [int]$X, [int]$Y, [int]$W, [int]$H,
    [Drawing.Bitmap]$Icon,
    [string]$Title,
    [string]$HeaderValue,
    [string]$BodyText,
    [string[]]$FooterButtons = @('Log', 'Aanpassen'),
    [bool]$ShowStar = $true,
    [int]$IconDisplayPx = $TileIconDisplayPx
) {
    $headerH = 28
    $footerH = 26
    $bodyH = $H - $headerH - $footerH
    $radius = 3.0

    # Tile shadow / border
    $borderPen = New-Object System.Drawing.Pen $TileBorder, 1.0
    $G.DrawRectangle($borderPen, $X, $Y, $W - 1, $H - 1)
    $borderPen.Dispose()

    # Header bar (light blue)
    $headerBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Rectangle $X, $Y, $W, $headerH),
        $HeaderBlue,
        $HeaderBlueDark,
        [Drawing.Drawing2D.LinearGradientMode]::Vertical
    )
    $G.FillRectangle($headerBrush, $X, $Y, $W, $headerH)
    $headerBrush.Dispose()

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 8.5, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $headerValueFont = New-Object System.Drawing.Font ('Segoe UI', 8.5, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerBrush2 = New-Object System.Drawing.SolidBrush $ButtonText
    $pad = 8

    $titleRect = New-Object System.Drawing.RectangleF ([single]($X + $pad)), ([single]($Y + 5)), ([single]($W * 0.58)), ([single]18)
    $titleSf = New-Object System.Drawing.StringFormat
    $titleSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
    $G.DrawString($Title, $headerFont, $headerBrush2, $titleRect, $titleSf)

    if ($HeaderValue) {
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + $W * 0.38)), ([single]($Y + 5)), ([single]($W * 0.58 - $pad)), ([single]18)
        $valueSf = New-Object System.Drawing.StringFormat
        $valueSf.Alignment = [Drawing.StringAlignment]::Far
        $valueSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
        $G.DrawString($HeaderValue, $headerValueFont, $headerBrush2, $valueRect, $valueSf)
        $valueSf.Dispose()
    }

    $headerFont.Dispose(); $headerValueFont.Dispose(); $headerBrush2.Dispose(); $titleSf.Dispose()

    # Body (white, icon left, text right)
    $bodyY = $Y + $headerH
    $bodyBrush = New-Object System.Drawing.SolidBrush $BodyWhite
    $G.FillRectangle($bodyBrush, $X, $bodyY, $W, $bodyH)
    $bodyBrush.Dispose()

    $iconSize = [math]::Min($IconDisplayPx, [int]($bodyH - 12))
    $iconX = $X + 10
    $iconY = $bodyY + [int](($bodyH - $iconSize) / 2)
    $G.DrawImage($Icon, $iconX, $iconY, $iconSize, $iconSize)

    $textX = $iconX + $iconSize + 8
    $textW = $W - ($textX - $X) - 8
    $bodyFont = New-Object System.Drawing.Font ('Segoe UI', 8.0, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $bodyBrush2 = New-Object System.Drawing.SolidBrush $BodyTextColor
    $textRect = New-Object System.Drawing.RectangleF ([single]$textX), ([single]($bodyY + 6)), ([single]$textW), ([single]($bodyH - 10))
    $textSf = New-Object System.Drawing.StringFormat
    $textSf.Alignment = [Drawing.StringAlignment]::Near
    $textSf.LineAlignment = [Drawing.StringAlignment]::Near
    $G.DrawString($BodyText, $bodyFont, $bodyBrush2, $textRect, $textSf)
    $bodyFont.Dispose(); $bodyBrush2.Dispose(); $textSf.Dispose()

    # Footer button row
    $footerY = $bodyY + $bodyH
    $footerBg = New-Object System.Drawing.SolidBrush ([Drawing.Color]::FromArgb(255, 235, 237, 240))
    $G.FillRectangle($footerBg, $X, $footerY, $W, $footerH)
    $footerBg.Dispose()

    $btnGap = 4
    $btnPad = 6
    $btnCount = $FooterButtons.Count
    $btnW = [single](($W - 2 * $btnPad - ($btnCount - 1) * $btnGap) / $btnCount)
    $btnH = [single]($footerH - 8)
    for ($bi = 0; $bi -lt $btnCount; $bi++) {
        $bx = [single]($X + $btnPad + $bi * ($btnW + $btnGap))
        $by = [single]($footerY + 4)
        Draw-DomoticzFooterButton $G $bx $by $btnW $btnH $FooterButtons[$bi]
    }

    # Yellow favourite star (bottom-left of tile)
    if ($ShowStar) {
        Draw-Star $G ([single]($X + 11)) ([single]($Y + $H - 9)) 5.5 $StarYellow $StarOutline
    }
}

function New-DashboardMockup {
    # Grid: 4 rows × 3 columns = 11 tiles (3+3+3+2)
    $tileW = 272
    $tileH = 178
    $cols = 3
    $rows = 4
    $gap = 8
    $pad = 12
    $canvasW = $pad * 2 + $cols * $tileW + ($cols - 1) * $gap
    $canvasH = $pad * 2 + $rows * $tileH + ($rows - 1) * $gap

    $bmp = New-Object System.Drawing.Bitmap $canvasW, $canvasH
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear($BgNavy)

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
    $NL = [Environment]::NewLine
    $stdButtons = @('Log', 'Aanpassen', 'Notificaties')
    $basicButtons = @('Log', 'Aanpassen')

    $tiles = @(
        @{
            Title = 'Easee - Status'; HeaderValue = ''; Icon = $icons.statusGlobal
            Body = "Online | EQ: 1${NL}2026-12-31 00:00:00"
            Buttons = $stdButtons
        }
        @{
            Title = 'Easee - Totaal Laden'; HeaderValue = '0 Watt'; Icon = $icons.power
            Body = "Vandaag: 0.000 kWh"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Totaal kWh'; HeaderValue = '0 kWh'; Icon = $icons.power
            Body = '0.000 kWh vandaag'
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Kosten & Samenvatting'; HeaderValue = ''; Icon = $icons.cost
            Body = "Kosten: ${Euro}0.00 | Tarief: ${Euro}0.00/kWh${NL}Energy: ${Euro}0.00 | Belasting: ${Euro}0.00"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Beste laden'; HeaderValue = ''; Icon = $icons.overview
            Body = "00:00 - 00:00 | ${Euro}0.00/kWh"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Lader 1 - Laden'; HeaderValue = '0 Watt'; Icon = $icons.charger
            Body = "Vandaag: 0.000 kWh"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Lader 1 - Totaal & Sessie'; HeaderValue = '0 kWh'; Icon = $icons.power
            Body = "Sessie: 0.000 kWh"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Lader 1 - Status'; HeaderValue = ''; Icon = $icons.chStatus
            Body = "Geen auto | 00:00"
            Buttons = $stdButtons
        }
        @{
            Title = 'Easee - Lader 1 - Kosten (Sessie/Dag)'; HeaderValue = ''; Icon = $icons.chCost
            Body = "Sessie: ${Euro}0.00 | Dag: ${Euro}0.00"
            Buttons = $basicButtons
        }
        @{
            Title = 'Easee - Meterkast - Status'; HeaderValue = ''; Icon = $icons.eqEqualizer
            Body = "Equalizer online${NL}Load balancing: Uit${NL}Vrij/Laad: ${Dash} / ${Dash} / ${Dash} A${NL}Spanning L1/L2/L3: 0 V / 0 V / 0 V"
            Buttons = $stdButtons
        }
        @{
            Title = 'Easee - Meterkast - Vermogen'; HeaderValue = '0 Watt'; Icon = $icons.eqEqualizer
            Body = "Import: 0 W | Terug: 0 W${NL}Netto: 0 W${NL}Vandaag import: 0.000 kWh | netto: +0.000 kWh"
            Buttons = $basicButtons
        }
    )

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $col = $i % $cols
        $row = [math]::Floor($i / $cols)
        $x = $pad + $col * ($tileW + $gap)
        $y = $pad + $row * ($tileH + $gap)
        $tile = $tiles[$i]
        Draw-DomoticzTile $g $x $y $tileW $tileH $tile.Icon $tile.Title $tile.HeaderValue $tile.Body $tile.Buttons
    }

    foreach ($icon in $icons.Values) { $icon.Dispose() }
    $g.Dispose()
    return $bmp
}

function New-EqualizerCloseupMockup {
    $tileW = 520
    $tileH = 178
    $gap = 10
    $pad = 14
    $canvasW = $pad * 2 + $tileW
    $canvasH = $pad * 2 + 3 * $tileH + 2 * $gap

    $bmp = New-Object System.Drawing.Bitmap $canvasW, $canvasH
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear($BgNavy)

    $Dash = [char]0x2014
    $NL = [Environment]::NewLine
    $stdButtons = @('Log', 'Aanpassen', 'Notificaties')
    $basicButtons = @('Log', 'Aanpassen')

    $tiles = @(
        @{
            Title = 'Easee - Status'; HeaderValue = ''; Icon = Get-EaseeIconBitmap 'EaseeStatusGlobal'
            Body = "Online | EQ: 1${NL}2026-12-31 00:00:00"
            Buttons = $stdButtons
        }
        @{
            Title = 'Easee - Meterkast - Status'; HeaderValue = ''; Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Body = "Equalizer online${NL}Load balancing: Uit${NL}Vrij/Laad: ${Dash} / ${Dash} / ${Dash} A${NL}Spanning L1/L2/L3: 0 V / 0 V / 0 V"
            Buttons = $stdButtons
        }
        @{
            Title = 'Easee - Meterkast - Vermogen'; HeaderValue = '0 Watt'; Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Body = "Import: 0 W | Terug: 0 W${NL}Netto: 0 W${NL}Vandaag import: 0.000 kWh | netto: +0.000 kWh"
            Buttons = $basicButtons
        }
    )

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $y = $pad + $i * ($tileH + $gap)
        Draw-DomoticzTile $g $pad $y $tileW $tileH $tiles[$i].Icon $tiles[$i].Title $tiles[$i].HeaderValue $tiles[$i].Body $tiles[$i].Buttons $true $EqualizerIconDisplayPx
        $tiles[$i].Icon.Dispose()
    }

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

Write-Output "Created $DashboardPath (11 tiles, grid 3+3+3+2)"
Write-Output "Created $EqualizerPath"
