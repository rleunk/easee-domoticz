#!/usr/bin/env python3
"""Generate Easee_icons_v2.zip with Domoticz-compatible custom icon sets."""

import io
import os
import struct
import zipfile
import zlib

ICON_SETS = [
    ('EaseeCharger', (46, 160, 67), 'charger'),
    ('EaseeEqualizer', (142, 68, 173), 'equalizer'),
    ('EaseePower', (255, 193, 7), 'power'),
    ('EaseeStatus', (33, 150, 243), 'status'),
    ('EaseeAlert', (229, 57, 53), 'alert'),
    ('EaseeLoadBal', (0, 188, 212), 'loadbal'),
    ('EaseeCost', (255, 152, 0), 'cost'),
    ('EaseeOverview', (0, 150, 136), 'overview'),
]

# Silhouette colors (Easee hardware look)
BODY_ON = (42, 44, 48)
BODY_OFF = (72, 74, 78)
PUCK_ON = (235, 237, 240)
PUCK_OFF = (160, 163, 168)
STRIP_ON = (58, 62, 66)
STRIP_OFF = (95, 98, 102)


def _chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xffffffff
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)


def _png_rgba(size, draw_fn):
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            row.extend(draw_fn(x, y, size))
        rows.append(bytes(row))
    raw = b''.join(rows)
    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    return b''.join([
        b'\x89PNG\r\n\x1a\n',
        _chunk(b'IHDR', ihdr),
        _chunk(b'IDAT', zlib.compress(raw, 9)),
        _chunk(b'IEND', b''),
    ])


