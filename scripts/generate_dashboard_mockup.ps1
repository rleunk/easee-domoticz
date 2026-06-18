# Generate sanitized Domoticz dashboard mockups for README (no real user data).
# Domoticz-faithful tile chrome: light page, white rounded tiles, pale-blue header bar,
# body icon-left / multi-line text-right, footer star + blue buttons.
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

# Domoticz light-dashboard palette (matches real tile close-up)
$PageBg = [Drawing.Color]::FromArgb(255, 224, 224, 224)       # #E0E0E0
$TileWhite = [Drawing.Color]::FromArgb(255, 255, 255, 255)
$TileBorder = [Drawing.Color]::FromArgb(255, 196, 196, 196)
$TileShadow = [Drawing.Color]::FromArgb(36, 0, 0, 0)
$HeaderBlue = [Drawing.Color]::FromArgb(255, 217, 232, 245)   # #D9E8F5
$HeaderBorder = [Drawing.Color]::FromArgb(255, 180, 180, 180)
$HeaderText = [Drawing.Color]::FromArgb(255, 51, 51, 51)
$BodyTextColor = [Drawing.Color]::FromArgb(255, 51, 51, 51)
$BodyTextMuted = [Drawing.Color]::FromArgb(255, 115, 115, 115)
$ButtonBlue = [Drawing.Color]::FromArgb(255, 51, 122, 183)    # #337AB7
$ButtonText = [Drawing.Color]::FromArgb(255, 255, 255, 255)
$StarYellow = [Drawing.Color]::FromArgb(255, 255, 193, 7)
$StarOutline = [Drawing.Color]::FromArgb(255, 200, 150, 0)
$StarGrey = [Drawing.Color]::FromArgb(255, 189, 189, 189)
$StarGreyOutline = [Drawing.Color]::FromArgb(255, 150, 150, 150)
$FooterBg = [Drawing.Color]::FromArgb(255, 248, 248, 248)

# Tile section heights (real Domoticz proportions at this scale)
$HeaderH = 26
$BodyH = 82
$FooterH = 30
$TileIconDisplayPx = 48

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

