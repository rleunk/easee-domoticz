# Generate Easee_icons.zip (Domoticz custom icon format)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$OutZip = Join-Path (Split-Path $PSScriptRoot -Parent) 'Easee_icons.zip'
$TempDir = Join-Path $env:TEMP "easee-icons-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $TempDir | Out-Null

$IconSets = @(
    @{ Name = 'EaseeCharger';   Color = [Drawing.Color]::FromArgb(255, 46, 160, 67);  Kind = 'plug' }
    @{ Name = 'EaseeEqualizer'; Color = [Drawing.Color]::FromArgb(255, 142, 68, 173); Kind = 'meter' }
    @{ Name = 'EaseePower';     Color = [Drawing.Color]::FromArgb(255, 255, 193, 7);  Kind = 'bolt' }
    @{ Name = 'EaseeStatus';    Color = [Drawing.Color]::FromArgb(255, 33, 150, 243); Kind = 'info' }
    @{ Name = 'EaseeAlert';     Color = [Drawing.Color]::FromArgb(255, 229, 57, 53);  Kind = 'alert' }
    @{ Name = 'EaseeLoadBal';   Color = [Drawing.Color]::FromArgb(255, 0, 188, 212);  Kind = 'balance' }
    @{ Name = 'EaseeCost';      Color = [Drawing.Color]::FromArgb(255, 255, 152, 0);  Kind = 'euro' }
    @{ Name = 'EaseeOverview';  Color = [Drawing.Color]::FromArgb(255, 0, 150, 136);  Kind = 'chart' }
)

function Test-Circle([int]$x, [int]$y, [double]$cx, [double]$cy, [double]$r) {
    (($x - $cx) * ($x - $cx) + ($y - $cy) * ($y - $cy)) -le ($r * $r)
}
function Test-Rect([int]$x, [int]$y, [double]$x0, [double]$y0, [double]$x1, [double]$y1) {
    ($x -ge $x0) -and ($x -le $x1) -and ($y -ge $y0) -and ($y -le $y1)
}

function Get-SymbolPixel([string]$Kind, [int]$x, [int]$y, [int]$Size) {
    $s = $Size / 48.0
    $cx = $Size / 2.0
    $cy = $Size / 2.0
    switch ($Kind) {
        'plug' {
            if ((Test-Rect $x $y (14*$s) (10*$s) (34*$s) (38*$s)) -or
                (Test-Rect $x $y (16*$s) (4*$s) (20*$s) (12*$s)) -or
                (Test-Rect $x $y (28*$s) (4*$s) (32*$s) (12*$s)) -or
                (Test-Rect $x $y (22*$s) (38*$s) (26*$s) (44*$s))) { return $true }
        }
        'bolt' {
            if ((Test-Rect $x $y (20*$s) (6*$s) (30*$s) (22*$s)) -or
                (Test-Rect $x $y (16*$s) (18*$s) (28*$s) (30*$s)) -or
                (Test-Rect $x $y (22*$s) (28*$s) (32*$s) (42*$s))) { return $true }
        }
        'info' {
            if ((Test-Circle $x $y $cx (14*$s) (3*$s)) -or
                (Test-Rect $x $y (21*$s) (20*$s) (27*$s) (40*$s))) { return $true }
        }
        'euro' {
            if (((Test-Circle $x $y $cx $cy (16*$s)) -and -not (Test-Circle $x $y $cx $cy (12*$s))) -or
                (Test-Rect $x $y (18*$s) (20*$s) (30*$s) (24*$s))) { return $true }
        }
        'meter' {
            if (((Test-Circle $x $y $cx $cy (18*$s)) -and -not (Test-Circle $x $y $cx $cy (14*$s))) -or
                (Test-Rect $x $y (23*$s) (22*$s) (27*$s) (34*$s))) { return $true }
        }
        'balance' {
            if ((Test-Circle $x $y (16*$s) (30*$s) (8*$s)) -or
                (Test-Circle $x $y (32*$s) (30*$s) (8*$s)) -or
                (Test-Rect $x $y (10*$s) (18*$s) (38*$s) (22*$s)) -or
                (Test-Rect $x $y (22*$s) (18*$s) (26*$s) (34*$s))) { return $true }
        }
        'alert' {
            $tri = ($y -ge (10*$s)) -and ($y -le (40*$s)) -and ([math]::Abs($x - $cx) -le (($y - (10*$s)) * 0.55))
            $inner = (Test-Rect $x $y (18*$s) (14*$s) (30*$s) (36*$s))
            if (($tri -and -not $inner) -or (Test-Rect $x $y (22*$s) (18*$s) (26*$s) (30*$s)) -or
                (Test-Circle $x $y $cx (34*$s) (2.5*$s))) { return $true }
        }
        'chart' {
            if ((Test-Rect $x $y (12*$s) (26*$s) (18*$s) (40*$s)) -or
                (Test-Rect $x $y (21*$s) (18*$s) (27*$s) (40*$s)) -or
                (Test-Rect $x $y (30*$s) (10*$s) (36*$s) (40*$s))) { return $true }
        }
    }
    return $false
}

function New-EaseeIcon([int]$Size, [Drawing.Color]$Color, [string]$Kind, [bool]$Dim) {
    $bmp = New-Object System.Drawing.Bitmap $Size, $Size
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([Drawing.Color]::Transparent)
    $use = if ($Dim) {
        [Drawing.Color]::FromArgb(200, [math]::Min(255, [int]($Color.R * 0.45 + 80)), [math]::Min(255, [int]($Color.G * 0.45 + 80)), [math]::Min(255, [int]($Color.B * 0.45 + 80)))
    } else { $Color }
    $bg = [Drawing.Color]::FromArgb(40, $use.R, $use.G, $use.B)
    if ($Dim) { $bg = [Drawing.Color]::FromArgb(25, $use.R, $use.G, $use.B) }
    $brush = New-Object Drawing.SolidBrush $use
    $bgBrush = New-Object Drawing.SolidBrush $bg
    for ($y = 0; $y -lt $Size; $y++) {
        for ($x = 0; $x -lt $Size; $x++) {
            if (Get-SymbolPixel $Kind $x $y $Size) {
                $bmp.SetPixel($x, $y, $use)
            } elseif (Test-Circle $x $y ($Size/2.0) ($Size/2.0) ($Size*0.46)) {
                $bmp.SetPixel($x, $y, $bg)
            }
        }
    }
    $brush.Dispose(); $bgBrush.Dispose(); $g.Dispose()
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
    Save-Png (New-EaseeIcon 16 $set.Color $set.Kind $false) (Join-Path $TempDir "$name.png")
    Save-Png (New-EaseeIcon 48 $set.Color $set.Kind $false) (Join-Path $TempDir "${name}48_On.png")
    Save-Png (New-EaseeIcon 48 $set.Color $set.Kind $true) (Join-Path $TempDir "${name}48_Off.png")
}
$iconsPath = Join-Path $TempDir 'icons.txt'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($iconsPath, ($Lines -join "`n") + "`n", $utf8NoBom)

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $OutZip)
Remove-Item $TempDir -Recurse -Force
Write-Output "Created $OutZip with $($IconSets.Count) icon sets"
