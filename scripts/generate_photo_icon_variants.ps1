# Generate Easee_icons_v2.zip — canonical Domoticz icon set (P-max photo charger + Equalizer-max).
# Optional: -IncludeVariants for experimental A–U / EQ preview folders (not shipped in repo).
param([switch]$IncludeVariants)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$RepoRoot = Split-Path $PSScriptRoot -Parent
$OutRoot = Join-Path $RepoRoot 'docs\icon-options'
$SourceDir = Join-Path $OutRoot 'source'
$PreviewPath = Join-Path $OutRoot 'charger-options-preview-v4-photo.png'
$PreviewLedPath = Join-Path $OutRoot 'charger-options-preview-v4-photo-led.png'
$PreviewPMaxPath = Join-Path $OutRoot 'charger-P-max-preview.png'
$FinalPreviewPath = Join-Path $OutRoot 'final-preview-charger-Pmax-equalizer-v15.png'
$FinalPreviewCombinedPath = Join-Path $OutRoot 'final-preview-combined.png'
$FinalPreviewWithHintsPath = Join-Path $OutRoot 'final-preview-with-hints.png'
$PMaxDir = Join-Path $OutRoot 'variant-P-max'
$EqualizerMaxDir = Join-Path $OutRoot 'variant-Equalizer-max'
$V2ZipPath = Join-Path $RepoRoot 'Easee_icons_v2.zip'
$OfficialPreviewPath = Join-Path $RepoRoot 'docs\icon-preview-v2.png'

$ChargerColor = [Drawing.Color]::FromArgb(255, 46, 160, 67)
$EqualizerColor = [Drawing.Color]::FromArgb(255, 33, 150, 243)
$TileBlue = [Drawing.Color]::FromArgb(255, 33, 150, 243)

$DarkSourcePath = Join-Path $SourceDir 'easee-charge-front-gray.png'
$RedSourcePath = Join-Path $SourceDir 'easee-charge-front-red.png'

$PhotoVariants = @(
    @{ Id = 'P'; Label = 'P — Foto crop (donker)'; Style = 'photo' }
    @{ Id = 'Q'; Label = 'Q — Foto + lichte rand'; Style = 'outline' }
    @{ Id = 'R'; Label = 'R — Foto + verscherpt'; Style = 'sharpen' }
    @{ Id = 'S'; Label = 'S — Rode laadpaal (foto)'; Style = 'red' }
    @{ Id = 'T'; Label = 'T — Foto-silhouet'; Style = 'silhouette' }
    @{ Id = 'U'; Label = 'U — Hybrid masker + vlak'; Style = 'hybrid' }
)

$RefVariants = @(
    @{ Id = 'H'; Label = 'H — Foto + dikke LED (vector)'; Dir = 'variant-H' }
    @{ Id = 'L'; Label = 'L — Plat schild (vector)'; Dir = 'variant-L' }
)

$LedStatusColors = @(
    @{ Name = 'Groen (geladen)'; Color = [Drawing.Color]::FromArgb(255, 46, 160, 67) }
    @{ Name = 'Geel (wacht)'; Color = [Drawing.Color]::FromArgb(255, 255, 193, 7) }
    @{ Name = 'Blauw (status)'; Color = [Drawing.Color]::FromArgb(255, 33, 150, 243) }
)

$DomoticzIconSets = @(
    @{ Name = 'EaseeCharger';   Color = [Drawing.Color]::FromArgb(255, 46, 160, 67);  Kind = 'charger' }
    @{ Name = 'EaseeEqualizer'; Color = [Drawing.Color]::FromArgb(255, 33, 150, 243); Kind = 'equalizer' }
    @{ Name = 'EaseePower';     Color = [Drawing.Color]::FromArgb(255, 255, 193, 7);  Kind = 'power' }
    @{ Name = 'EaseeStatus';    Color = [Drawing.Color]::FromArgb(255, 33, 150, 243); Kind = 'status' }
    @{ Name = 'EaseeAlert';     Color = [Drawing.Color]::FromArgb(255, 229, 57, 53);  Kind = 'alert' }
    @{ Name = 'EaseeLoadBal';   Color = [Drawing.Color]::FromArgb(255, 0, 188, 212);  Kind = 'loadbal' }
    @{ Name = 'EaseeCost';      Color = [Drawing.Color]::FromArgb(255, 255, 152, 0);  Kind = 'cost' }
    @{ Name = 'EaseeOverview';  Color = [Drawing.Color]::FromArgb(255, 0, 150, 136);  Kind = 'overview' }
)

function Save-Png([Drawing.Bitmap]$Bmp, [string]$Path) {
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $Bmp.Save($Path, [Drawing.Imaging.ImageFormat]::Png)
}

function Get-BitmapArgb([Drawing.Image]$Image) {
    $bmp = New-Object System.Drawing.Bitmap $Image.Width, $Image.Height, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.Clear([Drawing.Color]::Transparent)
    $g.DrawImage($Image, 0, 0, $Image.Width, $Image.Height)
    $g.Dispose()
    return $bmp
}

function Remove-BlackBackground([Drawing.Bitmap]$Src, [int]$Tolerance = 18) {
    $bmp = Get-BitmapArgb $Src
    $w = $bmp.Width; $h = $bmp.Height
    $visited = New-Object 'bool[,]' $w, $h
    $queue = New-Object System.Collections.Generic.Queue[object]

    function Enqueue-Seed([int]$x, [int]$y) {
        if ($x -lt 0 -or $y -lt 0 -or $x -ge $w -or $y -ge $h) { return }
        if ($visited[$x, $y]) { return }
        $c = $bmp.GetPixel($x, $y)
        if ($c.A -lt 10) { $visited[$x, $y] = $true; return }
        $lum = ($c.R + $c.G + $c.B) / 3.0
        if ($lum -le $Tolerance) {
            $visited[$x, $y] = $true
            $queue.Enqueue(@($x, $y))
        }
    }

    for ($x = 0; $x -lt $w; $x++) { Enqueue-Seed $x 0; Enqueue-Seed $x ($h - 1) }
    for ($y = 0; $y -lt $h; $y++) { Enqueue-Seed 0 $y; Enqueue-Seed ($w - 1) $y }

    while ($queue.Count -gt 0) {
        $p = $queue.Dequeue()
        $x = $p[0]; $y = $p[1]
        $bmp.SetPixel($x, $y, [Drawing.Color]::Transparent)
        foreach ($d in @(@(-1, 0), @(1, 0), @(0, -1), @(0, 1))) {
            $nx = $x + $d[0]; $ny = $y + $d[1]
            if ($nx -lt 0 -or $ny -lt 0 -or $nx -ge $w -or $ny -ge $h) { continue }
            if ($visited[$nx, $ny]) { continue }
            $c = $bmp.GetPixel($nx, $ny)
            $lum = ($c.R + $c.G + $c.B) / 3.0
            if ($lum -le $Tolerance) {
                $visited[$nx, $ny] = $true
                $queue.Enqueue(@($nx, $ny))
            }
        }
    }
    return $bmp
}

