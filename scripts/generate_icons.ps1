# Generate Easee_icons_v2.zip (Domoticz custom icon format — Easee hardware silhouettes)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$OutZip = Join-Path (Split-Path $PSScriptRoot -Parent) 'Easee_icons_v2.zip'
$PreviewPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'docs\icon-preview-v2.png'
$TempDir = Join-Path $env:TEMP "easee-icons-v2-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
$docsDir = Split-Path $PreviewPath -Parent
if (-not (Test-Path $docsDir)) { New-Item -ItemType Directory -Path $docsDir -Force | Out-Null }

$IconSets = @(
    @{ Name = 'EaseeCharger';   Color = [Drawing.Color]::FromArgb(255, 46, 160, 67);  Kind = 'charger' }
    @{ Name = 'EaseeEqualizer'; Color = [Drawing.Color]::FromArgb(255, 142, 68, 173); Kind = 'equalizer' }
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
        OuterX0b = [int](21 * $s + $oxs); OuterX1b = [int](27 * $s + $oxs)
        OuterYb = [int](42 * $s + $oys)
        CapR = [math]::Max(1, [int](3.5 * $s))
        PanelX0t = [int](15 * $s + $oxs); PanelX1t = [int](33 * $s + $oxs)
        PanelYt = [int](14 * $s + $oys)
        PanelX0b = [int](20 * $s + $oxs); PanelX1b = [int](28 * $s + $oxs)
        PanelYb = [int](38 * $s + $oys)
        SocketCy = [int](41.5 * $s + $oys)
        SocketR = [math]::Max(1, [int](1.6 * $s))
        Cx = [int](24 * $s + $oxs)
        S = $s; Oxs = $oxs; Oys = $oys
    }
}

function Test-ChargerShield([int]$x, [int]$y, [hashtable]$G) {
    $cap = Test-RoundedRect $x $y $G.OuterX0t $G.CapY0 $G.OuterX1t $G.CapY1 $G.CapR
    $body = Test-Trapezoid $x $y $G.OuterX0t $G.OuterX1t $G.OuterYt $G.OuterX0b $G.OuterX1b $G.OuterYb
    $cap -or $body
}

function Test-ChargerPanel([int]$x, [int]$y, [hashtable]$G) {
    Test-Trapezoid $x $y $G.PanelX0t $G.PanelX1t $G.PanelYt $G.PanelX0b $G.PanelX1b $G.PanelYb
}

function Test-ChargerSocket([int]$x, [int]$y, [hashtable]$G) {
    Test-Circle $x $y $G.Cx $G.SocketCy $G.SocketR
}

function Test-ChargerLedLine([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    $cx = $G.Cx; $s = $G.S; $oys = $G.Oys
    if ($Size -le 16) {
        $y0 = [int](14 * $s + $oys); $y1 = [int](22 * $s + $oys)
        return ($y -ge $y0) -and ($y -le $y1) -and ([math]::Abs($x - $cx) -le [math]::Max(0, [int](0.5 * $s)))
    }
    $half = if ($Size -ge 48) { 0 } else { [math]::Max(0, [int][math]::Round(0.5 * $s)) }
    $y0 = [int](18 * $s + $oys); $y1 = [int](30 * $s + $oys)
    return ($y -ge $y0) -and ($y -le $y1) -and ([math]::Abs($x - $cx) -le $half)
}

function Test-ChargerLedOutline([int]$x, [int]$y, [int]$Size, [hashtable]$G) {
    if ($Size -lt 32) { return $false }
    $cx = $G.Cx; $s = $G.S; $oys = $G.Oys
    $y0 = [int](18 * $s + $oys); $y1 = [int](30 * $s + $oys)
    if (-not (($y -ge $y0) -and ($y -le $y1))) { return $false }
    if ([math]::Abs($x - $cx) -ne 1) { return $false }
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

function Test-EqualizerPuck([int]$x, [int]$y, [int]$Size, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0) {
    $s = ($Size / 48.0) * $Scale
    $oxs = $Ox * $s; $oys = $Oy * $s
    $r = [math]::Max(2, [int](8 * $s))
    Test-RoundedRect $x $y ([int](10 * $s + $oxs)) ([int](10 * $s + $oys)) ([int](38 * $s + $oxs)) ([int](38 * $s + $oys)) $r
}

function Test-EqualizerLed([int]$x, [int]$y, [int]$Size, [double]$Ox = 0, [double]$Oy = 0, [double]$Scale = 1.0) {
    $s = ($Size / 48.0) * $Scale
    $cx = [int](24 * $s + $Ox * $s); $cy = [int](40 * $s + $Oy * $s)
    $r = [math]::Max(1, [int](2.5 * $s))
    Test-Circle $x $y $cx $cy $r
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
    $ledAlpha = if ($Dim) { 140 } else { 178 }
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
        return Get-BlendColor $wing ([Drawing.Color]::FromArgb(255, 0, 0, 0)) 0.25
    }

    return $wing
}

function Get-SymbolPixelV2([string]$Kind, [int]$x, [int]$y, [int]$Size, [Drawing.Color]$Bright, [bool]$Dim) {
    $puck = if ($Dim) { [Drawing.Color]::FromArgb(200, 160, 163, 168) } else { [Drawing.Color]::FromArgb(255, 235, 237, 240) }
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
            if (Test-EqualizerPuck $x $y $Size) { return $puck }
            if (Test-EqualizerLed $x $y $Size) { return (Get-StatusDotColor $Bright $Dim) }
        }
        'overview' {
            foreach ($ox in @(-7, 7)) {
                $px = Get-ChargerPixel $x $y $Size $Bright $Dim 'overview' -Ox $ox -Scale 0.72
                if ($null -ne $px) { return $px }
            }
        }
        'loadbal' {
            if (Test-EqualizerPuck $x $y $Size -Scale 0.82) { return $puck }
            if (Test-ArrowLR $x $y $Size) { return $accent }
            if (Test-EqualizerLed $x $y $Size -Scale 0.82) { return (Get-StatusDotColor $Bright $Dim) }
        }
    }
    return $null
}

function New-EaseeIconV2([int]$Size, [Drawing.Color]$Color, [string]$Kind, [bool]$Dim) {
    $bmp = New-Object System.Drawing.Bitmap $Size, $Size
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([Drawing.Color]::Transparent)
    for ($y = 0; $y -lt $Size; $y++) {
        for ($x = 0; $x -lt $Size; $x++) {
            $px = Get-SymbolPixelV2 $Kind $x $y $Size $Color $Dim
            if ($null -ne $px) { $bmp.SetPixel($x, $y, $px) }
        }
    }
    $g.Dispose()
    return $bmp
}

function Save-Png([Drawing.Bitmap]$Bmp, [string]$Path) {
    $Bmp.Save($Path, [Drawing.Imaging.ImageFormat]::Png)
    $Bmp.Dispose()
}

$Lines = New-Object System.Collections.Generic.List[string]
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
