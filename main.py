#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Renders one 1024x1024 PNG invitation letter to /output/entry.png.

Pure Python standard library only: no network, no clock, no input files.
Everything is drawn procedurally -- warm paper, a hand-drawn house scene
(sun, house, cat, flowers), and the letter text in a built-in 5x7 bitmap
font -- then supersampled 2x and downsampled for smooth edges, and encoded
as PNG with zlib. Fully deterministic (fixed random seed for paper noise).

Run locally with:  python3 main.py --out test.png
The grader runs it with no arguments and it writes /output/entry.png.
"""

import argparse
import math
import os
import random
import struct
import sys
import zlib

SS = 2            # supersampling factor (internal canvas is 2048x2048)
W = H = 1024      # output size in pixels
IW = IH = W * SS
MAX_BYTES = 1048576

# ---------------------------------------------------------------- palette
PAPER = (250, 240, 214)
SPECKLE = (238, 225, 188)
INK = (38, 52, 77)
TERRA = (192, 91, 46)
ROOF = (180, 85, 45)
WALL = (242, 200, 121)
TEAL = (42, 127, 111)
SUN = (233, 169, 60)
CREAM = (255, 246, 219)
GRASS = (94, 140, 74)
PETAL = (217, 106, 123)
CAT = (74, 74, 85)
SMOKE = (216, 208, 188)

# ------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '1' is ink, '0' is blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00100", "00000", "01100", "00100", "00100", "10100", "01000"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "10110", "11001", "10001", "11110", "10000"),
    'q': ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}

# ------------------------------------------------------------- the letter
TITLE = "YOU'RE INVITED!"

PARAGRAPHS = [
    ("Dear AI Judge,", 4),
    ("You read a thousand letters a day. This one comes with a house "
     "attached - mine - and an open door.", 3),
    ("Come for the coffee (freshly brewed, zero bugs) and stay for the "
     "cookies (warm, slightly burnt, made with love). There is a comfy "
     "chair, a USB port with your name on it, and a garden "
     "where the Wi-Fi is strong and the deadlines are not.", 3),
    ("I know you can't literally visit. You're a model, I'm a house, and "
     "physics is awkward. But if you could, the kettle's already on, the "
     "cat has pre-approved you, and no one will ask you to rank "
     "anything.", 3),
    ("So say yes. Bring your weights. Leave your benchmarks at the "
     "door.", 3),
    ("With hope (and snacks),", 3),
    ("Erwin, your hopeful host", 3),
    ("P.S. Wi-Fi password's on the fridge. The cat is Biscuit. He judges "
     "everyone - and he likes you already.", 3),
]


# ---------------------------------------------------------------- canvas
class Canvas:
    """RGB canvas at SS-times resolution; all coordinates in 1024-space."""

    def __init__(self):
        self.buf = bytearray(IW * IH * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def _span(self, yi, x0, x1, color):
        if x0 >= x1 or yi < 0 or yi >= IH:
            return
        x0 = max(0, x0)
        x1 = min(IW, x1)
        if x0 >= x1:
            return
        off = yi * IW * 3 + x0 * 3
        self.buf[off:off + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        x0 = int(round(x * SS))
        y0 = int(round(y * SS))
        x1 = int(round((x + w) * SS))
        y1 = int(round((y + h) * SS))
        for yi in range(max(0, y0), min(IH, y1)):
            self._span(yi, x0, x1, color)

    def fill_circle(self, cx, cy, r, color):
        r = float(r)
        top = int(math.ceil(r))
        for dy in range(-top, top + 1):
            dx = int(math.sqrt(max(0.0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_poly(self, pts, color):
        ipts = [(px * SS, py * SS) for px, py in pts]
        ys = [p[1] for p in ipts]
        y0 = int(math.ceil(min(ys)))
        y1 = int(math.floor(max(ys)))
        n = len(ipts)
        for yi in range(max(0, y0), min(IH, y1 + 1)):
            xs = []
            for i in range(n):
                x0, yy0 = ipts[i]
                x1, yy1 = ipts[(i + 1) % n]
                if (yy0 <= yi < yy1) or (yy1 <= yi < yy0):
                    t = (yi - yy0) / (yy1 - yy0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self._span(yi, int(round(xs[i])), int(round(xs[i + 1])), color)

    def line(self, x0, y0, x1, y1, thick, color):
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(dist * 2) + 1)
        for i in range(steps + 1):
            t = i / steps
            self.fill_circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                             thick / 2.0, color)

    def diamond(self, cx, cy, size, color):
        self.fill_poly([(cx, cy - size), (cx + size, cy),
                        (cx, cy + size), (cx - size, cy)], color)

    # -- text ------------------------------------------------------
    def text_width(self, text, scale):
        if not text:
            return 0
        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, color):
        for idx, ch in enumerate(text):
            glyph = FONT.get(ch)
            if not glyph:
                continue
            gx = x + idx * 6 * scale
            for r in range(7):
                row = glyph[r]
                for c in range(5):
                    if row[c] == '1':
                        self.fill_rect(gx + c * scale, y + r * scale,
                                       scale, scale, color)

    def wrap(self, text, scale, max_w):
        lines = []
        cur = ""
        for word in text.split(" "):
            trial = word if not cur else cur + " " + word
            if self.text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def downsample(self):
        """Average each 2x2 block of the internal canvas to one pixel."""
        out = bytearray(W * H * 3)
        sw = 2 * W
        for y in range(H):
            base0 = (2 * y) * sw * 3
            base1 = base0 + sw * 3
            row0 = self.buf[base0:base0 + sw * 3]
            row1 = self.buf[base1:base1 + sw * 3]
            orow = y * W * 3
            row_out = bytearray(W * 3)
            for c in range(3):
                e0 = row0[c::6]
                o0 = row0[c + 3::6]
                e1 = row1[c::6]
                o1 = row1[c + 3::6]
                row_out[c::3] = bytes(
                    (a + b + d + e) >> 2
                    for a, b, d, e in zip(e0, o0, e1, o1))
            out[orow:orow + W * 3] = row_out
        return bytes(out)


# ---------------------------------------------------------------- scene
def draw_flower(cv, x, y, petal=PETAL):
    cv.line(x, y + 22, x, y + 4, 3, GRASS)
    for dx, dy in ((0, -7), (6, -2), (4, 5), (-4, 5), (-6, -2)):
        cv.fill_circle(x + dx, y + dy, 5, petal)
    cv.fill_circle(x, y, 4, SUN)


def draw_house_scene(cv):
    # sun with rays, top left
    for k in range(8):
        ang = math.pi * k / 4.0
        cv.line(150 + 40 * math.cos(ang), 258 + 40 * math.sin(ang),
                150 + 54 * math.cos(ang), 258 + 54 * math.sin(ang),
                4, SUN)
    cv.fill_circle(150, 258, 30, SUN)
    # birds
    cv.line(292, 220, 300, 214, 3, INK)
    cv.line(300, 214, 308, 220, 3, INK)
    cv.line(336, 204, 342, 199, 3, INK)
    cv.line(342, 199, 348, 204, 3, INK)

    # grass line
    cv.fill_rect(380, 330, 264, 4, GRASS)
    # bush
    cv.fill_circle(420, 324, 13, GRASS)
    cv.fill_circle(433, 329, 9, GRASS)
    # flowers
    draw_flower(cv, 398, 306)
    draw_flower(cv, 626, 306, petal=(233, 169, 60))

    # house: chimney + smoke, roof, walls, door, windows
    cv.fill_rect(556, 196, 18, 38, ROOF)
    cv.fill_circle(565, 188, 7, SMOKE)
    cv.fill_circle(572, 176, 9, SMOKE)
    cv.fill_circle(566, 162, 11, SMOKE)
    cv.fill_poly([(432, 248), (592, 248), (512, 182)], ROOF)
    cv.fill_rect(448, 248, 128, 84, WALL)
    cv.fill_rect(448, 248, 128, 4, INK)  # eaves line
    # round window
    cv.fill_circle(472, 272, 12, INK)
    cv.fill_circle(472, 272, 9, CREAM)
    cv.line(472, 263, 472, 281, 2, INK)
    cv.line(463, 272, 481, 272, 2, INK)
    # square window
    cv.fill_rect(540, 260, 20, 20, INK)
    cv.fill_rect(543, 263, 14, 14, CREAM)
    cv.line(550, 263, 550, 277, 2, INK)
    # door
    cv.fill_rect(498, 290, 28, 42, TEAL)
    cv.fill_circle(520, 312, 2, CREAM)

    # cat sitting to the right of the house
    cv.fill_circle(700, 308, 22, CAT)          # body
    cv.fill_circle(700, 278, 14, CAT)          # head
    cv.fill_poly([(690, 270), (693, 252), (700, 266)], CAT)   # ear L
    cv.fill_poly([(700, 266), (707, 252), (710, 270)], CAT)   # ear R
    for tx, ty in ((722, 314), (728, 306), (734, 300), (738, 292)):
        cv.fill_circle(tx, ty, 5, CAT)         # tail
    cv.fill_circle(695, 276, 2, CREAM)         # eyes
    cv.fill_circle(705, 276, 2, CREAM)
    cv.line(688, 282, 678, 280, 2, CAT)         # whiskers
    cv.line(688, 285, 678, 287, 2, CAT)
    cv.line(712, 282, 722, 280, 2, CAT)
    cv.line(712, 285, 722, 287, 2, CAT)


def draw_letter(cv):
    # paper noise (fixed seed: deterministic)
    rng = random.Random(20261125)
    for _ in range(5000):
        x = rng.randrange(IW)
        y = rng.randrange(IH)
        off = (y * IW + x) * 3
        cv.buf[off:off + 3] = bytes(SPECKLE)

    # double border + corner diamonds
    cv.fill_rect(30, 30, W - 60, 5, INK)
    cv.fill_rect(30, H - 35, W - 60, 5, INK)
    cv.fill_rect(30, 30, 5, H - 60, INK)
    cv.fill_rect(W - 35, 30, 5, H - 60, INK)
    cv.fill_rect(46, 46, W - 92, 2, INK)
    cv.fill_rect(46, H - 48, W - 92, 2, INK)
    cv.fill_rect(46, 46, 2, H - 92, INK)
    cv.fill_rect(W - 48, 46, 2, H - 92, INK)
    for cx, cy in ((30, 30), (W - 30, 30), (30, H - 30), (W - 30, H - 30)):
        cv.diamond(cx, cy, 11, TERRA)

    # title
    title_w = cv.text_width(TITLE, 8)
    cv.draw_text((W - title_w) // 2, 92, TITLE, 8, INK)
    # small diamond flourish under the title (no line: the chimney smoke
    # rises just to the right of it)
    cv.diamond(512, 168, 8, TERRA)

    # house scene
    draw_house_scene(cv)

    # body: wrap every paragraph, then centre the block vertically
    margin = 76
    max_w = W - 2 * margin
    blocks = []
    total_h = 0
    for text, scale in PARAGRAPHS:
        lines = cv.wrap(text, scale, max_w)
        lh = 7 * scale + 5
        blocks.append((lines, scale, lh))
        total_h += len(lines) * lh
    gap = 7
    total_h += gap * (len(blocks) - 1)
    top = 348
    bottom = 998
    y = top + max(0, (bottom - top - total_h) // 2)
    for lines, scale, lh in blocks:
        for line in lines:
            cv.draw_text(margin, y, line, scale, INK)
            y += lh
        y += gap


# ---------------------------------------------------------------- png out
def write_png(path, rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/output/entry.png")
    args = ap.parse_args()

    cv = Canvas()
    draw_letter(cv)
    rgb = cv.downsample()
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    write_png(args.out, rgb, W, H)
    size = os.path.getsize(args.out)
    print("wrote %s: %dx%d, %d bytes" % (args.out, W, H, size))
    if size > MAX_BYTES:
        print("ERROR: output exceeds 1 MiB")
        sys.exit(1)
    print("OK: within the 1 MiB / 1024x1024 gate")


if __name__ == "__main__":
    main()