def _inside_circle(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2


def _inside_rect(x, y, x0, y0, x1, y1):
    return x0 <= x <= x1 and y0 <= y <= y1


def _inside_rounded_rect(x, y, x0, y0, x1, y1, r):
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    if x <= x0 + r and y <= y0 + r:
        return _inside_circle(x, y, x0 + r, y0 + r, r)
    if x >= x1 - r and y <= y0 + r:
        return _inside_circle(x, y, x1 - r, y0 + r, r)
    if x <= x0 + r and y >= y1 - r:
        return _inside_circle(x, y, x0 + r, y1 - r, r)
    if x >= x1 - r and y >= y1 - r:
        return _inside_circle(x, y, x1 - r, y1 - r, r)
    return True


def _inside_trapezoid(x, y, x0t, x1t, yt, x0b, x1b, yb):
    if y < yt or y > yb:
        return False
    if yb == yt:
        return x0t <= x <= x1t
    t = (y - yt) / (yb - yt)
    return (x0t + t * (x0b - x0t)) <= x <= (x1t + t * (x1b - x1t))


def _scale(size, *vals):
    s = size / 48.0
    return tuple(int(v * s) for v in vals)


def _charger_body(x, y, size, ox=0, oy=0, scale=1.0):
    s = size / 48.0 * scale
    ox_s, oy_s = ox * s, oy * s
    top_y0, top_y1 = int(6 * s + oy_s), int(13 * s + oy_s)
    x0t, x1t = int(13 * s + ox_s), int(35 * s + ox_s)
    body_yb = int(41 * s + oy_s)
    x0b, x1b = int(19 * s + ox_s), int(29 * s + ox_s)
    cap = _inside_rect(x, y, x0t, top_y0, x1t, top_y1)
    body = _inside_trapezoid(x, y, x0t, x1t, top_y1, x0b, x1b, body_yb)
    return cap or body


def _charger_strip(x, y, size, ox=0, oy=0, scale=1.0):
    s = size / 48.0 * scale
    ox_s, oy_s = ox * s, oy * s
    return _inside_rect(
        x, y,
        int(22 * s + ox_s), int(7 * s + oy_s),
        int(26 * s + ox_s), int(40 * s + oy_s),
    )


def _equalizer_puck(x, y, size, ox=0, oy=0, scale=1.0):
    s = size / 48.0 * scale
    ox_s, oy_s = ox * s, oy * s
    r = max(2, int(8 * s))
    return _inside_rounded_rect(
        x, y,
        int(10 * s + ox_s), int(10 * s + oy_s),
        int(38 * s + ox_s), int(38 * s + oy_s),
        r,
    )


def _equalizer_led(x, y, size, ox=0, oy=0, scale=1.0):
    s = size / 48.0 * scale
    cx = int(24 * s + ox * s)
    cy = int(40 * s + oy * s)
    r = max(1, int(2.5 * s))
    return _inside_circle(x, y, cx, cy, r)


def _draw_arrow_lr(x, y, size, ox=0, oy=0):
    s = size / 48.0
    ox_s, oy_s = ox * s, oy * s
    cy = int(24 * s + oy_s)
    left = (
        _inside_rect(x, y, int(4 * s + ox_s), cy - int(2 * s), int(12 * s + ox_s), cy + int(2 * s))
        or _inside_trapezoid(x, y, int(12 * s + ox_s), int(16 * s + ox_s), cy - int(4 * s),
                             int(8 * s + ox_s), int(12 * s + ox_s), cy + int(4 * s))
    )
    right = (
        _inside_rect(x, y, int(36 * s + ox_s), cy - int(2 * s), int(44 * s + ox_s), cy + int(2 * s))
        or _inside_trapezoid(x, y, int(32 * s + ox_s), int(36 * s + ox_s), cy - int(4 * s),
                             int(36 * s + ox_s), int(40 * s + ox_s), cy + int(4 * s))
    )
    return left or right


def _draw_euro_badge(x, y, size):
    s = size / 48.0
    cx, cy = int(36 * s), int(36 * s)
    r = int(7 * s)
    ring = _inside_circle(x, y, cx, cy, r) and not _inside_circle(x, y, cx, cy, max(1, r - int(2 * s)))
    bar = _inside_rect(x, y, int(33 * s), int(34 * s), int(39 * s), int(38 * s))
    return ring or bar


def _blend_toward(rgb, target, amount):
    return tuple(int(c + (t - c) * amount) for c, t in zip(rgb, target))


def _accent_rgb(rgb, dim):
    if dim:
        return tuple(max(0, int(c * 0.45 + 55)) for c in rgb)
    return rgb


def _pixel(rgba):
    return rgba if rgba[3] else (0, 0, 0, 0)


def _draw_symbol_v2(kind, x, y, size, accent, dim):
    accent = _accent_rgb(accent, dim)
    body = BODY_OFF if dim else BODY_ON
    puck = PUCK_OFF if dim else PUCK_ON
    strip = STRIP_OFF if dim else STRIP_ON
    alpha = 200 if dim else 255

    if kind == 'charger':
        if _charger_body(x, y, size):
            if _charger_strip(x, y, size):
                return (strip[0], strip[1], strip[2], alpha)
            return (body[0], body[1], body[2], alpha)
        if _equalizer_led(x, y, size) and not dim:
            return (accent[0], accent[1], accent[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'equalizer':
        if _equalizer_puck(x, y, size):
            return (puck[0], puck[1], puck[2], alpha)
        if _equalizer_led(x, y, size):
            c = _blend_toward(accent, (180, 180, 185), 0.35) if dim else accent
            return (c[0], c[1], c[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'power':
        if _charger_body(x, y, size):
            if _charger_strip(x, y, size):
                glow = _blend_toward(accent, (46, 160, 67), 0.35) if not dim else strip
                return (glow[0], glow[1], glow[2], alpha)
            return (body[0], body[1], body[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'status':
        if _charger_body(x, y, size):
            if _charger_strip(x, y, size):
                return (strip[0], strip[1], strip[2], alpha)
            return (body[0], body[1], body[2], alpha)
        cx, cy = size * 0.78, size * 0.22
        r = max(1.5, size * 0.08)
        ring_r = r + max(1, size * 0.04)
        if _inside_circle(x, y, cx, cy, ring_r) and not _inside_circle(x, y, cx, cy, r - 0.5):
            c = _accent_rgb((46, 160, 67), dim)
            return (c[0], c[1], c[2], alpha)
        if _inside_circle(x, y, cx, cy, r):
            c = _accent_rgb((46, 160, 67), dim)
            return (c[0], c[1], c[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'cost':
        if _draw_euro_badge(x, y, size):
            return (accent[0], accent[1], accent[2], alpha)
        if _charger_body(x, y, size):
            if _charger_strip(x, y, size):
                return (strip[0], strip[1], strip[2], alpha)
            return (body[0], body[1], body[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'overview':
        for ox in (-7, 7):
            if _charger_body(x, y, size, ox=ox, scale=0.72):
                if _charger_strip(x, y, size, ox=ox, scale=0.72):
                    return (strip[0], strip[1], strip[2], alpha)
                return (body[0], body[1], body[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'loadbal':
        if _equalizer_puck(x, y, size, scale=0.82):
            return (puck[0], puck[1], puck[2], alpha)
        if _draw_arrow_lr(x, y, size):
            return (accent[0], accent[1], accent[2], alpha)
        if _equalizer_led(x, y, size, scale=0.82):
            c = _blend_toward(accent, (180, 180, 185), 0.35) if dim else accent
            return (c[0], c[1], c[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'alert':
        if _charger_body(x, y, size):
            if _charger_strip(x, y, size):
                c = _accent_rgb((229, 57, 53), dim)
                return (c[0], c[1], c[2], alpha)
            return (body[0], body[1], body[2], alpha)
        cx, cy = size * 0.78, size * 0.18
        if _inside_circle(x, y, cx, cy, max(1.5, size * 0.07)):
            c = _accent_rgb((229, 57, 53), dim)
            return (c[0], c[1], c[2], alpha)
        return (0, 0, 0, 0)

    return (0, 0, 0, 0)


def _icon_png(size, rgb, kind, dim=False):
    def draw(x, y, sz):
        return _draw_symbol_v2(kind, x, y, sz, rgb, dim)
    return _png_rgba(size, draw)


def build_zip(out_path):
    lines = []
    entries = {}
    for icon_name, rgb, kind in ICON_SETS:
        desc = icon_name.replace('Easee', 'Easee ', 1)
        lines.append(f'{icon_name};{icon_name};{desc}')
        entries[f'{icon_name}.png'] = _icon_png(16, rgb, kind)
        entries[f'{icon_name}48_On.png'] = _icon_png(48, rgb, kind, dim=False)
        entries[f'{icon_name}48_Off.png'] = _icon_png(48, rgb, kind, dim=True)
    entries['icons.txt'] = ('\n'.join(lines) + '\n').encode('utf-8')
    with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('icons.txt', entries['icons.txt'])
        for name, data in entries.items():
            if name == 'icons.txt':
                continue
            zf.writestr(name, data)
    return len(ICON_SETS)


def build_preview(out_path):
    """Save a row of 48px on-state icons for review."""
    icon_w = 48
    pad = 8
    total_w = len(ICON_SETS) * icon_w + (len(ICON_SETS) + 1) * pad
    total_h = icon_w + 2 * pad

    def draw(x, y):
        if y < pad or y >= pad + icon_w:
            return (32, 34, 38, 255)
        idx = (x - pad) // (icon_w + pad)
        if idx < 0 or idx >= len(ICON_SETS):
            return (32, 34, 38, 255)
        local_x = x - pad - idx * (icon_w + pad)
        if local_x >= icon_w:
            return (32, 34, 38, 255)
        _, rgb, kind = ICON_SETS[idx]
        return _draw_symbol_v2(kind, local_x, y - pad, icon_w, rgb, dim=False)

    rows = []
    for y in range(total_h):
        row = bytearray([0])
        for x in range(total_w):
            row.extend(draw(x, y))
        rows.append(bytes(row))
    raw = b''.join(rows)
    ihdr = struct.pack('>IIBBBBB', total_w, total_h, 8, 6, 0, 0, 0)
    png = b''.join([
        b'\x89PNG\r\n\x1a\n',
        _chunk(b'IHDR', ihdr),
        _chunk(b'IDAT', zlib.compress(raw, 9)),
        _chunk(b'IEND', b''),
    ])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(png)


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, 'Easee_icons_v2.zip')
    preview = os.path.join(root, 'docs', 'icon-preview-v2.png')
    count = build_zip(out)
    build_preview(preview)
    print(f'Created {out} with {count} icon sets')
    print(f'Created {preview}')
