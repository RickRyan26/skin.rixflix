#!/usr/bin/env python3
"""Render the small white nine-slice focus bloom from rounded-rectangle geometry.

128px source, 26px slice corners; displayed 6px outside the card. The sharp
outline is 3px outside the card, leaving 3px of soft exterior bloom. The interior
falls away over 12px so artwork is not covered by a translucent white fill.
"""
import math
import struct
import zlib
from pathlib import Path

size = 128
rows = []
for y in range(size):
    row = bytearray([0])
    for x in range(size):
        qx = abs(x + .5 - 64) - 41
        qy = abs(y + .5 - 64) - 41
        distance = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - 20
        if distance >= 0:
            alpha = 180 * math.exp(-.5 * (distance / 1.8) ** 2) * max(0, 1-distance/3) ** 2
        else:
            alpha = 120 * math.exp(-.5 * (distance / 4) ** 2)
        row.extend((255, 255, 255, round(alpha)))
    rows.append(row)
def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data))
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
path = Path(__file__).resolve().parents[1]/"media/rixflix/card-focus-glow.png"
path.write_bytes(png)
print(f"{path}: {len(png)} bytes; decoded 64 KiB")
