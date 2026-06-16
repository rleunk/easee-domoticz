#!/usr/bin/env python3
"""Generate Easee_icons_v2.zip with Domoticz-compatible custom icon sets."""

import io
import os
import struct
import zipfile
import zlib

ICON_SETS = [
    ('EaseeCharger', (46, 160, 67), 'charger'),      # green — charger
    ('EaseeEqualizer', (142, 68, 173), 'equalizer'),
    ('EaseePower', (255, 193, 7), 'power'),          # #FFC107 amber — charging
    ('EaseeStatus', (33, 150, 243), 'status'),       # #2196F3 blue — status/info
    ('EaseeAlert', (229, 57, 53), 'alert'),          # #E53935 red — error
    ('EaseeLoadBal', (0, 188, 212), 'loadbal'),
    ('EaseeCost', (255, 152, 0), 'cost'),            # #FF9800 orange — cost
    ('EaseeOverview', (0, 150, 136), 'overview'),    # #009688 teal — overview
]

# Silhouette colors (Easee Charge Lite — two-tone faceted front)
WING_ON = (18, 18, 20)          # matte black outer wings
WING_OFF = (52, 54, 58)
PANEL_ON = (118, 120, 124)       # lighter grey center trapezoid
PANEL_OFF = (86, 88, 92)
PUCK_ON = (235, 237, 240)
PUCK_OFF = (160, 163, 168)
LED_DIM_GRAY = (102, 102, 102)  # #666 — charger off / dim blend target
LED_ON_ALPHA = 204              # ~80% — visible but not dominating
LED_OFF_ALPHA = 170             # ~67% dim strip
LED_OUTLINE = (38, 40, 44)


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


def _inside_ellipse(x, y, cx, cy, rx, ry):
    if rx <= 0 or ry <= 0:
        return False
    return ((x - cx) ** 2) / (rx ** 2) + ((y - cy) ** 2) / (ry ** 2) <= 1.0


def _scale(size, *vals):
    s = size / 48.0
    return tuple(int(v * s) for v in vals)


def _charger_geom(size, ox=0, oy=0, scale=1.0):
    """Shield taper + inset grey panel (48px design coords)."""
    s = size / 48.0 * scale
    ox_s, oy_s = ox * s, oy * s
    return {
        'cap_y0': int(5 * s + oy_s),
        'cap_y1': int(12 * s + oy_s),
        'outer_x0t': int(10 * s + ox_s),
        'outer_x1t': int(38 * s + ox_s),
        'outer_yt': int(12 * s + oy_s),
        'outer_x0m': int(16 * s + ox_s),
        'outer_x1m': int(32 * s + ox_s),
        'outer_ym': int(39 * s + oy_s),
        'tip_cx': 24 * s + ox_s,
        'tip_cy': 41.5 * s + oy_s,
        'tip_rx': 4.5 * s,
        'tip_ry': 2.8 * s,
        'tip_y0': int(37 * s + oy_s),
        'cap_r': max(1, int(3.5 * s)),
        'panel_x0t': int(15 * s + ox_s),
        'panel_x1t': int(33 * s + ox_s),
        'panel_yt': int(14 * s + oy_s),
        'panel_x0b': int(19 * s + ox_s),
        'panel_x1b': int(29 * s + ox_s),
        'panel_yb': int(36 * s + oy_s),
        'socket_cx': 24 * s + ox_s,
        'socket_cy': 41 * s + oy_s,
        'socket_r': max(1, 2 * s),
        'cx': int(24 * s + ox_s),
        's': s,
        'ox_s': ox_s,
        'oy_s': oy_s,
    }


def _charger_bottom_tip(x, y, g):
    if y < g['tip_y0']:
        return False
    return _inside_ellipse(x, y, g['tip_cx'], g['tip_cy'], g['tip_rx'], g['tip_ry'])


def _charger_shield(x, y, g):
    cap = _inside_rounded_rect(
        x, y, g['outer_x0t'], g['cap_y0'], g['outer_x1t'], g['cap_y1'], g['cap_r'],
    )
    body = _inside_trapezoid(
        x, y,
        g['outer_x0t'], g['outer_x1t'], g['outer_yt'],
        g['outer_x0m'], g['outer_x1m'], g['outer_ym'],
    )
    tip = _charger_bottom_tip(x, y, g)
    return cap or body or tip