function New-RoundedRectPath([single]$X, [single]$Y, [single]$W, [single]$H, [single]$R) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $R * 2
    $path.AddArc($X, $Y, $d, $d, 180, 90)
    $path.AddArc($X + $W - $d, $Y, $d, $d, 270, 90)
    $path.AddArc($X + $W - $d, $Y + $H - $d, $d, $d, 0, 90)
    $path.AddArc($X, $Y + $H - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Draw-RoundedRect([Drawing.Graphics]$G, [Drawing.Brush]$Brush, [single]$X, [single]$Y, [single]$W, [single]$H, [single]$R) {
    $path = New-RoundedRectPath $X $Y $W $H $R
    $G.FillPath($Brush, $path)
    $path.Dispose()
}

function Draw-RoundedRectBorder([Drawing.Graphics]$G, [Drawing.Pen]$Pen, [single]$X, [single]$Y, [single]$W, [single]$H, [single]$R) {
    $path = New-RoundedRectPath $X $Y ($W - 1) ($H - 1) $R
    $G.DrawPath($Pen, $path)
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
    Draw-RoundedRect $G $brush $X $Y $W $H 3.0
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
    [string]$StatusLine,
    [string]$LastSeen = '2026-12-31 00:00:00',
    [string]$DeviceType = 'Type: General, Text',
    [string[]]$FooterButtons = @('Log', 'Aanpassen'),
    [bool]$ShowStar = $true,
    [bool]$StarFavorite = $false,
    [int]$IconDisplayPx = $TileIconDisplayPx
) {
    $headerH = $HeaderH
    $footerH = $FooterH
    $bodyH = $BodyH
    $radius = 4.0
    $shadowOff = 2

    # Drop shadow
    $shadowBrush = New-Object System.Drawing.SolidBrush $TileShadow
    Draw-RoundedRect $G $shadowBrush ([single]($X + $shadowOff)) ([single]($Y + $shadowOff)) ([single]$W) ([single]$H) $radius
    $shadowBrush.Dispose()

    # Outer white tile
    $tileBrush = New-Object System.Drawing.SolidBrush $TileWhite
    Draw-RoundedRect $G $tileBrush ([single]$X) ([single]$Y) ([single]$W) ([single]$H) $radius
    $tileBrush.Dispose()

    $borderPen = New-Object System.Drawing.Pen $TileBorder, 1.0
    Draw-RoundedRectBorder $G $borderPen ([single]$X) ([single]$Y) ([single]$W) ([single]$H) $radius
    $borderPen.Dispose()

    # Clip to rounded rect for inner sections
    $clipPath = New-RoundedRectPath ([single]$X) ([single]$Y) ([single]$W) ([single]$H) $radius
    $G.SetClip($clipPath)
    $clipPath.Dispose()

    # Header bar (pale blue, dark text)
    $headerBrush = New-Object System.Drawing.SolidBrush $HeaderBlue
    $G.FillRectangle($headerBrush, $X, $Y, $W, $headerH)
    $headerBrush.Dispose()

    $headerBorderPen = New-Object System.Drawing.Pen $HeaderBorder, 1.0
    $G.DrawLine($headerBorderPen, $X, $Y + $headerH - 1, $X + $W, $Y + $headerH - 1)
    $headerBorderPen.Dispose()

    $headerFont = New-Object System.Drawing.Font ('Segoe UI', 8.0, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $headerValueFont = New-Object System.Drawing.Font ('Segoe UI', 8.0, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $headerTextBrush = New-Object System.Drawing.SolidBrush $HeaderText
    $pad = 7
    $headerTextY = [single]($Y + 5)

    if ($HeaderValue) {
        $valueRect = New-Object System.Drawing.RectangleF ([single]($X + $pad)), $headerTextY, ([single]($W - 2 * $pad)), ([single]16)
        $valueSf = New-Object System.Drawing.StringFormat
        $valueSf.Alignment = [Drawing.StringAlignment]::Far
        $valueSf.LineAlignment = [Drawing.StringAlignment]::Center
        $valueSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
        $G.DrawString($HeaderValue, $headerValueFont, $headerTextBrush, $valueRect, $valueSf)
        $valueSf.Dispose()
    }

    $titleMaxW = if ($HeaderValue) { [single]($W * 0.62) } else { [single]($W - 2 * $pad) }
    $titleRect = New-Object System.Drawing.RectangleF ([single]($X + $pad)), $headerTextY, $titleMaxW, ([single]16)
    $titleSf = New-Object System.Drawing.StringFormat
    $titleSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
    $titleSf.LineAlignment = [Drawing.StringAlignment]::Center
    $G.DrawString($Title, $headerFont, $headerTextBrush, $titleRect, $titleSf)

    $headerFont.Dispose(); $headerValueFont.Dispose(); $headerTextBrush.Dispose(); $titleSf.Dispose()

    # Body (white, icon left, multi-line text right)
    $bodyY = $Y + $headerH
    $bodyBrush = New-Object System.Drawing.SolidBrush $TileWhite
    $G.FillRectangle($bodyBrush, $X, $bodyY, $W, $bodyH)
    $bodyBrush.Dispose()

    $iconSize = [math]::Min($IconDisplayPx, [int]($bodyH - 6))
    $iconX = $X + 6
    $iconY = $bodyY + [int](($bodyH - $iconSize) / 2)
    $G.DrawImage($Icon, $iconX, $iconY, $iconSize, $iconSize)

    $textX = $iconX + $iconSize + 5
    $textW = $W - ($textX - $X) - 5
    $lineY = [single]($bodyY + 5)
    $lineH = 15.5
    $statusLines = @($StatusLine -split "`n" | Where-Object { $_ -ne '' })
    if ($statusLines.Count -eq 0) { $statusLines = @('') }

    $boldFont = New-Object System.Drawing.Font ('Segoe UI', 7.5, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $italicFont = New-Object System.Drawing.Font ('Segoe UI', 7.0, [Drawing.FontStyle]::Italic, [Drawing.GraphicsUnit]::Point)
    $plainFont = New-Object System.Drawing.Font ('Segoe UI', 7.0, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
    $textBrush = New-Object System.Drawing.SolidBrush $BodyTextColor
    $mutedBrush = New-Object System.Drawing.SolidBrush $BodyTextMuted
    $textSf = New-Object System.Drawing.StringFormat
    $textSf.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
    $textSf.FormatFlags = [Drawing.StringFormatFlags]::NoWrap

    $boldLineCount = [math]::Min($statusLines.Count, 3)
    for ($si = 0; $si -lt $boldLineCount; $si++) {
        $statusRect = New-Object System.Drawing.RectangleF ([single]$textX), ($lineY + $si * $lineH), ([single]$textW), $lineH
        $G.DrawString($statusLines[$si], $boldFont, $textBrush, $statusRect, $textSf)
    }

    $metaStart = $lineY + $boldLineCount * $lineH
    $line2Text = "Laatst gezien: $LastSeen"
    $line2Rect = New-Object System.Drawing.RectangleF ([single]$textX), $metaStart, ([single]$textW), $lineH
    $G.DrawString($line2Text, $italicFont, $mutedBrush, $line2Rect, $textSf)

    $line3Rect = New-Object System.Drawing.RectangleF ([single]$textX), ($metaStart + $lineH), ([single]$textW), $lineH
    $G.DrawString($DeviceType, $plainFont, $textBrush, $line3Rect, $textSf)

    $boldFont.Dispose(); $italicFont.Dispose(); $plainFont.Dispose()
    $textBrush.Dispose(); $mutedBrush.Dispose(); $textSf.Dispose()

    # Footer
    $footerY = $bodyY + $bodyH
    $footerBgBrush = New-Object System.Drawing.SolidBrush $FooterBg
    $G.FillRectangle($footerBgBrush, $X, $footerY, $W, $footerH)
    $footerBgBrush.Dispose()

    $footerBorderPen = New-Object System.Drawing.Pen $HeaderBorder, 1.0
    $G.DrawLine($footerBorderPen, $X, $footerY, $X + $W, $footerY)
    $footerBorderPen.Dispose()

    $btnGap = 4
    $btnPad = 6
    $starSpace = 22
    $btnCount = $FooterButtons.Count
    $availW = $W - $btnPad - $starSpace - $btnPad
    $btnW = [single](($availW - ($btnCount - 1) * $btnGap) / $btnCount)
    $btnH = [single]($footerH - 10)
    $btnStartX = [single]($X + $starSpace)
    for ($bi = 0; $bi -lt $btnCount; $bi++) {
        $bx = $btnStartX + $bi * ($btnW + $btnGap)
        $by = [single]($footerY + 5)
        Draw-DomoticzFooterButton $G $bx $by $btnW $btnH $FooterButtons[$bi]
    }

    if ($ShowStar) {
        $starFill = if ($StarFavorite) { $StarYellow } else { $StarGrey }
        $starOutline = if ($StarFavorite) { $StarOutline } else { $StarGreyOutline }
        Draw-Star $G ([single]($X + 11)) ([single]($footerY + $footerH - 9)) 5.5 $starFill $starOutline
    }

    $G.ResetClip()
}

function New-DashboardMockup {
    $tileW = 258
    $tileH = $HeaderH + $BodyH + $FooterH
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
    $g.Clear($PageBg)

    $icons = @{
        statusGlobal = Get-EaseeIconBitmap 'EaseeStatusGlobal'
        power        = Get-EaseeIconBitmap 'EaseePower'
        cost         = Get-EaseeIconBitmap 'EaseeCost'
        overview     = Get-EaseeIconBitmap 'EaseeOverview'
        charger      = Get-EaseeIconBitmap 'EaseeCharger'
        chStatus     = Get-EaseeIconBitmap 'EaseeStatus'
        chCost       = Get-EaseeIconBitmap 'EaseeCost'
        eqEqualizer  = Get-EaseeIconBitmap 'EaseeEqualizer'
        loadBal      = Get-EaseeIconBitmap 'EaseeLoadBal'
    }

    $Euro = [char]0x20AC
    $Check = [char]0x2705
    $RedCircle = -join [char[]]@(0xD83D, 0xDD34)
    $statusButtons = @('Log', 'Aanpassen')
    $powerButtons = @('Log', 'Aanpassen', 'Notificaties')
    $freshTs = '2026-12-31 23:03:00'
    $staleTs = '2026-12-31 18:59:00'

    $tiles = @(
        @{
            Title = 'Easee - Status'; HeaderValue = ''; Icon = $icons.statusGlobal
            Status = "$Check Online | EQ: 1"; Type = 'Type: General, Text'
            Buttons = $statusButtons; LastSeen = $freshTs; Favorite = $true
        }
        @{
            Title = 'Easee - Totaal Laden'; HeaderValue = '0 Watt'; Icon = $icons.power
            Status = 'Vandaag: 0.000 kWh'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Totaal kWh'; HeaderValue = '0 kWh'; Icon = $icons.power
            Status = '0.000 kWh vandaag'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - LoadBal'; HeaderValue = ''; Icon = $icons.loadBal
            Status = 'Uit'; Type = 'Type: General, Switch'
            Buttons = @('Log', 'Aanpassen'); LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Kosten & Samenvatting'; HeaderValue = ''; Icon = $icons.cost
            Status = "${RedCircle} EUR`nKosten: ${Euro}0.00 | Tarief: ${Euro}0.00/kWh`nEnergy: ${Euro}0.00 | Belasting: ${Euro}0.00"
            Type = 'Type: General, Text'
            Buttons = $powerButtons; LastSeen = $staleTs; Favorite = $false
        }
        @{
            Title = 'Easee - Beste laden'; HeaderValue = ''; Icon = $icons.overview
            Status = "00:00 - 00:00 | ${Euro}0.00/kWh"; Type = 'Type: General, Text'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Lader 1 - Laden'; HeaderValue = '0 Watt'; Icon = $icons.charger
            Status = 'Vandaag: 0.000 kWh'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $true
        }
        @{
            Title = 'Easee - Lader 1 - Totaal & Sessie'; HeaderValue = '0 kWh'; Icon = $icons.power
            Status = 'Sessie: 0.000 kWh'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Lader 1 - Status'; HeaderValue = ''; Icon = $icons.chStatus
            Status = 'Geen auto | 00:00'; Type = 'Type: General, Text'
            Buttons = $statusButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Lader 1 - Kosten (Sessie/Dag)'; HeaderValue = ''; Icon = $icons.chCost
            Status = "${RedCircle} Laatste sessie: ${Euro}0.00 | Dag: ${Euro}0.00"
            Type = 'Type: General, Text'
            Buttons = $powerButtons; LastSeen = $staleTs; Favorite = $false
        }
        @{
            Title = 'Easee - Meterkast - Status'; HeaderValue = ''; Icon = $icons.eqEqualizer
            Status = 'Equalizer online | LB: Uit'; Type = 'Type: General, Text'
            Buttons = $statusButtons; LastSeen = $freshTs; Favorite = $false
        }
        @{
            Title = 'Easee - Meterkast - Vermogen'; HeaderValue = '0 Watt'; Icon = $icons.eqEqualizer
            Status = 'Import: 0 W | Terug: 0 W | Netto: 0 W'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; LastSeen = $freshTs; Favorite = $false
        }
    )

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $col = $i % $cols
        $row = [math]::Floor($i / $cols)
        $x = $pad + $col * ($tileW + $gap)
        $y = $pad + $row * ($tileH + $gap)
        $tile = $tiles[$i]
        $lastSeen = if ($tile.LastSeen) { $tile.LastSeen } else { '2026-12-31 00:00:00' }
        $favorite = if ($null -ne $tile.Favorite) { [bool]$tile.Favorite } else { $false }
        Draw-DomoticzTile $g $x $y $tileW $tileH $tile.Icon $tile.Title $tile.HeaderValue $tile.Status $lastSeen $tile.Type $tile.Buttons $true $favorite
    }

    foreach ($icon in $icons.Values) { $icon.Dispose() }
    $g.Dispose()
    return $bmp
}

function New-EqualizerCloseupMockup {
    $tileW = 520
    $tileH = $HeaderH + $BodyH + $FooterH
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
    $g.Clear($PageBg)

    $Check = [char]0x2705
    $statusButtons = @('Log', 'Aanpassen')
    $powerButtons = @('Log', 'Aanpassen', 'Notificaties')

    $tiles = @(
        @{
            Title = 'Easee - Status'; HeaderValue = ''; Icon = Get-EaseeIconBitmap 'EaseeStatusGlobal'
            Status = "$Check Online | EQ: 1"; Type = 'Type: General, Text'
            Buttons = $statusButtons; Favorite = $true
        }
        @{
            Title = 'Easee - Meterkast - Status'; HeaderValue = ''; Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Status = 'Equalizer online | LB: Uit'; Type = 'Type: General, Text'
            Buttons = $statusButtons; Favorite = $false
        }
        @{
            Title = 'Easee - Meterkast - Vermogen'; HeaderValue = '0 Watt'; Icon = Get-EaseeIconBitmap 'EaseeEqualizer'
            Status = 'Import: 0 W | Terug: 0 W | Netto: 0 W'; Type = 'Type: General, kWh'
            Buttons = $powerButtons; Favorite = $false
        }
    )

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $y = $pad + $i * ($tileH + $gap)
        $favorite = if ($null -ne $tiles[$i].Favorite) { [bool]$tiles[$i].Favorite } else { $false }
        Draw-DomoticzTile $g $pad $y $tileW $tileH $tiles[$i].Icon $tiles[$i].Title $tiles[$i].HeaderValue $tiles[$i].Status '2026-12-31 23:03:00' $tiles[$i].Type $tiles[$i].Buttons $true $favorite
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

Write-Output "Created $DashboardPath (12 tiles, grid 3x4)"
Write-Output "Created $EqualizerPath"
