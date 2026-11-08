#!/usr/bin/env python3
"""Reproducible rounded nine-slice panel for the native seek preview."""
import math
from pathlib import Path
import struct
import zlib

size, radius = 128, 20
raw = bytearray()
for y in range(size):
    raw.append(0)
    for x in range(size):
        qx, qy = abs(x + .5 - size / 2) - (size / 2 - radius), abs(y + .5 - size / 2) - (size / 2 - radius)
        distance = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius
        raw.extend((255, 255, 255, round(255 * max(0, min(1, .5 - distance)))))
def chunk(kind, value):
    return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value))
image = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
image += chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
(Path(__file__).resolve().parents[1] / 'media/rixflix/trickplay-panel.png').write_bytes(image)