def _charger_panel(x, y, g):
    return _inside_trapezoid(
        x, y,
        g['panel_x0t'], g['panel_x1t'], g['panel_yt'],
        g['panel_x0b'], g['panel_x1b'], g['panel_yb'],
    )


def _charger_socket(x, y, g):
    return _inside_circle(x, y, g['socket_cx'], g['socket_cy'], g['socket_r'])


def _charger_led_line(x, y, size, g):
    """Vertical LED strip (~2px × ~16px at 48px)."""
    cx = g['cx']
    s = g['s']
    oy_s = g['oy_s']
    led_w = max(1, int(round(1.25 * s))) if size <= 16 else max(1, int(round(1.75 * s)))
    led_x0 = cx - int(led_w // 2)
    led_x1 = cx + int((led_w - 1) // 2)
    if size <= 16:
        y0, y1 = int(14 * s + oy_s), int(22 * s + oy_s)
    else:
        y0, y1 = int(17 * s + oy_s), int(32 * s + oy_s)
    return y0 <= y <= y1 and led_x0 <= x <= led_x1


def _charger_led_outline(x, y, size, g):
    """Dark 1px flanking outline for LED strip (48px only)."""
    if size < 32:
        return False
    cx = g['cx']
    s = g['s']
    oy_s = g['oy_s']
    led_w = max(1, int(round(1.75 * s)))
    led_x0 = cx - int(led_w // 2)
    led_x1 = cx + int((led_w - 1) // 2)
    y0, y1 = int(17 * s + oy_s), int(32 * s + oy_s)
    if not (y0 <= y <= y1):
        return False
    return x in (led_x0 - 1, led_x1 + 1) and _charger_panel(x, y, g)


def _charger_led_dot(x, y, size, g):
    """Small status dot above LED strip."""
    cx = g['cx']
    s = g['s']
    oy_s = g['oy_s']
    cy = int(16.5 * s + oy_s)
    r = max(1, int(1.1 * s)) if size > 16 else max(1, int(0.9 * s))
    return _inside_circle(x, y, cx, cy, r)


def _charger_markings(x, y, size, g):
    """Optional tiny dashes below LED strip (48px only)."""
    if size <= 16:
        return False
    s = g['s']
    oy_s = g['oy_s']
    ox_s = g['ox_s']
    y0, y1 = int(30 * s + oy_s), int(31 * s + oy_s)
    if not (y0 <= y <= y1):
        return False
    left = int(21 * s + ox_s) <= x <= int(22 * s + ox_s)
    right = int(26 * s + ox_s) <= x <= int(27 * s + ox_s)
    return left or right


def _equalizer_geom(size, ox=0, oy=0, scale=1.0):
    s = size / 48.0 * scale
    ox_s, oy_s = ox * s, oy * s
    return {
        'outer_x0': int(10 * s + ox_s), 'outer_y0': int(10 * s + oy_s),
        'outer_x1': int(38 * s + ox_s), 'outer_y1': int(38 * s + oy_s),
        'outer_r': max(2, int(8 * s)),
        'inner_cx': 24 * s + ox_s, 'inner_cy': 23 * s + oy_s,
        'inner_r': max(3, 12 * s),
        'led_cx': 24 * s + ox_s, 'led_cy': 33.5 * s + oy_s,
        'led_r': max(1, 2.0 * s),
        's': s, 'ox_s': ox_s, 'oy_s': oy_s,
    }


def _equalizer_outer(x, y, g):
    return _inside_rounded_rect(
        x, y, g['outer_x0'], g['outer_y0'], g['outer_x1'], g['outer_y1'], g['outer_r'])


def _equalizer_inner_face(x, y, g):
    return _inside_circle(x, y, g['inner_cx'], g['inner_cy'], g['inner_r'])


def _equalizer_led(x, y, g):
    return _inside_circle(x, y, g['led_cx'], g['led_cy'], g['led_r'])


def _equalizer_logo_e(x, y, size, g):
    if size <= 16:
        return False
    s = g['s']
    ox_s, oy_s = g['ox_s'], g['oy_s']
    cx, cy = int(24 * s + ox_s), int(23 * s + oy_s)
    stem_w = max(1, int(1.25 * s))
    stem_x0 = cx - int(2.5 * s)
    stem_x1 = stem_x0 + stem_w - 1
    stem_y0, stem_y1 = cy - int(3.5 * s), cy + int(3 * s)
    if _inside_rect(x, y, stem_x0, stem_y0, stem_x1, stem_y1):
        return True
    bar_y0 = cy - int(0.5 * s)
    bar_y1 = cy + max(0, int(0.5 * s) - 1)
    bar_x0, bar_x1 = stem_x0, cx + int(2.5 * s)
    if _inside_rect(x, y, bar_x0, bar_y0, bar_x1, bar_y1):
        return True
    top_y0, top_y1 = cy - int(3.5 * s), cy - int(2.5 * s)
    top_x0, top_x1 = stem_x0, cx + int(1.5 * s)
    if _inside_rect(x, y, top_x0, top_y0, top_x1, top_y1):
        return True
    bot_y0, bot_y1 = cy + int(2 * s), cy + int(3 * s)
    if _inside_rect(x, y, top_x0, bot_y0, bar_x1, bot_y1):
        return True
    return False


def _equalizer_outer_color(x, y, g, dim):
    w = max(1.0, g['outer_x1'] - g['outer_x0'])
    h = max(1.0, g['outer_y1'] - g['outer_y0'])
    shade = ((x - g['outer_x0']) / w + (y - g['outer_y0']) / h) * 0.5
    light = (198, 202, 208) if dim else (248, 249, 252)
    dark = (168, 172, 178) if dim else (218, 222, 228)
    base = _blend_toward(light, dark, shade)
    alpha = 200 if dim else 255
    dx, dy = x - g['inner_cx'], y - g['inner_cy']
    dist = (dx ** 2 + dy ** 2) ** 0.5 - g['inner_r']
    if 0 <= dist <= 1.4 * g['s']:
        base = _blend_toward(base, (190, 194, 200), 0.35)
    return (base[0], base[1], base[2], alpha)


def _equalizer_inner_color(dim):
    alpha = 200 if dim else 255
    rgb = (228, 231, 236) if dim else (252, 253, 255)
    return (rgb[0], rgb[1], rgb[2], alpha)


def _draw_equalizer_icon(x, y, size, accent, dim, ox=0, oy=0, scale=1.0):
    g = _equalizer_geom(size, ox=ox, oy=oy, scale=scale)
    if not _equalizer_outer(x, y, g):
        return None
    if _equalizer_led(x, y, g):
        c = _status_dot_color(accent, dim)
        alpha = 200 if dim else 255
        return (c[0], c[1], c[2], alpha)
    if _equalizer_logo_e(x, y, size, g):
        logo = (150, 154, 160) if dim else (175, 178, 184)
        alpha = 200 if dim else 255
        return (logo[0], logo[1], logo[2], alpha)
    if _equalizer_inner_face(x, y, g):
        return _equalizer_inner_color(dim)
    return _equalizer_outer_color(x, y, g, dim)


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


def _led_strip_color(accent, dim, kind=''):
    """Status color on charger LED strip; gray or dim accent when off."""
    if dim:
        if kind == 'charger':
            return LED_DIM_GRAY
        return _blend_toward(accent, LED_DIM_GRAY, 0.35)
    return _blend_toward(accent, PANEL_ON, 0.12)


def _status_dot_color(accent, dim):
    """Bottom status dot on equalizer puck icons."""
    if dim:
        return _blend_toward(accent, LED_DIM_GRAY, 0.55)
    return accent


def _draw_charger_icon(x, y, size, accent, dim, kind='', ox=0, oy=0, scale=1.0):
    g = _charger_geom(size, ox=ox, oy=oy, scale=scale)
    wing = WING_OFF if dim else WING_ON
    panel = PANEL_OFF if dim else PANEL_ON
    body_alpha = 200 if dim else 255
    led = _led_strip_color(accent, dim, kind)
    led_alpha = LED_OFF_ALPHA if dim else LED_ON_ALPHA

    if not _charger_shield(x, y, g):
        return None

    if _charger_panel(x, y, g):
        if _charger_led_line(x, y, size, g):
            if _charger_led_outline(x, y, size, g):
                return (LED_OUTLINE[0], LED_OUTLINE[1], LED_OUTLINE[2], body_alpha)
            return (led[0], led[1], led[2], led_alpha)
        if _charger_led_dot(x, y, size, g):
            dot = _blend_toward(panel, wing, 0.45)
            return (dot[0], dot[1], dot[2], body_alpha)
        if _charger_markings(x, y, size, g):
            mark = _blend_toward(panel, wing, 0.35)
            return (mark[0], mark[1], mark[2], body_alpha)
        return (panel[0], panel[1], panel[2], body_alpha)

    if _charger_socket(x, y, g):
        sock = _blend_toward(wing, (0, 0, 0), 0.45)
        return (sock[0], sock[1], sock[2], body_alpha)

    return (wing[0], wing[1], wing[2], body_alpha)


def _draw_symbol_v2(kind, x, y, size, accent, dim):
    bright = accent
    accent = _accent_rgb(accent, dim)
    puck = PUCK_OFF if dim else PUCK_ON
    alpha = 200 if dim else 255

    if kind == 'charger':
        px = _draw_charger_icon(x, y, size, bright, dim, kind='charger')
        return px if px else (0, 0, 0, 0)

    if kind == 'power':
        px = _draw_charger_icon(x, y, size, bright, dim, kind='power')
        return px if px else (0, 0, 0, 0)

    if kind == 'status':
        px = _draw_charger_icon(x, y, size, bright, dim, kind='status')
        if px:
            return px
        cx, cy = size * 0.78, size * 0.22
        r = max(1.5, size * 0.08)
        ring_r = r + max(1, size * 0.04)
        info = _accent_rgb((46, 160, 67), dim)
        if _inside_circle(x, y, cx, cy, ring_r) and not _inside_circle(x, y, cx, cy, r - 0.5):
            return (info[0], info[1], info[2], alpha)
        if _inside_circle(x, y, cx, cy, r):
            return (info[0], info[1], info[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'cost':
        if _draw_euro_badge(x, y, size):
            return (accent[0], accent[1], accent[2], alpha)
        px = _draw_charger_icon(x, y, size, bright, dim, kind='cost')
        return px if px else (0, 0, 0, 0)

    if kind == 'alert':
        px = _draw_charger_icon(x, y, size, bright, dim, kind='alert')
        if px:
            return px
        cx, cy = size * 0.78, size * 0.18
        if _inside_circle(x, y, cx, cy, max(1.5, size * 0.07)):
            c = _led_strip_color((229, 57, 53), dim, 'alert')
            return (c[0], c[1], c[2], alpha)
        return (0, 0, 0, 0)

    if kind == 'equalizer':
        px = _draw_equalizer_icon(x, y, size, bright, dim)
        return px if px else (0, 0, 0, 0)

    if kind == 'overview':
        for ox in (-7, 7):
            px = _draw_charger_icon(x, y, size, bright, dim, kind='overview', ox=ox, scale=0.72)
            if px:
                return px
        return (0, 0, 0, 0)

    if kind == 'loadbal':
        px = _draw_equalizer_icon(x, y, size, bright, dim, scale=0.82)
        if px:
            return px
        if _draw_arrow_lr(x, y, size):
            return (accent[0], accent[1], accent[2], alpha)
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
    """Save on/off rows of 48px icons showing LED strip color coding."""
    icon_w = 48
    pad = 8
    row_h = icon_w + pad
    total_w = len(ICON_SETS) * icon_w + (len(ICON_SETS) + 1) * pad
    total_h = 2 * row_h + pad

    def draw(x, y):
        bg = (32, 34, 38, 255)
        if y < pad:
            return bg
        row = (y - pad) // row_h
        if row > 1:
            return bg
        local_y = (y - pad) - row * row_h
        if local_y >= icon_w:
            return bg
        idx = (x - pad) // (icon_w + pad)
        if idx < 0 or idx >= len(ICON_SETS):
            return bg
        local_x = x - pad - idx * (icon_w + pad)
        if local_x >= icon_w:
            return bg
        _, rgb, kind = ICON_SETS[idx]
        return _draw_symbol_v2(kind, local_x, local_y, icon_w, rgb, dim=(row == 1))

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
