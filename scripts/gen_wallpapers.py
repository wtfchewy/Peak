#!/usr/bin/env python3
"""Generate the Peak 'sither' (dithered) gradient wallpapers for iPhone 17 Pro.

Recreates the brand logo aesthetic: an ordered (Bayer) dither between two
colors that fades vertically, rendered in chunky pixel cells.
"""
import struct, zlib

W, H = 1206, 2622          # iPhone 17 Pro native resolution (portrait)
CELL = 18                  # pixel-cell size (chunky brand dither)

# 8x8 Bayer ordered-dither threshold matrix, normalized to (0,1)
BAYER8 = [
    [ 0,48,12,60, 3,51,15,63],
    [32,16,44,28,35,19,47,31],
    [ 8,56, 4,52,11,59, 7,55],
    [40,24,36,20,43,27,39,23],
    [ 2,50,14,62, 1,49,13,61],
    [34,18,46,30,33,17,45,29],
    [10,58, 6,54, 9,57, 5,53],
    [42,26,38,22,41,25,37,21],
]
BAYER_N = 64

def hx(c):
    return (int(c[0:2],16), int(c[2:4],16), int(c[4:6],16))

def smooth(t):
    # ease so the dither band sits pleasantly, not linearly
    return t*t*(3-2*t)

def build(top_hex, bot_hex, path, gamma=1.0):
    top, bot = hx(top_hex), hx(bot_hex)
    cols = (W + CELL - 1)//CELL
    rows = (H + CELL - 1)//CELL
    # decide color per cell via ordered dithering of a vertical gradient
    cell_rgb = [[None]*cols for _ in range(rows)]
    for cy in range(rows):
        t = smooth((cy + 0.5)/rows) ** gamma   # 0 = top color, 1 = bottom color
        brow = BAYER8[cy % 8]
        for cx in range(cols):
            thr = (brow[cx % 8] + 0.5)/BAYER_N
            cell_rgb[cy][cx] = bot if t > thr else top

    # precompute one scanline of bytes per cell-row
    row_cache = []
    for cy in range(rows):
        line = bytearray()
        for cx in range(cols):
            r,g,b = cell_rgb[cy][cx]
            line += bytes((r,g,b)) * CELL
        del line[W*3:]                 # trim partial last cell
        row_cache.append(bytes(line))

    raw = bytearray()
    for y in range(H):
        raw.append(0)                  # PNG filter type: none
        raw += row_cache[y//CELL]

    comp = zlib.compress(bytes(raw), 9)
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ+data) & 0xffffffff))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path}  {W}x{H}  cells {cols}x{rows}  {len(png)//1024} KB")

# Blue: brand deep blue -> brand light blue (the original logo gradient)
build("1E96EB", "93E2FD", "wallpapers/peak-wallpaper-blue.png")
# White: brand light blue -> pure white (white-dominant companion)
build("93E2FD", "FFFFFF", "wallpapers/peak-wallpaper-white.png")