function Get-AlphaBounds([Drawing.Bitmap]$Bmp, [int]$AlphaThreshold = 8) {
    $minX = $Bmp.Width; $minY = $Bmp.Height; $maxX = -1; $maxY = -1
    for ($y = 0; $y -lt $Bmp.Height; $y++) {
        for ($x = 0; $x -lt $Bmp.Width; $x++) {
            if ($Bmp.GetPixel($x, $y).A -gt $AlphaThreshold) {
                if ($x -lt $minX) { $minX = $x }
                if ($y -lt $minY) { $minY = $y }
                if ($x -gt $maxX) { $maxX = $x }
                if ($y -gt $maxY) { $maxY = $y }
            }
        }
    }
    if ($maxX -lt 0) { return @{ X = 0; Y = 0; W = $Bmp.Width; H = $Bmp.Height } }
    return @{ X = $minX; Y = $minY; W = ($maxX - $minX + 1); H = ($maxY - $minY + 1) }
}

function Copy-BitmapRegion([Drawing.Bitmap]$Src, [hashtable]$Bounds) {
    $out = New-Object System.Drawing.Bitmap $Bounds.W, $Bounds.H, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [Drawing.Graphics]::FromImage($out)
    $g.Clear([Drawing.Color]::Transparent)
    $g.DrawImage($Src, (New-Object System.Drawing.Rectangle 0, 0, $Bounds.W, $Bounds.H),
        (New-Object System.Drawing.Rectangle $Bounds.X, $Bounds.Y, $Bounds.W, $Bounds.H),
        [Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    return $out
}

function Resize-SharpFill([Drawing.Bitmap]$Src, [int]$Size, [double]$Fill = 0.94) {
    $target = [int][math]::Floor($Size * $Fill)
    return Resize-SharpFillTarget $Src $Size $target
}

function Resize-SharpFillMargin([Drawing.Bitmap]$Src, [int]$Size, [int]$Margin = 2) {
    $target = [math]::Max(1, $Size - 2 * $Margin)
    return Resize-SharpFillTarget $Src $Size $target
}

function Get-PhotoMaxMargin([int]$Size) {
    # 48px: 1px marge → 46px inhoud (groter dan P @ 94% = 45px)
    # 16px: 0px marge → 16px inhoud (groter dan P @ 94% = 15px)
    if ($Size -le 16) { return 0 }
    return 1
}

function Resize-SharpFillTarget([Drawing.Bitmap]$Src, [int]$Size, [int]$Target) {
    if ($null -eq $Src -or $Src.Width -lt 1 -or $Src.Height -lt 1) {
        throw "Resize-SharpFillTarget: invalid source ($($Src.Width)x$($Src.Height))"
    }
    $scale = [math]::Min($Target / $Src.Width, $Target / $Src.Height)
    $newW = [math]::Max(1, [int][math]::Round($Src.Width * $scale))
    $newH = [math]::Max(1, [int][math]::Round($Src.Height * $scale))

    $scaled = New-Object System.Drawing.Bitmap $newW, $newH, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $sg = [Drawing.Graphics]::FromImage($scaled)
    $sg.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $sg.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
    $sg.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::None
    $sg.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighSpeed
    $sg.Clear([Drawing.Color]::Transparent)
    $sg.DrawImage($Src, 0, 0, $newW, $newH)
    $sg.Dispose()

    $out = New-Object System.Drawing.Bitmap $Size, $Size, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $og = [Drawing.Graphics]::FromImage($out)
    $og.Clear([Drawing.Color]::Transparent)
    $ox = [int][math]::Floor(($Size - $newW) / 2.0)
    $oy = [int][math]::Floor(($Size - $newH) / 2.0)
    $og.DrawImage($scaled, $ox, $oy)
    $og.Dispose()
    $scaled.Dispose()
    return $out
}

function Get-IconContentMetrics([Drawing.Bitmap]$Icon) {
    $b = Get-AlphaBounds $Icon
    return @{
        W = $b.W; H = $b.H; Area = ($b.W * $b.H)
        MarginTop = $b.Y; MarginBottom = ($Icon.Height - $b.Y - $b.H)
    }
}

function Apply-ColorMatrix([Drawing.Bitmap]$Src, [Drawing.Imaging.ColorMatrix]$Matrix) {
    $out = New-Object System.Drawing.Bitmap $Src.Width, $Src.Height, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $attrs = New-Object System.Drawing.Imaging.ImageAttributes
    $attrs.SetColorMatrix($Matrix)
    $g = [Drawing.Graphics]::FromImage($out)
    $g.DrawImage($Src, (New-Object System.Drawing.Rectangle 0, 0, $Src.Width, $Src.Height),
        0, 0, $Src.Width, $Src.Height, [Drawing.GraphicsUnit]::Pixel, $attrs)
    $g.Dispose()
    $attrs.Dispose()
    return $out
}

function Get-DimMatrix() {
    $m = New-Object System.Drawing.Imaging.ColorMatrix
    $m.Matrix00 = 0.45; $m.Matrix11 = 0.45; $m.Matrix22 = 0.45
    $m.Matrix33 = 0.72
    $m.Matrix40 = 0.08; $m.Matrix41 = 0.08; $m.Matrix42 = 0.08
    return $m
}

function Add-LightOutline([Drawing.Bitmap]$Src, [Drawing.Color]$OutlineColor) {
    $w = $Src.Width; $h = $Src.Height
    $out = New-Object System.Drawing.Bitmap $w, $h, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    for ($y = 0; $y -lt $h; $y++) {
        for ($x = 0; $x -lt $w; $x++) {
            $a = $Src.GetPixel($x, $y).A
            if ($a -gt 8) { continue }
            $edge = $false
            foreach ($d in @(@(-1, 0), @(1, 0), @(0, -1), @(0, 1), @(-1, -1), @(-1, 1), @(1, -1), @(1, 1))) {
                $nx = $x + $d[0]; $ny = $y + $d[1]
                if ($nx -lt 0 -or $ny -lt 0 -or $nx -ge $w -or $ny -ge $h) { continue }
                if ($Src.GetPixel($nx, $ny).A -gt 8) { $edge = $true; break }
            }
            if ($edge) { $out.SetPixel($x, $y, $OutlineColor) }
        }
    }
    $g = [Drawing.Graphics]::FromImage($out)
    $g.CompositingMode = [Drawing.Drawing2D.CompositingMode]::SourceOver
    $g.DrawImage($Src, 0, 0)
    $g.Dispose()
    return $out
}

function Apply-Sharpen([Drawing.Bitmap]$Src, [double]$Amount = 1.35) {
    $w = $Src.Width; $h = $Src.Height
    $out = New-Object System.Drawing.Bitmap $w, $h, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $kernel = @(
        @(0, -1, 0),
        @(-1, 5, -1),
        @(0, -1, 0)
    )
    for ($y = 0; $y -lt $h; $y++) {
        for ($x = 0; $x -lt $w; $x++) {
            $srcPx = $Src.GetPixel($x, $y)
            if ($srcPx.A -lt 8) { $out.SetPixel($x, $y, [Drawing.Color]::Transparent); continue }
            $r = 0.0; $gVal = 0.0; $b = 0.0; $a = 0.0; $wSum = 0.0
            for ($ky = -1; $ky -le 1; $ky++) {
                for ($kx = -1; $kx -le 1; $kx++) {
                    $sx = [math]::Min($w - 1, [math]::Max(0, $x + $kx))
                    $sy = [math]::Min($h - 1, [math]::Max(0, $y + $ky))
                    $p = $Src.GetPixel($sx, $sy)
                    if ($p.A -lt 8) { continue }
                    $k = $kernel[$ky + 1][$kx + 1]
                    $r += $p.R * $k; $gVal += $p.G * $k; $b += $p.B * $k; $a += $p.A * $k
                    $wSum += [math]::Abs($k)
                }
            }
            if ($wSum -le 0) { $out.SetPixel($x, $y, $srcPx); continue }
            $nr = [int][math]::Min(255, [math]::Max(0, $srcPx.R + ($r / $wSum - $srcPx.R) * ($Amount - 1.0)))
            $ng = [int][math]::Min(255, [math]::Max(0, $srcPx.G + ($gVal / $wSum - $srcPx.G) * ($Amount - 1.0)))
            $nb = [int][math]::Min(255, [math]::Max(0, $srcPx.B + ($b / $wSum - $srcPx.B) * ($Amount - 1.0)))
            $out.SetPixel($x, $y, [Drawing.Color]::FromArgb($srcPx.A, $nr, $ng, $nb))
        }
    }
    return $out
}

function Convert-Silhouette([Drawing.Bitmap]$Src) {
    $w = $Src.Width; $h = $Src.Height
    $out = New-Object System.Drawing.Bitmap $w, $h, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $wing = [Drawing.Color]::FromArgb(255, 8, 9, 11)
    $panel = [Drawing.Color]::FromArgb(255, 118, 120, 124)
    $bounds = Get-AlphaBounds $Src
    $cx = ($bounds.X + $bounds.X + $bounds.W - 1) / 2.0
    for ($y = 0; $y -lt $h; $y++) {
        for ($x = 0; $x -lt $w; $x++) {
            if ($Src.GetPixel($x, $y).A -lt 24) { continue }
            $relY = ($y - $bounds.Y) / [math]::Max(1.0, $bounds.H)
            $panelHalf = (0.22 - 0.06 * $relY) * $bounds.W
            $inPanel = ([math]::Abs($x - $cx) -le $panelHalf) -and ($relY -ge 0.18) -and ($relY -le 0.82)
            $out.SetPixel($x, $y, $(if ($inPanel) { $panel } else { $wing }))
        }
    }
    return $out
}

function Convert-HybridFill([Drawing.Bitmap]$Src) {
    $w = $Src.Width; $h = $Src.Height
    $out = New-Object System.Drawing.Bitmap $w, $h, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $wing = [Drawing.Color]::FromArgb(255, 6, 7, 9)
    $panel = [Drawing.Color]::FromArgb(255, 168, 170, 174)
    $ridge = [Drawing.Color]::FromArgb(255, 215, 217, 220)
    $edge = [Drawing.Color]::FromArgb(255, 72, 74, 78)
    $bounds = Get-AlphaBounds $Src
    $cx = ($bounds.X + $bounds.X + $bounds.W - 1) / 2.0
    for ($y = 0; $y -lt $h; $y++) {
        for ($x = 0; $x -lt $w; $x++) {
            if ($Src.GetPixel($x, $y).A -lt 24) { continue }
            $relY = ($y - $bounds.Y) / [math]::Max(1.0, $bounds.H)
            $panelHalfTop = 0.20 * $bounds.W
            $panelHalfBot = 0.12 * $bounds.W
            $panelHalf = $panelHalfTop + ($panelHalfBot - $panelHalfTop) * $relY
            $ridgeHalf = [math]::Max(1.0, 0.035 * $bounds.W)
            $inPanel = ([math]::Abs($x - $cx) -le $panelHalf) -and ($relY -ge 0.16) -and ($relY -le 0.86)
            $onRidge = ([math]::Abs($x - $cx) -le $ridgeHalf) -and ($relY -ge 0.16) -and ($relY -le 0.86)
            $leftEdge = $inPanel -and ([math]::Abs($x - ($cx - $panelHalf)) -le 1.2)
            $rightEdge = $inPanel -and ([math]::Abs($x - ($cx + $panelHalf)) -le 1.2)
            if ($onRidge) { $out.SetPixel($x, $y, $ridge) }
            elseif ($leftEdge -or $rightEdge) { $out.SetPixel($x, $y, $edge) }
            elseif ($inPanel) { $out.SetPixel($x, $y, $panel) }
            else { $out.SetPixel($x, $y, $wing) }
        }
    }
    return $out
}

function Get-LedGeometry([Drawing.Bitmap]$Bmp) {
    $b = Get-AlphaBounds $Bmp
    $cx = [int][math]::Round(($b.X + $b.X + $b.W - 1) / 2.0)
    $y0 = [int][math]::Round($b.Y + $b.H * 0.22)
    $y1 = [int][math]::Round($b.Y + $b.H * 0.72)
    $dotY = [int][math]::Round($b.Y + $b.H * 0.16)
    $w = if ($Bmp.Width -le 16) { 1 } else { 2 }
    return @{ Cx = $cx; Y0 = $y0; Y1 = $y1; DotY = $dotY; W = $w }
}

function Get-FunctionHintGlyph([string]$Kind) {
    switch ($Kind) {
        'charger'   { return $null }
        'power'     { return 'W' }
        'status'    { return 'i' }
        'cost'      { return [char]0x20AC }  # €
        'alert'     { return '!' }
        'overview'  { return [char]0x03A3 }  # Σ
        'equalizer' { return 'E' }
        'loadbal'   { return 'L' }
        default     { return $null }
    }
}

function Get-DimAccentColor([Drawing.Color]$Color) {
    return [Drawing.Color]::FromArgb(200,
        [math]::Max(0, [int]($Color.R * 0.55 + 40)),
        [math]::Max(0, [int]($Color.G * 0.55 + 40)),
        [math]::Max(0, [int]($Color.B * 0.55 + 40)))
}

function Add-FunctionHintOverlay([Drawing.Bitmap]$Src, [string]$Kind, [Drawing.Color]$AccentColor, [bool]$Dim) {
    $glyph = Get-FunctionHintGlyph $Kind
    if (-not $glyph) { return $Src.Clone() }

    $out = $Src.Clone()
    $size = $out.Width
    $g = [Drawing.Graphics]::FromImage($out)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $g.CompositingQuality = [Drawing.Drawing2D.CompositingQuality]::HighQuality

    $badge = if ($size -le 16) { 6 } else { 13 }
    $margin = if ($size -le 16) { 0 } else { 1 }
    $bx = $size - $badge - $margin
    $by = $size - $badge - $margin

    $accent = if ($Dim) { Get-DimAccentColor $AccentColor } else { $AccentColor }
    $bgAlpha = if ($Dim) { 175 } else { 225 }
    $bgBrush = New-Object System.Drawing.SolidBrush ([Drawing.Color]::FromArgb($bgAlpha, 12, 14, 18))
    $borderWidth = if ($size -le 16) { 1.0 } else { 1.25 }
    $borderPen = New-Object System.Drawing.Pen $accent, ([single]$borderWidth)
    $rect = New-Object System.Drawing.RectangleF ([single]$bx), ([single]$by), ([single]$badge), ([single]$badge)
    $radius = if ($size -le 16) { 1.5 } else { 3.0 }
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc($rect.X, $rect.Y, $radius * 2, $radius * 2, 180, 90)
    $path.AddArc($rect.Right - $radius * 2, $rect.Y, $radius * 2, $radius * 2, 270, 90)
    $path.AddArc($rect.Right - $radius * 2, $rect.Bottom - $radius * 2, $radius * 2, $radius * 2, 0, 90)
    $path.AddArc($rect.X, $rect.Bottom - $radius * 2, $radius * 2, $radius * 2, 90, 90)
    $path.CloseFigure()
    $g.FillPath($bgBrush, $path)
    $g.DrawPath($borderPen, $path)

    $fontSize = if ($size -le 16) { 4.25 } else { 7.5 }
    $font = New-Object System.Drawing.Font 'Segoe UI', $fontSize, ([Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush ([Drawing.Color]::FromArgb(255, 248, 250, 252))
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Center
    $format.LineAlignment = [Drawing.StringAlignment]::Center
    $g.DrawString([string]$glyph, $font, $textBrush, $rect, $format)

    $format.Dispose(); $textBrush.Dispose(); $font.Dispose()
    $path.Dispose(); $borderPen.Dispose(); $bgBrush.Dispose(); $g.Dispose()
    return $out
}

function Add-LedOverlay([Drawing.Bitmap]$Src, [Drawing.Color]$LedColor, [bool]$Dim) {
    $out = $Src.Clone()
    $led = Get-LedGeometry $out
    $alpha = if ($Dim) { 140 } else { 245 }
    $c = [Drawing.Color]::FromArgb($alpha, $LedColor.R, $LedColor.G, $LedColor.B)
    $dot = if ($Dim) { [Drawing.Color]::FromArgb(120, 110, 112, 116) } else { $c }
    for ($y = $led.Y0; $y -le $led.Y1; $y++) {
        for ($dx = -[int][math]::Floor($led.W / 2.0); $dx -le [int][math]::Floor(($led.W - 1) / 2.0); $dx++) {
            $x = $led.Cx + $dx
            if ($x -lt 0 -or $y -lt 0 -or $x -ge $out.Width -or $y -ge $out.Height) { continue }
            if ($out.GetPixel($x, $y).A -gt 8) { $out.SetPixel($x, $y, $c) }
        }
    }
    foreach ($dx in @(-1, 0, 1)) {
        foreach ($dy in @(-1, 0, 1)) {
            $x = $led.Cx + $dx; $y = $led.DotY + $dy
            if ($x -lt 0 -or $y -lt 0 -or $x -ge $out.Width -or $y -ge $out.Height) { continue }
            if ($out.GetPixel($x, $y).A -gt 8) { $out.SetPixel($x, $y, $dot) }
        }
    }
    return $out
}

function Test-ShapeNotV([Drawing.Bitmap]$Icon48) {
    $b = Get-AlphaBounds $Icon48
    function Get-RowWidth([int]$y) {
        $left = $Icon48.Width; $right = -1
        for ($x = 0; $x -lt $Icon48.Width; $x++) {
            if ($Icon48.GetPixel($x, $y).A -gt 8) {
                if ($x -lt $left) { $left = $x }
                if ($x -gt $right) { $right = $x }
            }
        }
        if ($right -lt 0) { return 0 }
        return ($right - $left + 1)
    }
    $yTop = [int][math]::Round($b.Y + $b.H * 0.08)
    $yShoulder = [int][math]::Round($b.Y + $b.H * 0.18)
    $yTaper = [int][math]::Round($b.Y + $b.H * 0.58)
    $wTop = Get-RowWidth $yTop
    $wShoulder = Get-RowWidth $yShoulder
    $wTaper = Get-RowWidth $yTaper
    $shoulderRatio = if ($wTop -gt 0) { $wShoulder / $wTop } else { 0 }
    $taperRatio = if ($wTop -gt 0) { $wTaper / $wTop } else { 0 }
    $flatTopOk = ($shoulderRatio -ge 0.88)
    $shouldersOk = ($taperRatio -ge 0.85)
    return @{
        TopWidth = $wTop; ShoulderWidth = $wShoulder; TaperWidth = $wTaper
        ShoulderRatio = [math]::Round($shoulderRatio, 3)
        TaperRatio = [math]::Round($taperRatio, 3)
        FlatTopOk = $flatTopOk
        NotV = ($flatTopOk -and $shouldersOk)
    }
}

function Import-PhotoSource([string]$Path, [switch]$AggressiveCrop) {
    if (-not (Test-Path $Path)) { throw "Source photo missing: $Path" }
    $img = [Drawing.Image]::FromFile($Path)
    $tolerance = 20
    $noBg = Remove-BlackBackground (Get-BitmapArgb $img) $tolerance
    $img.Dispose()
    $bounds = Get-AlphaBounds $noBg 8
    if ($AggressiveCrop) {
        $pad = 0
        # Tweede pass: trim faint edge alpha zodat schouders dichter op crop zitten
        $tight = Get-AlphaBounds $noBg 24
        if ($tight.W -gt 0 -and $tight.H -gt 0) { $bounds = $tight }
    } else {
        $pad = [int][math]::Max(2, [math]::Round([math]::Min($bounds.W, $bounds.H) * 0.01))
    }
    $bounds.X = [math]::Max(0, $bounds.X - $pad)
    $bounds.Y = [math]::Max(0, $bounds.Y - $pad)
    $bounds.W = [math]::Max(1, [math]::Min($noBg.Width - $bounds.X, $bounds.W + 2 * $pad))
    $bounds.H = [math]::Max(1, [math]::Min($noBg.Height - $bounds.Y, $bounds.H + 2 * $pad))
    $cropped = Copy-BitmapRegion $noBg $bounds
    $noBg.Dispose()
    return $cropped
}

function New-PhotoVariantIcon([Drawing.Bitmap]$DarkCrop, [Drawing.Bitmap]$RedCrop, [string]$Style, [int]$Size, [bool]$Dim, [Drawing.Color]$LedColor, [Drawing.Bitmap]$DarkCropMax = $null, [string]$Kind = 'charger', [bool]$WithHint = $false) {
    $baseSrc = if ($Style -eq 'red') { $RedCrop } elseif ($Style -eq 'photo-max' -and $DarkCropMax) { $DarkCropMax } else { $DarkCrop }
    if ($Style -eq 'photo-max') {
        $icon = Resize-SharpFillMargin $baseSrc $Size (Get-PhotoMaxMargin $Size)
    } else {
        $icon = Resize-SharpFill $baseSrc $Size 0.94
    }

    switch ($Style) {
        'photo-max' { break }
        'outline' {
            $outline = if ($Dim) {
                [Drawing.Color]::FromArgb(180, 190, 192, 196)
            } else {
                [Drawing.Color]::FromArgb(255, 225, 228, 232)
            }
            $tmp = Add-LightOutline $icon $outline
            $icon.Dispose(); $icon = $tmp
        }
        'sharpen' {
            $tmp = Apply-Sharpen $icon 1.45
            $icon.Dispose(); $icon = $tmp
        }
        'silhouette' {
            $tmp = Convert-Silhouette $icon
            $icon.Dispose(); $icon = $tmp
        }
        'hybrid' {
            $tmp = Convert-HybridFill $icon
            $icon.Dispose(); $icon = $tmp
        }
    }

    if ($Dim) {
        $tmp = Apply-ColorMatrix $icon (Get-DimMatrix)
        $icon.Dispose(); $icon = $tmp
    }

    if ($Style -ne 'silhouette') {
        $tmp = Add-LedOverlay $icon $LedColor $Dim
        $icon.Dispose(); $icon = $tmp
    }

    if ($WithHint) {
        $tmp = Add-FunctionHintOverlay $icon $Kind $LedColor $Dim
        $icon.Dispose(); $icon = $tmp
    }

    return $icon
}

function New-ProductionIcon([hashtable]$Set, [int]$Size, [bool]$Dim, [Drawing.Bitmap]$DarkCrop, [Drawing.Bitmap]$RedCrop, [Drawing.Bitmap]$DarkCropMax) {
    if ($Set.Kind -in @('equalizer', 'loadbal')) {
        $icon = New-EaseeIconV2 $Size $Set.Color $Set.Kind $Dim $true
        $hinted = Add-FunctionHintOverlay $icon $Set.Kind $Set.Color $Dim
        $icon.Dispose()
        return $hinted
    }
    return New-PhotoVariantIcon $DarkCrop $RedCrop 'photo-max' $Size $Dim $Set.Color $DarkCropMax $Set.Kind $true
}

function Draw-Label([Drawing.Graphics]$G, [string]$Text, [int]$X, [int]$Y, [Drawing.Color]$Color, [single]$Size = 8.5) {
    $font = New-Object System.Drawing.Font 'Segoe UI', $Size, ([Drawing.FontStyle]::Regular)
    $brush = New-Object System.Drawing.SolidBrush $Color
    $G.DrawString($Text, $font, $brush, [single]$X, [single]$Y)
    $brush.Dispose(); $font.Dispose()
}

function Draw-IconOnTile([Drawing.Graphics]$G, [Drawing.Bitmap]$Icon, [int]$TileX, [int]$TileY, [int]$TileSize, [Drawing.Color]$TileColor) {
    $tileBrush = New-Object System.Drawing.SolidBrush $TileColor
    $G.FillRectangle($tileBrush, $TileX, $TileY, $TileSize, $TileSize)
    $tileBrush.Dispose()
    $offset = [int](($TileSize - $Icon.Width) / 2)
    $G.DrawImage($Icon, ($TileX + $offset), ($TileY + $offset))
}

# --- Ensure source photos ---
if (-not (Test-Path $SourceDir)) { New-Item -ItemType Directory -Path $SourceDir -Force | Out-Null }

$SourceDownloads = @{
    'easee-charge-front-gray.png' = 'https://easee.com/wp-content/uploads/2024/08/ev-charger_front-gray.png'
    'easee-charge-front-red.png'  = 'https://easee.com/wp-content/uploads/2024/08/ev-charger_front-red.png'
}
foreach ($kv in $SourceDownloads.GetEnumerator()) {
    $out = Join-Path $SourceDir $kv.Key
    if (-not (Test-Path $out)) {
        Invoke-WebRequest -Uri $kv.Value -OutFile $out -UseBasicParsing
        Write-Output "Downloaded $($kv.Key)"
    }
}

if (-not (Test-Path $DarkSourcePath) -or -not (Test-Path $RedSourcePath)) {
    throw "Download source photos first to $SourceDir (easee-charge-front-gray.png, easee-charge-front-red.png)."
}

$darkCrop = Import-PhotoSource $DarkSourcePath
$redCrop = Import-PhotoSource $RedSourcePath
$darkCropMax = Import-PhotoSource $DarkSourcePath -AggressiveCrop
$redCropMax = Import-PhotoSource $RedSourcePath -AggressiveCrop

# --- Generate P-U folders (optional) ---
$shapeReport = New-Object System.Collections.Generic.List[string]

if ($IncludeVariants) {
foreach ($v in $PhotoVariants) {
    $dir = Join-Path $OutRoot ("variant-{0}" -f $v.Id)
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

    $on48 = New-PhotoVariantIcon $darkCrop $redCrop $v.Style 48 $false $ChargerColor
    $off48 = New-PhotoVariantIcon $darkCrop $redCrop $v.Style 48 $true $ChargerColor
    $on16 = New-PhotoVariantIcon $darkCrop $redCrop $v.Style 16 $false $ChargerColor

    Save-Png $on48 (Join-Path $dir 'EaseeCharger48_On.png')
    Save-Png $off48 (Join-Path $dir 'EaseeCharger48_Off.png')
    Save-Png $on16 (Join-Path $dir 'EaseeCharger16_On.png')

    $shape = Test-ShapeNotV $on48
    $shapeReport.Add("$($v.Id): shoulder/top=$($shape.ShoulderRatio) taper/top=$($shape.TaperRatio) notV=$($shape.NotV)")

    $on48.Dispose(); $off48.Dispose(); $on16.Dispose()
}

# --- v4 preview: H/L vector refs + photo P-U ---
$previewRows = @()
foreach ($r in $RefVariants) {
    $previewRows += @{
        Label = $r.Label
        Color = [Drawing.Color]::FromArgb(255, 200, 202, 206)
        On48Path = Join-Path $OutRoot ($r.Dir + '\EaseeCharger48_On.png')
        On16Path = Join-Path $OutRoot ($r.Dir + '\EaseeCharger16_On.png')
    }
}
foreach ($v in $PhotoVariants) {
    $previewRows += @{
        Label = $v.Label
        Color = [Drawing.Color]::FromArgb(255, 180, 230, 200)
        On48Path = Join-Path $OutRoot ("variant-{0}\EaseeCharger48_On.png" -f $v.Id)
        On16Path = Join-Path $OutRoot ("variant-{0}\EaseeCharger16_On.png" -f $v.Id)
    }
}

$labelW = 190; $pad = 10; $rowH = 68; $headerH = 52
$tile48 = 56; $tile16 = 28; $gap = 16
$gridW = $labelW + $tile48 + $gap + $tile16 + 2 * $pad
$gridH = $headerH + $previewRows.Count * $rowH + $pad
$preview = New-Object System.Drawing.Bitmap $gridW, $gridH
$pg = [Drawing.Graphics]::FromImage($preview)
$pg.Clear([Drawing.Color]::FromArgb(255, 16, 18, 22))
$pg.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit

Draw-Label $pg 'V4 — foto-varianten vs vector H/L' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $pg 'Variant' 8 ($headerH - 26) ([Drawing.Color]::White)
Draw-Label $pg '48px op tegel' ($labelW + $pad) ($headerH - 26) ([Drawing.Color]::FromArgb(255, 180, 220, 255))
Draw-Label $pg '16px op tegel' ($labelW + $pad + $tile48 + $gap) ($headerH - 26) ([Drawing.Color]::FromArgb(255, 180, 220, 255))

for ($i = 0; $i -lt $previewRows.Count; $i++) {
    $row = $previewRows[$i]
    $y = $headerH + $i * $rowH + 6
    Draw-Label $pg $row.Label 8 ($y + 18) $row.Color 8.5

    $on48 = [Drawing.Image]::FromFile($row.On48Path)
    $on16 = [Drawing.Image]::FromFile($row.On16Path)
    $x48 = $labelW + $pad
    $x16 = $x48 + $tile48 + $gap
    Draw-IconOnTile $pg $on48 $x48 ($y + 4) $tile48 $TileBlue
    Draw-IconOnTile $pg $on16 $x16 ($y + 18) $tile16 $TileBlue
    $on48.Dispose(); $on16.Dispose()
}

$pg.Dispose()
Save-Png $preview $PreviewPath
$preview.Dispose()

# --- LED color preview (variant P, green/yellow/blue) ---
$darkCrop2 = Import-PhotoSource $DarkSourcePath
$redCrop2 = Import-PhotoSource $RedSourcePath
$ledLabelW = 150; $ledPad = 10; $ledRowH = 64; $ledHeaderH = 40
$ledGridW = $ledLabelW + 3 * ($tile48 + $ledPad) + $ledPad
$ledGridH = $ledHeaderH + $LedStatusColors.Count * $ledRowH + $ledPad
$ledPreview = New-Object System.Drawing.Bitmap $ledGridW, $ledGridH
$lg = [Drawing.Graphics]::FromImage($ledPreview)
$lg.Clear([Drawing.Color]::FromArgb(255, 16, 18, 22))
$lg.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit

Draw-Label $lg 'LED-kleuren op variant P (foto)' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $lg 'Status' 8 ($ledHeaderH - 18) ([Drawing.Color]::White)
Draw-Label $lg '48px' ($ledLabelW + $ledPad) ($ledHeaderH - 18) ([Drawing.Color]::FromArgb(255, 180, 220, 255))
Draw-Label $lg '16px' ($ledLabelW + $ledPad + $tile48 + $ledPad) ($ledHeaderH - 18) ([Drawing.Color]::FromArgb(255, 180, 220, 255))
Draw-Label $lg '48px uit' ($ledLabelW + $ledPad + 2 * ($tile48 + $ledPad)) ($ledHeaderH - 18) ([Drawing.Color]::FromArgb(255, 160, 160, 160))

for ($i = 0; $i -lt $LedStatusColors.Count; $i++) {
    $led = $LedStatusColors[$i]
    $y = $ledHeaderH + $i * $ledRowH + 6
    Draw-Label $lg $led.Name 8 ($y + 18) ([Drawing.Color]::FromArgb(255, 220, 222, 226)) 8.5

    $on48 = New-PhotoVariantIcon $darkCrop2 $redCrop2 'photo' 48 $false $led.Color
    $on16 = New-PhotoVariantIcon $darkCrop2 $redCrop2 'photo' 16 $false $led.Color
    $off48 = New-PhotoVariantIcon $darkCrop2 $redCrop2 'photo' 48 $true $led.Color

    $x0 = $ledLabelW + $ledPad
    Draw-IconOnTile $lg $on48 $x0 ($y + 4) $tile48 $TileBlue
    Draw-IconOnTile $lg $on16 ($x0 + $tile48 + $ledPad) ($y + 18) $tile16 $TileBlue
    Draw-IconOnTile $lg $off48 ($x0 + 2 * ($tile48 + $ledPad)) ($y + 4) $tile48 $TileBlue

    $on48.Dispose(); $on16.Dispose(); $off48.Dispose()
}

$darkCrop2.Dispose(); $redCrop2.Dispose()
$lg.Dispose()
Save-Png $ledPreview $PreviewLedPath
$ledPreview.Dispose()

# --- P-max: maximale vulling op tegel (agressieve crop + 2px marge) ---
if (-not (Test-Path $PMaxDir)) { New-Item -ItemType Directory -Path $PMaxDir -Force | Out-Null }

$pOn48 = New-PhotoVariantIcon $darkCrop $redCrop 'photo' 48 $false $ChargerColor
$pMaxOn48 = New-PhotoVariantIcon $darkCrop $redCrop 'photo-max' 48 $false $ChargerColor $darkCropMax
$pOn16 = New-PhotoVariantIcon $darkCrop $redCrop 'photo' 16 $false $ChargerColor
$pMaxOn16 = New-PhotoVariantIcon $darkCrop $redCrop 'photo-max' 16 $false $ChargerColor $darkCropMax
$rOn48 = New-PhotoVariantIcon $darkCrop $redCrop 'sharpen' 48 $false $ChargerColor
$rOn16 = New-PhotoVariantIcon $darkCrop $redCrop 'sharpen' 16 $false $ChargerColor

$pMetrics48 = Get-IconContentMetrics $pOn48
$pMaxMetrics48 = Get-IconContentMetrics $pMaxOn48
$pMetrics16 = Get-IconContentMetrics $pOn16
$pMaxMetrics16 = Get-IconContentMetrics $pMaxOn16
$heightGain48 = [math]::Round((($pMaxMetrics48.H / [math]::Max(1, $pMetrics48.H)) - 1.0) * 100.0, 1)
$widthGain48 = [math]::Round((($pMaxMetrics48.W / [math]::Max(1, $pMetrics48.W)) - 1.0) * 100.0, 1)
$heightGain16 = [math]::Round((($pMaxMetrics16.H / [math]::Max(1, $pMetrics16.H)) - 1.0) * 100.0, 1)
$widthGain16 = [math]::Round((($pMaxMetrics16.W / [math]::Max(1, $pMetrics16.W)) - 1.0) * 100.0, 1)
$areaGain48 = [math]::Round((($pMaxMetrics48.Area / [math]::Max(1, $pMetrics48.Area)) - 1.0) * 100.0, 1)

$pMaxOff48 = New-PhotoVariantIcon $darkCrop $redCrop 'photo-max' 48 $true $ChargerColor $darkCropMax
Save-Png $pMaxOn48 (Join-Path $PMaxDir 'EaseeCharger48_On.png')
Save-Png $pMaxOff48 (Join-Path $PMaxDir 'EaseeCharger48_Off.png')
Save-Png $pMaxOn16 (Join-Path $PMaxDir 'EaseeCharger16_On.png')
$pMaxOff48.Dispose()

# --- P-max preview: P vs P-max vs R on blue tile ---
$pmaxRows = @(
    @{ Label = ('P - origineel (94% fill)'); On48 = $pOn48; On16 = $pOn16; Color = [Drawing.Color]::FromArgb(255, 180, 230, 200) }
    @{ Label = ('P-max - max vulling (+' + $heightGain48 + ' pct hoogte, +' + $widthGain48 + ' pct breed 48px)'); On48 = $pMaxOn48; On16 = $pMaxOn16; Color = [Drawing.Color]::FromArgb(255, 140, 255, 180) }
    @{ Label = 'R - verscherpt (referentie)'; On48 = $rOn48; On16 = $rOn16; Color = [Drawing.Color]::FromArgb(255, 200, 220, 255) }
)

$pmaxLabelW = 220; $pmaxPad = 10; $pmaxRowH = 68; $pmaxHeaderH = 56
$pmaxGridW = $pmaxLabelW + $tile48 + $gap + $tile16 + 2 * $pmaxPad
$pmaxGridH = $pmaxHeaderH + $pmaxRows.Count * $pmaxRowH + $pmaxPad
$pmaxPreview = New-Object System.Drawing.Bitmap $pmaxGridW, $pmaxGridH
$pmg = [Drawing.Graphics]::FromImage($pmaxPreview)
$pmg.Clear([Drawing.Color]::FromArgb(255, 16, 18, 22))
$pmg.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit

Draw-Label $pmg 'P vs P-max vs R - blauwe Domoticz-tegel' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $pmg ('P: {0}x{1}px 48 | P-max: {2}x{3}px (+{4} pct H, +{5} pct B) | marge 1px/0px' -f $pMetrics48.W, $pMetrics48.H, $pMaxMetrics48.W, $pMaxMetrics48.H, $heightGain48, $widthGain48) 8 26 ([Drawing.Color]::FromArgb(255, 180, 190, 200)) 8
Draw-Label $pmg 'Variant' 8 ($pmaxHeaderH - 26) ([Drawing.Color]::White)
Draw-Label $pmg '48px op tegel' ($pmaxLabelW + $pmaxPad) ($pmaxHeaderH - 26) ([Drawing.Color]::FromArgb(255, 180, 220, 255))
Draw-Label $pmg '16px op tegel' ($pmaxLabelW + $pmaxPad + $tile48 + $gap) ($pmaxHeaderH - 26) ([Drawing.Color]::FromArgb(255, 180, 220, 255))

for ($i = 0; $i -lt $pmaxRows.Count; $i++) {
    $row = $pmaxRows[$i]
    $y = $pmaxHeaderH + $i * $pmaxRowH + 6
    Draw-Label $pmg $row.Label 8 ($y + 18) $row.Color 8.5
    $x48 = $pmaxLabelW + $pmaxPad
    $x16 = $x48 + $tile48 + $gap
    Draw-IconOnTile $pmg $row.On48 $x48 ($y + 4) $tile48 $TileBlue
    Draw-IconOnTile $pmg $row.On16 $x16 ($y + 18) $tile16 $TileBlue
}

$pmg.Dispose()
Save-Png $pmaxPreview $PreviewPMaxPath
$pmaxPreview.Dispose()

$pOn48.Dispose(); $pOn16.Dispose(); $rOn48.Dispose(); $rOn16.Dispose()
} # end IncludeVariants

# --- Equalizer-max: v10.5.15 squircle, max tile fill (1 px @48, 0 px @16) ---
if (-not (Test-Path $EqualizerMaxDir)) { New-Item -ItemType Directory -Path $EqualizerMaxDir -Force | Out-Null }
$global:EaseeIconsDotSourceOnly = $true
. (Join-Path $PSScriptRoot 'generate_icons.ps1')
$eqMaxOn48 = New-EaseeIconV2 48 $EqualizerColor 'equalizer' $false $true
$eqMaxOff48 = New-EaseeIconV2 48 $EqualizerColor 'equalizer' $true $true
$eqMaxOn16 = New-EaseeIconV2 16 $EqualizerColor 'equalizer' $false $true
$eqV15On48 = New-EaseeIconV2 48 $EqualizerColor 'equalizer' $false $false
$eqMetricsV15 = Get-IconContentMetrics $eqV15On48
$eqMetricsMax = Get-IconContentMetrics $eqMaxOn48
$eqHeightGain48 = [math]::Round((($eqMetricsMax.H / [math]::Max(1, $eqMetricsV15.H)) - 1.0) * 100.0, 1)
$eqWidthGain48 = [math]::Round((($eqMetricsMax.W / [math]::Max(1, $eqMetricsV15.W)) - 1.0) * 100.0, 1)
$eqAreaGain48 = [math]::Round((($eqMetricsMax.Area / [math]::Max(1, $eqMetricsV15.Area)) - 1.0) * 100.0, 1)
Save-Png $eqMaxOn48 (Join-Path $EqualizerMaxDir 'EaseeEqualizer48_On.png')
Save-Png $eqMaxOff48 (Join-Path $EqualizerMaxDir 'EaseeEqualizer48_Off.png')
Save-Png $eqMaxOn16 (Join-Path $EqualizerMaxDir 'EaseeEqualizer16_On.png')
$lbSet = $DomoticzIconSets | Where-Object { $_.Kind -eq 'loadbal' } | Select-Object -First 1
$lbMaxOn48 = New-EaseeIconV2 48 $lbSet.Color 'loadbal' $false $true
$lbMaxOff48 = New-EaseeIconV2 48 $lbSet.Color 'loadbal' $true $true
$lbMaxOn16 = New-EaseeIconV2 16 $lbSet.Color 'loadbal' $false $true
Save-Png $lbMaxOn48 (Join-Path $EqualizerMaxDir 'EaseeLoadBal48_On.png')
Save-Png $lbMaxOff48 (Join-Path $EqualizerMaxDir 'EaseeLoadBal48_Off.png')
Save-Png $lbMaxOn16 (Join-Path $EqualizerMaxDir 'EaseeLoadBal16_On.png')

# --- P-max zip + canonical v2: P-max laadpalen + Equalizer-max puck ---
$zipTemp = Join-Path $env:TEMP "easee-pmax-icons-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $zipTemp -Force | Out-Null
foreach ($set in $DomoticzIconSets) {
    $name = $set.Name
    $on16 = New-ProductionIcon $set 16 $false $darkCrop $redCrop $darkCropMax
    $on48 = New-ProductionIcon $set 48 $false $darkCrop $redCrop $darkCropMax
    $off48 = New-ProductionIcon $set 48 $true $darkCrop $redCrop $darkCropMax
    Save-Png $on16 (Join-Path $zipTemp "$name.png")
    Save-Png $on48 (Join-Path $zipTemp "${name}48_On.png")
    Save-Png $off48 (Join-Path $zipTemp "${name}48_Off.png")
    $on16.Dispose(); $on48.Dispose(); $off48.Dispose()
}
$zipLines = New-Object System.Collections.Generic.List[string]
foreach ($set in $DomoticzIconSets) {
    $desc = $set.Name -replace '^Easee', 'Easee '
    $zipLines.Add("$($set.Name);$($set.Name);$desc")
}
$iconsTxtPath = Join-Path $zipTemp 'icons.txt'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($iconsTxtPath, ($zipLines -join "`n") + "`n", $utf8NoBom)
if (Test-Path $V2ZipPath) { Remove-Item $V2ZipPath -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($zipTemp, $V2ZipPath)
Remove-Item $zipTemp -Recurse -Force

if ($IncludeVariants) {
# --- Final preview: P-max charger + Equalizer-max on blue tile ---
$finalCharger48 = New-PhotoVariantIcon $darkCrop $redCrop 'photo-max' 48 $false $ChargerColor $darkCropMax
$finalEqualizer48 = New-EaseeIconV2 48 $EqualizerColor 'equalizer' $false $true
$finalPad = 12; $finalLabelW = 220; $finalTile = 48; $finalGap = 16; $finalRowH = 72
$finalW = $finalPad + $finalLabelW + $finalGap + $finalTile + $finalGap + $finalTile + $finalPad
$finalH = $finalPad + 36 + $finalRowH + $finalPad
$finalPreview = New-Object System.Drawing.Bitmap $finalW, $finalH
$fg = [Drawing.Graphics]::FromImage($finalPreview)
$fg.Clear([Drawing.Color]::FromArgb(255, 28, 30, 34))
Draw-Label $fg 'P-max laadpaal + Equalizer-max (48px op blauwe tegel)' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $fg 'EaseeCharger (P-max)' 8 ($finalPad + 36 + 18) ([Drawing.Color]::FromArgb(255, 140, 255, 180)) 8.5
Draw-Label $fg 'EaseeEqualizer (max)' 8 ($finalPad + 36 + 18 + 28) ([Drawing.Color]::FromArgb(255, 170, 210, 255)) 8.5
$xCharger = $finalLabelW + $finalGap
$xEqualizer = $xCharger + $finalTile + $finalGap
$yTile = $finalPad + 36 + 4
Draw-IconOnTile $fg $finalCharger48 $xCharger $yTile $finalTile $TileBlue
Draw-IconOnTile $fg $finalEqualizer48 $xEqualizer $yTile $finalTile $TileBlue
$fg.Dispose()
Save-Png $finalPreview $FinalPreviewPath
$finalCharger48.Dispose(); $finalEqualizer48.Dispose(); $eqV15On48.Dispose()

# --- Combined preview: all 8 icon sets @48px on blue tile with labels ---
$combinedLabelW = 200; $combinedPad = 10; $combinedTile = 48; $combinedRowH = 56; $combinedHeaderH = 44
$Euro = [char]0x20AC
$Sigma = [char]0x03A3
$combinedRows = @(
    @{ Label = 'EaseeCharger - groen, laden (geen hint)'; Hint = $null; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeCharger' }) }
    @{ Label = 'EaseePower - geel, vermogen W/kW'; Hint = 'W'; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseePower' }) }
    @{ Label = 'EaseeStatus - blauw, core status'; Hint = 'i'; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeStatus' }) }
    @{ Label = "EaseeCost - oranje, kosten $Euro"; Hint = $Euro; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeCost' }) }
    @{ Label = 'EaseeAlert - rood, fout/waarschuwing'; Hint = '!'; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeAlert' }) }
    @{ Label = "EaseeOverview - teal, overzicht $Sigma"; Hint = $Sigma; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeOverview' }) }
    @{ Label = 'EaseeEqualizer - blauw, EQ/charger status'; Hint = 'E'; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeEqualizer' }) }
    @{ Label = 'EaseeLoadBal - teal, load balancing'; Hint = 'L'; Set = ($DomoticzIconSets | Where-Object { $_.Name -eq 'EaseeLoadBal' }) }
)
$combinedW = $combinedPad + $combinedLabelW + $combinedPad + $combinedTile + $combinedPad
$combinedH = $combinedHeaderH + $combinedRows.Count * $combinedRowH + $combinedPad
$combinedPreview = New-Object System.Drawing.Bitmap $combinedW, $combinedH
$cg = [Drawing.Graphics]::FromImage($combinedPreview)
$cg.Clear([Drawing.Color]::FromArgb(255, 28, 30, 34))
$cg.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
Draw-Label $cg 'P-max laadpalen + Equalizer-max — alle 8 sets (48 px op blauwe tegel)' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $cg 'Iconenset / LED-kleur' 8 ($combinedHeaderH - 20) ([Drawing.Color]::White) 8.5
Draw-Label $cg '48 px' ($combinedLabelW + $combinedPad) ($combinedHeaderH - 20) ([Drawing.Color]::FromArgb(255, 180, 220, 255)) 8.5
for ($i = 0; $i -lt $combinedRows.Count; $i++) {
    $row = $combinedRows[$i]
    $set = $row.Set
    $y = $combinedHeaderH + $i * $combinedRowH + 8
    Draw-Label $cg $row.Label 8 ($y + 14) ([Drawing.Color]::FromArgb(255, 210, 212, 216)) 8.5
    $icon = New-ProductionIcon $set 48 $false $darkCrop $redCrop $darkCropMax
    Draw-IconOnTile $cg $icon ($combinedLabelW + $combinedPad) ($y + 2) $combinedTile $TileBlue
    $icon.Dispose()
}
$cg.Dispose()
Save-Png $combinedPreview $FinalPreviewCombinedPath
$combinedPreview.Dispose()
} # end IncludeVariants (extra previews)

# --- Final preview with hints: 48px + 16px, tile function labels ---
$hintLabelW = 240; $hintPad = 10; $hintTile48 = 48; $hintTile16 = 28; $hintGap = 14; $hintRowH = 58; $hintHeaderH = 52
$hintRows = $combinedRows
$hintW = $hintPad + $hintLabelW + $hintGap + $hintTile48 + $hintGap + $hintTile16 + $hintPad
$hintH = $hintHeaderH + $hintRows.Count * $hintRowH + $hintPad
$hintPreview = New-Object System.Drawing.Bitmap $hintW, $hintH
$hg = [Drawing.Graphics]::FromImage($hintPreview)
$hg.Clear([Drawing.Color]::FromArgb(255, 20, 22, 26))
$hg.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit
Draw-Label $hg 'P-max + hints — LED-kleur + functie-badge (rechtsonder)' 8 8 ([Drawing.Color]::FromArgb(255, 255, 220, 160)) 10
Draw-Label $hg 'Tegelfunctie / hint' 8 ($hintHeaderH - 22) ([Drawing.Color]::White) 8.5
Draw-Label $hg '48 px' ($hintLabelW + $hintGap) ($hintHeaderH - 22) ([Drawing.Color]::FromArgb(255, 180, 220, 255)) 8.5
Draw-Label $hg '16 px' ($hintLabelW + $hintGap + $hintTile48 + $hintGap) ($hintHeaderH - 22) ([Drawing.Color]::FromArgb(255, 180, 220, 255)) 8.5
for ($i = 0; $i -lt $hintRows.Count; $i++) {
    $row = $hintRows[$i]
    $set = $row.Set
    $y = $hintHeaderH + $i * $hintRowH + 6
    $hintText = if (-not $row.Hint) { 'geen badge' } else { "badge $($row.Hint)" }
    Draw-Label $hg $row.Label 8 ($y + 8) ([Drawing.Color]::FromArgb(255, 210, 212, 216)) 8.5
    Draw-Label $hg $hintText 8 ($y + 24) ([Drawing.Color]::FromArgb(255, 150, 155, 165)) 7.5
    $icon48 = New-ProductionIcon $set 48 $false $darkCrop $redCrop $darkCropMax
    $icon16 = New-ProductionIcon $set 16 $false $darkCrop $redCrop $darkCropMax
    $x48 = $hintLabelW + $hintGap
    $x16 = $x48 + $hintTile48 + $hintGap
    Draw-IconOnTile $hg $icon48 $x48 ($y + 4) $hintTile48 $TileBlue
    Draw-IconOnTile $hg $icon16 $x16 ($y + 14) $hintTile16 $TileBlue
    $icon48.Dispose(); $icon16.Dispose()
}
$hg.Dispose()
Save-Png $hintPreview $FinalPreviewWithHintsPath
$hintPreview.Dispose()
Copy-Item $FinalPreviewWithHintsPath $OfficialPreviewPath -Force

$eqMaxOn48.Dispose(); $eqMaxOff48.Dispose(); $eqMaxOn16.Dispose()
$lbMaxOn48.Dispose(); $lbMaxOff48.Dispose(); $lbMaxOn16.Dispose()

$darkCrop.Dispose(); $redCrop.Dispose()
$darkCropMax.Dispose(); $redCropMax.Dispose()
if ($IncludeVariants) {
    $pMaxOn48.Dispose(); $pMaxOn16.Dispose()
}

Write-Output "Created $V2ZipPath (8 icon sets: P-max laadpaal + Equalizer-max)"
Write-Output "Created $FinalPreviewWithHintsPath"
Write-Output "Created $OfficialPreviewPath"
Write-Output ('Equalizer-max vs v10.5.15 48px: {0}x{1} -> {2}x{3} px (+{4} pct H, +{5} pct W, area +{6} pct)' -f $eqMetricsV15.W, $eqMetricsV15.H, $eqMetricsMax.W, $eqMetricsMax.H, $eqHeightGain48, $eqWidthGain48, $eqAreaGain48)
if ($IncludeVariants) {
    Write-Output "Created $PreviewPath"
    Write-Output "Created $PreviewLedPath"
    Write-Output "Created $PreviewPMaxPath"
    Write-Output "Created $FinalPreviewPath"
    Write-Output "Created $FinalPreviewCombinedPath"
    Write-Output "Created $EqualizerMaxDir (Equalizer-max + LoadBal-max)"
    Write-Output ('P-max vs P 48px: {0}x{1} -> {2}x{3} px (+{4} pct H, +{5} pct W, area +{6} pct)' -f $pMetrics48.W, $pMetrics48.H, $pMaxMetrics48.W, $pMaxMetrics48.H, $heightGain48, $widthGain48, $areaGain48)
    Write-Output ('P-max vs P 16px: {0}x{1} -> {2}x{3} px (+{4} pct H, +{5} pct W)' -f $pMetrics16.W, $pMetrics16.H, $pMaxMetrics16.W, $pMaxMetrics16.H, $heightGain16, $widthGain16)
    Write-Output "Created $PMaxDir (EaseeCharger 16/48 On/Off)"
    Write-Output "Shape check (shoulder/top >= 0.88 + breedte@58% >= 85% top = plat top, geen V):"
    $shapeReport | ForEach-Object { Write-Output "  $_" }
    Write-Output "Created variant-P/ through variant-U/ under $OutRoot"
}
