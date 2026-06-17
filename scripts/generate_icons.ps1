# Vector Equalizer drawing helpers (dot-sourced; do not run standalone for production icons).

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$OutZip = Join-Path (Split-Path $PSScriptRoot -Parent) 'Easee_icons_v2.zip'
$PreviewPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'docs\icon-preview-v2.png'

$IconSets = @(
    @{ Name = 'EaseeCharger';   Color = [Drawing.Color]::FromArgb(255, 46, 160, 67);  Kind = 'charger' }
    @{ Name = 'EaseeEqualizer'; Color = [Drawing.Color]::FromArgb(255, 33, 150, 243); Kind = 'equalizer' }
    @{ Name = 'EaseePower';     Color = [Drawing.Color]::FromArgb(255, 255, 193, 7);  Kind = 'power' }
    @{ Name = 'EaseeStatus';    Color = [Drawing.Color]::FromArgb(255, 33, 150, 243); Kind = 'status' }
    @{ Name = 'EaseeAlert';     Color = [Drawing.Color]::FromArgb(255, 229, 57, 53);  Kind = 'alert' }
    @{ Name = 'EaseeLoadBal';   Color = [Drawing.Color]::FromArgb(255, 0, 188, 212);  Kind = 'loadbal' }
    @{ Name = 'EaseeCost';      Color = [Drawing.Color]::FromArgb(255, 255, 152, 0);  Kind = 'cost' }
    @{ Name = 'EaseeOverview';  Color = [Drawing.Color]::FromArgb(255, 0, 150, 136);  Kind = 'overview' }
)

function Test-Circle([int]$x, [int]$y, [double]$cx, [double]$cy, [double]$r) {
    (($x - $cx) * ($x - $cx) + ($y - $cy) * ($y - $cy)) -le ($r * $r)
}

function Test-Rect([int]$x, [int]$y, [double]$x0, [double]$y0, [double]$x1, [double]$y1) {
    ($x -ge $x0) -and ($x -le $x1) -and ($y -ge $y0) -and ($y -le $y1)
}

function Test-RoundedRect([int]$x, [int]$y, [double]$x0, [double]$y0, [double]$x1, [double]$y1, [double]$r) {
    if (-not (Test-Rect $x $y $x0 $y0 $x1 $y1)) { return $false }
    if (($x -le ($x0 + $r)) -and ($y -le ($y0 + $r))) { return (Test-Circle $x $y ($x0 + $r) ($y0 + $r) $r) }
    if (($x -ge ($x1 - $r)) -and ($y -le ($y0 + $r))) { return (Test-Circle $x $y ($x1 - $r) ($y0 + $r) $r) }
    if (($x -le ($x0 + $r)) -and ($y -ge ($y1 - $r))) { return (Test-Circle $x $y ($x0 + $r) ($y1 - $r) $r) }
    if (($x -ge ($x1 - $r)) -and ($y -ge ($y1 - $r))) { return (Test-Circle $x $y ($x1 - $r) ($y1 - $r) $r) }
    return $true
}

function Test-Trapezoid([int]$x, [int]$y, [double]$x0t, [double]$x1t, [double]$yt, [double]$x0b, [double]$x1b, [double]$yb) {
    if ($y -lt $yt -or $y -gt $yb) { return $false }
    if ($yb -eq $yt) { return (Test-Rect $x $y $x0t $yt $x1t $yt) }
    $t = ($y - $yt) / ($yb - $yt)
    $left = $x0t + $t * ($x0b - $x0t)
    $right = $x1t + $t * ($x1b - $x1t)
    return ($x -ge $left) -and ($x -le $right)
}

function Test-Ellipse([int]$x, [int]$y, [double]$cx, [double]$cy, [double]$rx, [double]$ry) {
    if ($rx -le 0 -or $ry -le 0) { return $false }
    (($x - $cx) * ($x - $cx)) / ($rx * $rx) + (($y - $cy) * ($y - $cy)) / ($ry * $ry) -le 1.0
}

