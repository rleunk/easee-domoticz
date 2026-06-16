#!/usr/bin/env python3
"""Generate Easee_icons.zip with Domoticz-compatible custom icon sets."""

import io
import os
import struct
import zipfile
import zlib

PLUGIN_KEY = 'EaseeCloudAutoDiscoveryV1000'

ICON_SETS = [
    ('EaseeCharger', (46, 160, 67), 'plug'),
    ('EaseeEqualizer', (142, 68, 173), 'meter'),
    ('EaseePower', (255, 193, 7), 'bolt'),
    ('EaseeStatus', (33, 150, 243), 'info'),
    ('EaseeAlert', (229, 57, 53), 'alert'),
    ('EaseeLoadBal', (0, 188, 212), 'balance'),
    ('EaseeCost', (255, 152, 0), 'euro'),
    ('EaseeOverview', (0, 150, 136), 'chart'),
]


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


def _draw_symbol(kind, x, y, size, rgb, alpha=255):
    s = size / 48.0
    cx = cy = size / 2.0
    r, g, b = rgb
    if kind == 'plug':
        body = _inside_rect(x, y, int(14 * s), int(10 * s), int(34 * s), int(38 * s))
        prong_l = _inside_rect(x, y, int(16 * s), int(4 * s), int(20 * s), int(12 * s))
        prong_r = _inside_rect(x, y, int(28 * s), int(4 * s), int(32 * s), int(12 * s))
        cable = _inside_rect(x, y, int(22 * s), int(38 * s), int(26 * s), int(44 * s))
        return (r, g, b, alpha) if body or prong_l or prong_r or cable else (0, 0, 0, 0)
    if kind == 'bolt':
        p1 = _inside_rect(x, y, int(20 * s), int(6 * s), int(30 * s), int(22 * s))
        p2 = _inside_rect(x, y, int(16 * s), int(18 * s), int(28 * s), int(30 * s))
        p3 = _inside_rect(x, y, int(22 * s), int(28 * s), int(32 * s), int(42 * s))
        return (r, g, b, alpha) if p1 or p2 or p3 else (0, 0, 0, 0)
    if kind == 'info':
        dot = _inside_circle(x, y, cx, int(14 * s), int(3 * s))
        stem = _inside_rect(x, y, int(21 * s), int(20 * s), int(27 * s), int(40 * s))
        return (r, g, b, alpha) if dot or stem else (0, 0, 0, 0)
    if kind == 'euro':
        ring = _inside_circle(x, y, cx, cy, int(16 * s)) and not _inside_circle(x, y, cx, cy, int(12 * s))
        bar = _inside_rect(x, y, int(18 * s), int(20 * s), int(30 * s), int(24 * s))
        return (r, g, b, alpha) if ring or bar else (0, 0, 0, 0)
    if kind == 'meter':
        outer = _inside_circle(x, y, cx, cy, int(18 * s)) and not _inside_circle(x, y, cx, cy, int(14 * s))
        needle = _inside_rect(x, y, int(23 * s), int(22 * s), int(27 * s), int(34 * s))
        return (r, g, b, alpha) if outer or needle else (0, 0, 0, 0)
    if kind == 'balance':
        left = _inside_circle(x, y, int(16 * s), int(30 * s), int(8 * s))
        right = _inside_circle(x, y, int(32 * s), int(30 * s), int(8 * s))
        beam = _inside_rect(x, y, int(10 * s), int(18 * s), int(38 * s), int(22 * s))
        post = _inside_rect(x, y, int(22 * s), int(18 * s), int(26 * s), int(34 * s))
        return (r, g, b, alpha) if left or right or beam or post else (0, 0, 0, 0)
    if kind == 'alert':
        tri = y >= int(10 * s) and y <= int(40 * s) and abs(x - cx) <= (y - int(10 * s)) * 0.55
        mark = _inside_rect(x, y, int(22 * s), int(18 * s), int(26 * s), int(30 * s))
        dot = _inside_circle(x, y, cx, int(34 * s), int(2.5 * s))
        return (r, g, b, alpha) if (tri and not _inside_rect(x, y, int(18 * s), int(14 * s), int(30 * s), int(36 * s))) or mark or dot else (0, 0, 0, 0)
    if kind == 'chart':
        b1 = _inside_rect(x, y, int(12 * s), int(26 * s), int(18 * s), int(40 * s))
        b2 = _inside_rect(x, y, int(21 * s), int(18 * s), int(27 * s), int(40 * s))
        b3 = _inside_rect(x, y, int(30 * s), int(10 * s), int(36 * s), int(40 * s))
        return (r, g, b, alpha) if b1 or b2 or b3 else (0, 0, 0, 0)
    bg = _inside_circle(x, y, cx, cy, int(18 * s))
    return (r, g, b, alpha) if bg else (0, 0, 0, 0)


def _icon_png(size, rgb, kind, dim=False):
    def draw(x, y, sz):
        if dim:
            rgb_use = tuple(max(0, int(c * 0.45 + 80)) for c in rgb)
            alpha = 200
        else:
            rgb_use = rgb
            alpha = 255
        sym = _draw_symbol(kind, x, y, sz, rgb_use, alpha)
        if sym[3]:
            return sym
        if _inside_circle(x, y, sz / 2, sz / 2, int(sz * 0.46)):
            return (rgb_use[0], rgb_use[1], rgb_use[2], 40 if not dim else 25)
        return (0, 0, 0, 0)
    return _png_rgba(size, draw)


def _base_name(icon_name):
    return f'{PLUGIN_KEY}{icon_name}'


def build_zip(out_path):
    lines = []
    entries = {}
    for icon_name, rgb, kind in ICON_SETS:
        base = _base_name(icon_name)
        desc = icon_name.replace('Easee', 'Easee ')
        lines.append(f'{base};{icon_name};{desc}')
        entries[f'{base}.png'] = _icon_png(16, rgb, kind)
        entries[f'{base}48_On.png'] = _icon_png(48, rgb, kind, dim=False)
        entries[f'{base}48_Off.png'] = _icon_png(48, rgb, kind, dim=True)
    entries['icons.txt'] = ('\n'.join(lines) + '\n').encode('utf-8')
    with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('icons.txt', entries['icons.txt'])
        for name, data in entries.items():
            if name == 'icons.txt':
                continue
            zf.writestr(name, data)
    return len(ICON_SETS)


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, 'Easee_icons.zip')
    count = build_zip(out)
    print(f'Created {out} with {count} icon sets')