function Get-AccentColor([Drawing.Color]$Color, [bool]$Dim) {
    if ($Dim) {
        return [Drawing.Color]::FromArgb(200,
            [math]::Max(0, [int]($Color.R * 0.45 + 55)),
            [math]::Max(0, [int]($Color.G * 0.45 + 55)),
            [math]::Max(0, [int]($Color.B * 0.45 + 55)))
    }
    return $Color
}

function Get-BlendColor([Drawing.Color]$From, [Drawing.Color]$To, [double]$Amount) {
    [Drawing.Color]::FromArgb($From.A,
        [int]($From.R + ($To.R - $From.R) * $Amount),
        [int]($From.G + ($To.G - $From.G) * $Amount),
        [int]($From.B + ($To.B - $From.B) * $Amount))
}

function Get-LedStripColor([Drawing.Color]$Accent, [bool]$Dim, [string]$Kind) {
    $gray = [Drawing.Color]::FromArgb(255, 102, 102, 102)
    $panel = [Drawing.Color]::FromArgb(255, 118, 120, 124)
    if ($Dim) {
        if ($Kind -eq 'charger') { return [Drawing.Color]::FromArgb(140, 102, 102, 102) }
        return Get-BlendColor (Get-AccentColor $Accent $true) $gray 0.35
    }
    return Get-BlendColor $Accent $panel 0.12
}

function Get-StatusDotColor([Drawing.Color]$Accent, [bool]$Dim) {
    $gray = [Drawing.Color]::FromArgb(255, 102, 102, 102)
    if ($Dim) { return Get-BlendColor (Get-AccentColor $Accent $true) $gray 0.55 }
    return $Accent
}

function Get-ChargerGeom([int]$Size, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0) {
    $s = ($Size / 48.0) * $Scale
    $oxs = $Ox * $s; $oys = $Oy * $s
    @{
        CapY0 = [int](5 * $s + $oys); CapY1 = [int](12 * $s + $oys)
        OuterX0t = [int](10 * $s + $oxs); OuterX1t = [int](38 * $s + $oxs)
        OuterYt = [int](12 * $s + $oys)
        OuterX0m = [int](16 * $s + $oxs); OuterX1m = [int](32 * $s + $oxs)
        OuterYm = [int](39 * $s + $oys)
        TipCx = 24 * $s + $oxs; TipCy = 41.5 * $s + $oys
        TipRx = 4.5 * $s; TipRy = 2.8 * $s
        TipY0 = [int](37 * $s + $oys)
        CapR = [math]::Max(1, [int](3.5 * $s))
        PanelX0t = [int](15 * $s + $oxs); PanelX1t = [int](33 * $s + $oxs)
        PanelYt = [int](14 * $s + $oys)
        PanelX0b = [int](19 * $s + $oxs); PanelX1b = [int](29 * $s + $oxs)
        PanelYb = [int](36 * $s + $oys)
        SocketCx = 24 * $s + $oxs; SocketCy = 41 * $s + $oys
        SocketR = [math]::Max(1, 2 * $s)
        Cx = [int](24 * $s + $oxs)
        S = $s; Oxs = $oxs; Oys = $oys
    }
}

function Test-ChargerBottomTip([int]$x, [int]$y, [hashtable]$G) {
    if ($y -lt $G.TipY0) { return $false }
    Test-Ellipse $x $y $G.TipCx $G.TipCy $G.TipRx $G.TipRy
}

function Test-ChargerShield([int]$x, [int]$y, [hashtable]$G) {
    $cap = Test-RoundedRect $x $y $G.OuterX0t $G.CapY0 $G.OuterX1t $G.CapY1 $G.CapR
    $body = Test-Trapezoid $x $y $G.OuterX0t $G.OuterX1t $G.OuterYt $G.OuterX0m $G.OuterX1m $G.OuterYm
    $tip = Test-ChargerBottomTip $x $y $G
    $cap -or $body -or $tip
}

function Test-ChargerPanel([int]$x, [int]$y, [hashtable]$G) {
    Test-Trapezoid $x $y $G.PanelX0t $G.PanelX1t $G.PanelYt $G.PanelX0b $G.PanelX1b $G.PanelYb
}

function Test-ChargerSocket([int]$x, [int]$y, [hashtable]$G) {
    Test-Circle $x $y $G.SocketCx $G.SocketCy $G.SocketR
}

function Test-ChargerLedLine([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    $cx = $G.Cx; $s = $G.S; $oys = $G.Oys
    $ledW = if ($Size -le 16) { [math]::Max(1, [int][math]::Round(1.25 * $s)) } else { [math]::Max(1, [int][math]::Round(1.75 * $s)) }
    $ledX0 = $cx - [int][math]::Floor($ledW / 2.0)
    $ledX1 = $cx + [int][math]::Floor(($ledW - 1) / 2.0)
    if ($Size -le 16) {
        $y0 = [int](14 * $s + $oys); $y1 = [int](22 * $s + $oys)
    } else {
        $y0 = [int](17 * $s + $oys); $y1 = [int](32 * $s + $oys)
    }
    return ($y -ge $y0) -and ($y -le $y1) -and ($x -ge $ledX0) -and ($x -le $ledX1)
}

function Test-ChargerLedOutline([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    if ($Size -lt 32) { return $false }
    $cx = $G.Cx; $s = $G.S; $oys = $G.Oys
    $ledW = [math]::Max(1, [int][math]::Round(1.75 * $s))
    $ledX0 = $cx - [int][math]::Floor($ledW / 2.0)
    $ledX1 = $cx + [int][math]::Floor(($ledW - 1) / 2.0)
    $y0 = [int](17 * $s + $oys); $y1 = [int](32 * $s + $oys)
    if (-not (($y -ge $y0) -and ($y -le $y1))) { return $false }
    if (($x -ne ($ledX0 - 1)) -and ($x -ne ($ledX1 + 1))) { return $false }
    Test-ChargerPanel $x $y $G
}

function Test-ChargerLedDot([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    $cx = $G.Cx; $s = $G.S; $oys = $G.Oys
    $cy = [int](16.5 * $s + $oys)
    $r = if ($Size -gt 16) { [math]::Max(1, [int](1.1 * $s)) } else { [math]::Max(1, [int](0.9 * $s)) }
    Test-Circle $x $y $cx $cy $r
}

function Test-ChargerMarkings([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    if ($Size -le 16) { return $false }
    $s = $G.S; $oys = $G.Oys; $oxs = $G.Oxs
    $y0 = [int](30 * $s + $oys); $y1 = [int](31 * $s + $oys)
    if (-not (($y -ge $y0) -and ($y -le $y1))) { return $false }
    (([int](21 * $s + $oxs) -le $x) -and ($x -le [int](22 * $s + $oxs))) -or
    (([int](26 * $s + $oxs) -le $x) -and ($x -le [int](27 * $s + $oxs)))
}

function Get-EqualizerMaxMargin([int]$Size) {
    # Match P-max photo margins: 1 px @48, 0 px @16
    if ($Size -le 16) { return 0 }
    return 1
}

function Get-EqualizerMaxScaleFactor([int]$Size) {
    $margin = Get-EqualizerMaxMargin $Size
    $center = $Size / 2.0
    $baseHalf = 14.0
    return ($center - $margin) / $baseHalf
}

function Map-EqualizerCoord48([double]$Coord48, [int]$Size, [double]$EffF) {
    $cx = $Size / 2.0
    return $cx + ($Coord48 - 24.0) * $EffF
}

function Get-EqualizerGeom([int]$Size, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0, [bool]$MaxFill = $false) {
    if ($MaxFill) {
        $effF = (Get-EqualizerMaxScaleFactor $Size) * $Scale
        $oxs = $Ox * ($Size / 48.0); $oys = $Oy * ($Size / 48.0)
        $s = $effF * ($Size / 48.0)
        return @{
            OuterX0 = [int][math]::Round((Map-EqualizerCoord48 10.0 $Size $effF) + $oxs)
            OuterY0 = [int][math]::Round((Map-EqualizerCoord48 10.0 $Size $effF) + $oys)
            OuterX1 = [int][math]::Round((Map-EqualizerCoord48 38.0 $Size $effF) + $oxs)
            OuterY1 = [int][math]::Round((Map-EqualizerCoord48 38.0 $Size $effF) + $oys)
            OuterR = [math]::Max(2, [int][math]::Round(8.0 * $effF))
            InnerCx = (Map-EqualizerCoord48 24.0 $Size $effF) + $oxs
            InnerCy = (Map-EqualizerCoord48 23.0 $Size $effF) + $oys
            InnerR = [math]::Max(3, 12.0 * $effF)
            LedCx = (Map-EqualizerCoord48 24.0 $Size $effF) + $oxs
            LedCy = (Map-EqualizerCoord48 33.5 $Size $effF) + $oys
            LedR = [math]::Max(1, 2.0 * $effF)
            S = $s; Oxs = $oxs; Oys = $oys
        }
    }
    $s = ($Size / 48.0) * $Scale
    $oxs = $Ox * $s; $oys = $Oy * $s
    return @{
        OuterX0 = [int](10 * $s + $oxs); OuterY0 = [int](10 * $s + $oys)
        OuterX1 = [int](38 * $s + $oxs); OuterY1 = [int](38 * $s + $oys)
        OuterR = [math]::Max(2, [int](8 * $s))
        InnerCx = 24 * $s + $oxs; InnerCy = 23 * $s + $oys
        InnerR = [math]::Max(3, 12 * $s)
        LedCx = 24 * $s + $oxs; LedCy = 33.5 * $s + $oys
        LedR = [math]::Max(1, 2.0 * $s)
        S = $s; Oxs = $oxs; Oys = $oys
    }
}

function Test-EqualizerOuter([int]$x, [int]$y, [hashtable]$G) {
    Test-RoundedRect $x $y $G.OuterX0 $G.OuterY0 $G.OuterX1 $G.OuterY1 $G.OuterR
}

function Test-EqualizerInnerFace([int]$x, [int]$y, [hashtable]$G) {
    Test-Circle $x $y $G.InnerCx $G.InnerCy $G.InnerR
}

function Test-EqualizerLed([int]$x, [int]$y, [hashtable]$G) {
    Test-Circle $x $y $G.LedCx $G.LedCy $G.LedR
}

function Test-EqualizerLogoE([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    if ($Size -le 16) { return $false }
    $s = $G.S; $oxs = $G.Oxs; $oys = $G.Oys
    $cx = [int](24 * $s + $oxs); $cy = [int](23 * $s + $oys)
    $stemW = [math]::Max(1, [int](1.25 * $s))
    $stemX0 = $cx - [int](2.5 * $s); $stemX1 = $stemX0 + $stemW - 1
    $stemY0 = $cy - [int](3.5 * $s); $stemY1 = $cy + [int](3 * $s)
    if (Test-Rect $x $y $stemX0 $stemY0 $stemX1 $stemY1) { return $true }
    $barY0 = $cy - [int](0.5 * $s); $barY1 = $cy + [math]::Max(0, [int](0.5 * $s) - 1)
    $barX0 = $stemX0; $barX1 = $cx + [int](2.5 * $s)
    if (Test-Rect $x $y $barX0 $barY0 $barX1 $barY1) { return $true }
    $topY0 = $cy - [int](3.5 * $s); $topY1 = $cy - [int](2.5 * $s)
    $topX0 = $stemX0; $topX1 = $cx + [int](1.5 * $s)
    if (Test-Rect $x $y $topX0 $topY0 $topX1 $topY1) { return $true }
    $botY0 = $cy + [int](2 * $s); $botY1 = $cy + [int](3 * $s)
    if (Test-Rect $x $y $topX0 $botY0 $barX1 $botY1) { return $true }
    return $false
}

function Get-EqualizerOuterColor([int]$x, [int]$y, [hashtable]$G, [bool]$Dim) {
    $w = [math]::Max(1.0, $G.OuterX1 - $G.OuterX0)
    $h = [math]::Max(1.0, $G.OuterY1 - $G.OuterY0)
    $shade = (($x - $G.OuterX0) / $w + ($y - $G.OuterY0) / $h) * 0.5
    $light = if ($Dim) {
        [Drawing.Color]::FromArgb(200, 198, 202, 208)
    } else {
        [Drawing.Color]::FromArgb(255, 248, 249, 252)
    }
    $dark = if ($Dim) {
        [Drawing.Color]::FromArgb(200, 168, 172, 178)
    } else {
        [Drawing.Color]::FromArgb(255, 218, 222, 228)
    }
    $base = Get-BlendColor $light $dark $shade
    $dx = $x - $G.InnerCx; $dy = $y - $G.InnerCy
    $dist = [math]::Sqrt($dx * $dx + $dy * $dy) - $G.InnerR
    if (($dist -ge 0) -and ($dist -le (1.4 * $G.S))) {
        return Get-BlendColor $base ([Drawing.Color]::FromArgb($base.A, 190, 194, 200)) 0.35
    }
    return $base
}

function Get-EqualizerInnerColor([bool]$Dim) {
    if ($Dim) { return [Drawing.Color]::FromArgb(200, 228, 231, 236) }
    return [Drawing.Color]::FromArgb(255, 252, 253, 255)
}

function Get-EqualizerPixel([int]$x, [int]$y, [int]$Size, [Drawing.Color]$Bright, [bool]$Dim, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0, [bool]$MaxFill = $false) {
    $G = Get-EqualizerGeom $Size -Ox $Ox -Oy $Oy -Scale $Scale -MaxFill $MaxFill
    if (-not (Test-EqualizerOuter $x $y $G)) { return $null }
    if (Test-EqualizerLed $x $y $G) { return (Get-StatusDotColor $Bright $Dim) }
    if (Test-EqualizerLogoE $x $y $Size $G) {
        $logo = if ($Dim) { [Drawing.Color]::FromArgb(200, 150, 154, 160) } else { [Drawing.Color]::FromArgb(255, 175, 178, 184) }
        return $logo
    }
    if (Test-EqualizerInnerFace $x $y $G) { return (Get-EqualizerInnerColor $Dim) }
    return (Get-EqualizerOuterColor $x $y $G $Dim)
}

function Test-ArrowLR([int]$x, [int]$y, [int]$Size, [double]$Ox = 0, [double]$Oy = 0) {
    $s = $Size / 48.0
    $oxs = $Ox * $s; $oys = $Oy * $s
    $cy = [int](24 * $s + $oys)
    $left = (Test-Rect $x $y ([int](4 * $s + $oxs)) ($cy - [int](2 * $s)) ([int](12 * $s + $oxs)) ($cy + [int](2 * $s))) -or
        (Test-Trapezoid $x $y ([int](12 * $s + $oxs)) ([int](16 * $s + $oxs)) ($cy - [int](4 * $s)) ([int](8 * $s + $oxs)) ([int](12 * $s + $oxs)) ($cy + [int](4 * $s)))
    $right = (Test-Rect $x $y ([int](36 * $s + $oxs)) ($cy - [int](2 * $s)) ([int](44 * $s + $oxs)) ($cy + [int](2 * $s))) -or
        (Test-Trapezoid $x $y ([int](32 * $s + $oxs)) ([int](36 * $s + $oxs)) ($cy - [int](4 * $s)) ([int](36 * $s + $oxs)) ([int](40 * $s + $oxs)) ($cy + [int](4 * $s)))
    $left -or $right
}

function Test-EuroBadge([int]$x, [int]$y, [int]$Size) {
    $s = $Size / 48.0
    $cx = [int](36 * $s); $cy = [int](36 * $s); $r = [int](7 * $s)
    $ring = (Test-Circle $x $y $cx $cy $r) -and -not (Test-Circle $x $y $cx $cy ([math]::Max(1, $r - [int](2 * $s))))
    $bar = Test-Rect $x $y ([int](33 * $s)) ([int](34 * $s)) ([int](39 * $s)) ([int](38 * $s))
    $ring -or $bar
}

function Get-ChargerPixel([int]$x, [int]$y, [int]$Size, [Drawing.Color]$Bright, [bool]$Dim, [string]$Kind, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0) {
    $G = Get-ChargerGeom $Size -Ox $Ox -Oy $Oy -Scale $Scale
    $wing = if ($Dim) { [Drawing.Color]::FromArgb(200, 52, 54, 58) } else { [Drawing.Color]::FromArgb(255, 18, 18, 20) }
    $panel = if ($Dim) { [Drawing.Color]::FromArgb(200, 86, 88, 92) } else { [Drawing.Color]::FromArgb(255, 118, 120, 124) }
    $led = Get-LedStripColor $Bright $Dim $Kind
    $ledAlpha = if ($Dim) { 170 } else { 204 }
    $outline = [Drawing.Color]::FromArgb(255, 38, 40, 44)

    if (-not (Test-ChargerShield $x $y $G)) { return $null }

    if ((Test-ChargerLedLine $x $y $Size $G) -or (Test-ChargerLedDot $x $y $Size $G)) {
        return [Drawing.Color]::FromArgb($ledAlpha, $led.R, $led.G, $led.B)
    }

    if (Test-ChargerLedOutline $x $y $Size $G) { return $outline }

    if (Test-ChargerPanel $x $y $G) {
        if (Test-ChargerMarkings $x $y $Size $G) {
            return Get-BlendColor $panel $wing 0.35
        }
        return $panel
    }

    if (Test-ChargerSocket $x $y $G) {
        return Get-BlendColor $wing ([Drawing.Color]::FromArgb(255, 0, 0, 0)) 0.45
    }

    return $wing
}

function Get-SymbolPixelV2([string]$Kind, [int]$x, [int]$y, [int]$Size, [Drawing.Color]$Bright, [bool]$Dim, [bool]$EqualizerMaxFill = $false) {
    $accent = Get-AccentColor $Bright $Dim
    $green = Get-AccentColor ([Drawing.Color]::FromArgb(255, 46, 160, 67)) $Dim
    $red = Get-AccentColor ([Drawing.Color]::FromArgb(255, 229, 57, 53)) $Dim

    switch ($Kind) {
        'charger' {
            $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'charger'
            if ($null -ne $px) { return $px }
        }
        'power' {
            $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'power'
            if ($null -ne $px) { return $px }
        }
        'status' {
            $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'status'
            if ($null -ne $px) { return $px }
            $cx = $Size * 0.78; $cy = $Size * 0.22
            $r = [math]::Max(1.5, $Size * 0.08); $ringR = $r + [math]::Max(1, $Size * 0.04)
            if ((Test-Circle $x $y $cx $cy $ringR) -and -not (Test-Circle $x $y $cx $cy ($r - 0.5))) { return $green }
            if (Test-Circle $x $y $cx $cy $r) { return $green }
        }
        'cost' {
            if (Test-EuroBadge $x $y $Size) { return $accent }
            $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'cost'
            if ($null -ne $px) { return $px }
        }
        'alert' {
            $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'alert'
            if ($null -ne $px) { return $px }
            $cx = $Size * 0.78; $cy = $Size * 0.18
            if (Test-Circle $x $y $cx $cy ([math]::Max(1.5, $Size * 0.07))) { return $red }
        }
        'equalizer' {
            $px = Get-EqualizerPixel $x $y $Size $Bright $Dim -MaxFill $EqualizerMaxFill
            if ($null -ne $px) { return $px }
        }
        'overview' {
            foreach ($ox in @(-7, 7)) {
                $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'overview' -Ox $ox -Scale 0.72
                if ($null -ne $px) { return $px }
            }
        }
        'loadbal' {
            $px = Get-EqualizerPixel $x $y $Size $Bright $Dim -Scale 0.82 -MaxFill $EqualizerMaxFill
            if ($null -ne $px) { return $px }
            if (Test-ArrowLR $x $y $Size) { return $accent }
        }
    }
    return $null
}

function New-EaseeIconV2([int]$Size, [Drawing.Color]$Color, [string]$Kind, [bool]$Dim, [bool]$EqualizerMaxFill = $false) {
    $bmp = New-Object System.Drawing.Bitmap $Size, $Size
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([Drawing.Color]::Transparent)
    for ($y = 0; $y -lt $Size; $y++) {
        for ($x = 0; $x -lt $Size; $x++) {
            $px = Get-SymbolPixelV2 $Kind $x $y $Size $Color $Dim $EqualizerMaxFill
            if ($null -ne $px) { $bmp.SetPixel($x, $y, $px) }
        }
    }
    $g.Dispose()
    return $bmp
}

function Save-Png([Drawing.Bitmap]$Bmp, [string]$Path) {
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $Bmp.Save($Path, [Drawing.Imaging.ImageFormat]::Png)
    if (-not $global:EaseeIconsDotSourceOnly) { $Bmp.Dispose() }
}

$Lines = New-Object System.Collections.Generic.List[string]
if ($MyInvocation.InvocationName -ne '.' -and -not $global:EaseeIconsDotSourceOnly) {
$TempDir = Join-Path $env:TEMP "easee-icons-v2-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
$docsDir = Split-Path $PreviewPath -Parent
if (-not (Test-Path $docsDir)) { New-Item -ItemType Directory -Path $docsDir -Force | Out-Null }
foreach ($set in $IconSets) {
    $name = $set.Name
    $desc = $name -replace '^Easee', 'Easee '
    $Lines.Add("$name;$name;$desc")
    Save-Png (New-EaseeIconV2 16 $set.Color $set.Kind $false) (Join-Path $TempDir "$name.png")
    Save-Png (New-EaseeIconV2 48 $set.Color $set.Kind $false) (Join-Path $TempDir "${name}48_On.png")
    Save-Png (New-EaseeIconV2 48 $set.Color $set.Kind $true) (Join-Path $TempDir "${name}48_Off.png")
}
$iconsPath = Join-Path $TempDir 'icons.txt'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($iconsPath, ($Lines -join "`n") + "`n", $utf8NoBom)

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $OutZip)
Remove-Item $TempDir -Recurse -Force

# Preview: on/off rows of 48px icons
$iconW = 48; $pad = 8; $rowH = $iconW + $pad
$totalW = $IconSets.Count * $iconW + ($IconSets.Count + 1) * $pad
$totalH = 2 * $rowH + $pad
$preview = New-Object System.Drawing.Bitmap $totalW, $totalH
$pg = [Drawing.Graphics]::FromImage($preview)
$pg.Clear([Drawing.Color]::FromArgb(255, 32, 34, 38))
for ($row = 0; $row -lt 2; $row++) {
    $dim = ($row -eq 1)
    for ($i = 0; $i -lt $IconSets.Count; $i++) {
        $icon = New-EaseeIconV2 48 $IconSets[$i].Color $IconSets[$i].Kind $dim
        $pg.DrawImage($icon, $pad + $i * ($iconW + $pad), $pad + $row * $rowH)
        $icon.Dispose()
    }
}
$pg.Dispose()
$preview.Save($PreviewPath, [Drawing.Imaging.ImageFormat]::Png)
$preview.Dispose()

Write-Output "Created $OutZip with $($IconSets.Count) icon sets"
Write-Output "Created $PreviewPath"
}
