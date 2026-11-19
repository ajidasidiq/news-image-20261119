#!/usr/bin/env python3
"""News in one image: Thursday 19 November 2026.

Draws a 1024x1024 newspaper-style infographic summing up the day's
world news and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Pure standard library: the picture is rasterised into an RGB buffer
with a hand-built 5x7 bitmap font and written out as a PNG with zlib.
No network, no clock, no randomness: every run writes identical bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows of 5 characters ('#' = ink).
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".###.", "#....", "#....", "#....", ".###."),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".###."),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': (".....", ".#...", ".....", "##...", ".#...", ".#...", "###.."),
    'j': (".....", "..#..", ".....", "..#..", "..#..", "#.#..", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': ("##...", ".#...", ".#...", ".#...", ".#...", ".#...", "###.."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", ".#..."),
    ',': (".....", ".....", ".....", ".....", ".....", ".#...", "#...."),
    ':': (".....", ".....", ".#...", ".....", ".#...", ".....", "....."),
    ';': (".....", ".....", ".#...", ".....", ".#...", ".#...", "#...."),
    '!': (".#...", ".#...", ".#...", ".#...", ".#...", ".....", ".#..."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": (".#...", ".#...", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '+': (".....", ".....", "..#..", ".###.", "..#..", ".....", "....."),
    '=': (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '\u2022': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    '\u2013': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '\u2014': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '\u2019': (".#...", ".#...", ".#...", ".....", ".....", ".....", "....."),
    '\u00b0': (".###.", "#...#", ".###.", ".....", ".....", ".....", "....."),
}

# The 'g' glyph above has no descender tail in the 7-row grid; fix it
# so the tail drops below the baseline like 'j', 'p', 'q', 'y'.
FONT['g'] = (".....", ".....", ".####", "#...#", "#...#", ".####", "....#")


def glyph(ch):
    return FONT.get(ch, FONT['?'])


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in s.split('\n'):
        words = para.split(' ')
        cur = ''
        for word in words:
            trial = word if not cur else cur + ' ' + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines

# ---------------------------------------------------------------- canvas
class Img:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = yy * self.w * 3
            for xx in range(x0, x1):
                i = base + xx * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, length, c, t=1):
        self.fill_rect(x, y, length, t, c)

    def vline(self, x, y, length, c, t=1):
        self.fill_rect(x, y, t, length, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=3):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            dx2 = int(max(0, (r - t) * (r - t) - dy * dy) ** 0.5) if abs(dy) < r - t else 0
            self.fill_rect(cx - dx, cy + dy, dx - dx2, 1, c)
            self.fill_rect(cx + dx2 + 1, cy + dy, dx - dx2, 1, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, max(1, int(xs[i + 1]) - int(xs[i])), 1, c)

    def arc(self, cx, cy, r, a0, a1, c, t=3):
        import math
        steps = max(8, int(r * 1.2))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.disc(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), t, c)

    def text(self, x, y, s, scale, c, align='left', bold=False):
        w = text_width(s, scale)
        if align == 'center':
            x -= w // 2
        elif align == 'right':
            x -= w
        extra = 1 if bold else 0
        for ci, ch in enumerate(s):
            gx = x + ci * 6 * scale
            for row in range(7):
                bits = glyph(ch)[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.fill_rect(gx + col * scale, y + row * scale,
                                       scale + extra, scale, c)
        return w

    def para(self, x, y, s, scale, c, max_w, leading, bold=False):
        for line in wrap_text(s, scale, max_w):
            self.text(x, y, line, scale, c, bold=bold)
            y += 7 * scale + leading
        return y


# ------------------------------------------------------------------ PNG
def write_png(img, path):
    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out
    ihdr = struct.pack('>IIBBBBB', img.w, img.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = img.w * 3
    for y in range(img.h):
        raw.append(0)
        raw += img.px[y * stride:(y + 1) * stride]
    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)


# -------------------------------------------------------------- palette
PAPER = (247, 242, 230)
INK = (16, 35, 63)        # deep navy
INK_SOFT = (52, 68, 92)
RED = (192, 57, 43)
AMBER = (232, 163, 61)
TEAL = (27, 122, 110)
BLUE = (42, 108, 182)
PURPLE = (106, 76, 147)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
GREY = (120, 116, 104)


# -------------------------------------------------------------- icons
def icon_controller(img, x, y, s, c):
    # simple game controller, s = half-width
    img.fill_rect(x - s, y - s // 2, 2 * s, s, c)
    img.disc(x - s, y, s // 2, c)
    img.disc(x + s, y, s // 2, c)
    img.fill_rect(x - s // 2 - 4, y - 4, 8, 8, PAPER)
    img.disc(x + s // 2, y - 2, 4, PAPER)
    img.disc(x + s // 2 + 9, y + 3, 4, PAPER)


def icon_burst(img, cx, cy, r, c):
    import math
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r // 2
        pts.append((int(cx + rr * math.cos(ang)), int(cy + rr * math.sin(ang))))
    img.poly(pts, c)
    img.disc(cx, cy, r // 3, AMBER)


def icon_capitol(img, x, y, w, h, c):
    # dome + columns + base, top-left (x, y), size w x h
    img.disc(x + w // 2, y + h // 4, w // 4, c)
    img.fill_rect(x + w // 4, y + h // 4, w // 2, h // 6, c)
    for i in range(4):
        cx = x + w // 6 + i * w // 5
        img.fill_rect(cx, y + h // 4 + h // 6, 6, h // 2, c)
    img.fill_rect(x, y + h // 4 + h // 6 + h // 2, w, h // 8, c)
    img.fill_rect(x - 4, y + h - h // 10, w + 8, h // 10, c)


def icon_scales(img, cx, cy, s, c):
    img.vline(cx, cy - s, 2 * s, c, 3)
    img.hline(cx - s, cy - s, 2 * s, c, 3)
    img.disc(cx, cy - s - 4, 5, c)
    for sx in (cx - s, cx + s):
        img.line(sx, cy - s, sx - 8, cy + s // 2, c, 2)
        img.line(sx, cy - s, sx + 8, cy + s // 2, c, 2)
        img.arc(sx, cy + s // 2, 10, 0, 3.14159, c, 3)
    img.fill_rect(cx - 14, cy + s, 28, 4, c)


def icon_cyclone(img, cx, cy, r, c):
    import math
    pts = []
    for i in range(90):
        t = i / 90.0 * 3.2 * math.pi
        rr = r * (1 - i / 130.0)
        pts.append((int(cx + rr * math.cos(t)), int(cy + rr * math.sin(t))))
    for i in range(len(pts) - 1):
        img.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, 3)
    img.disc(cx, cy, 5, c)


# ------------------------------------------------------------- layout
def build():
    img = Img(W, H, PAPER)
    img.rect(6, 6, W - 12, H - 12, INK, 3)

    # ---- masthead ----
    img.fill_rect(12, 12, W - 24, 138, INK)
    img.text(W // 2, 30, "THURSDAY, 19 NOVEMBER 2026", 5, WHITE, 'center', bold=True)
    img.hline(212, 96, 600, GOLD, 3)
    img.text(W // 2, 112, "THE WORLD IN ONE IMAGE", 3, AMBER, 'center', bold=True)
    img.fill_rect(12, 150, W - 24, 8, RED)

    # ---- lead story: the Shenzhen trilateral ----
    lx, ly, lw, lh = 24, 170, W - 48, 308
    img.fill_rect(lx, ly, lw, lh, CARD)
    img.rect(lx, ly, lw, lh, INK, 2)
    img.fill_rect(lx, ly, 10, lh, RED)
    img.text(lx + 34, ly + 20, "SHENZHEN \u2022 APEC SUMMIT", 2, RED, bold=True)
    img.text(lx + 34, ly + 52, "TRUMP, XI AND PUTIN", 5, INK, bold=True)
    img.text(lx + 34, ly + 92, "MEET FACE TO FACE", 5, INK, bold=True)
    img.hline(lx + 34, ly + 140, 560, GOLD, 3)
    img.para(lx + 34, ly + 158,
             "The first-ever trilateral of the US, China and Russia. "
             "Xi hosts the APEC talks in Shenzhen. Nuclear arms top "
             "the agenda.",
             3, INK_SOFT, 560, 8)
    # three leaders, three circles
    cx0, cy0 = 812, 310
    for i, (letter, col) in enumerate((('T', BLUE), ('X', RED), ('P', TEAL))):
        cx = cx0 + (i - 1) * 74
        cy = cy0 + (14 if i == 1 else 0)
        img.ring(cx, cy, 52, col, 5)
        img.disc(cx, cy, 44, col)
        img.text(cx, cy - 24, letter, 7, WHITE, 'center', bold=True)
    img.text(cx0, cy0 + 84, "FIRST-EVER TRILATERAL", 2, INK, 'center', bold=True)
    img.text(cx0, cy0 + 104, "OF THE THREE NUCLEAR POWERS", 2, GREY, 'center')

    # ---- three cards row ----
    cards = [
        ("CULTURE \u2022 GAMING", AMBER, "GTA VI IS HERE",
         "AT LAST",
         "After a 13-year wait, Rockstar's blockbuster rolls out "
         "worldwide at midnight. Pre-orders top $1.5bn.",
         icon_controller),
        ("MIDDLE EAST", RED, "US-IRAN FIRE",
         "SPREADS",
         "Iran strikes US bases in Kuwait and Bahrain. The US had "
         "hit a missile site on Qeshm Island.",
         icon_burst),
        ("WASHINGTON", BLUE, "JEFFRIES SET TO",
         "MAKE HISTORY",
         "Democrats nominate Hakeem Jeffries for Speaker. He would "
         "be the first Black Speaker in US history.",
         icon_capitol),
    ]
    cy, ch, cw, gap = 494, 220, 314, 16
    for i, (kick, col, h1, h2, body, icon) in enumerate(cards):
        x = 24 + i * (cw + gap)
        img.fill_rect(x, cy, cw, ch, CARD)
        img.rect(x, cy, cw, ch, INK, 2)
        img.fill_rect(x, cy, cw, 8, col)
        img.text(x + 18, cy + 22, kick, 2, col, bold=True)
        img.text(x + 18, cy + 56, h1, 3, INK, bold=True)
        img.text(x + 18, cy + 82, h2, 3, INK, bold=True)
        img.para(x + 18, cy + 116, body, 2, INK_SOFT, cw - 36, 4)
        if icon is icon_controller:
            icon_controller(img, x + cw - 40, cy + 34, 24, col)
        elif icon is icon_burst:
            icon_burst(img, x + cw - 40, cy + 34, 22, col)
        else:
            icon_capitol(img, x + cw - 62, cy + 12, 48, 40, col)

    # ---- two wide cards row ----
    wide = [
        ("THE HAGUE", PURPLE, "MYANMAR GENOCIDE VERDICT",
         "The UN's top court rules today in the landmark Rohingya "
         "genocide case against Myanmar.",
         icon_scales),
        ("INDIA", TEAL, "CYCLONE AKVAN NEARS COAST",
         "Cyclone Akvan nears India's east coast, landfall due at "
         "Machilipatnam.",
         icon_cyclone),
    ]
    wy, wh, ww = 730, 190, 480
    for i, (kick, col, head, body, icon) in enumerate(wide):
        x = 24 + i * (ww + gap)
        img.fill_rect(x, wy, ww, wh, CARD)
        img.rect(x, wy, ww, wh, INK, 2)
        img.fill_rect(x, wy, 8, wh, col)
        img.text(x + 26, wy + 20, kick, 2, col, bold=True)
        hlines = wrap_text(head, 3, ww - 130)
        hy = wy + 50
        for line in hlines:
            img.text(x + 26, hy, line, 3, INK, bold=True)
            hy += 26
        img.para(x + 26, hy + 10, body, 2, INK_SOFT, ww - 140, 3)
        if icon is icon_scales:
            icon_scales(img, x + ww - 52, wy + 100, 30, col)
        else:
            icon_cyclone(img, x + ww - 52, wy + 100, 34, col)

    # ---- ticker: also today ----
    ty = 934
    img.fill_rect(12, ty, W - 24, 76, INK)
    img.text(36, ty + 10, "ALSO TODAY", 2, AMBER, bold=True)
    img.text(36, ty + 30, "Voyager 1 reaches one light-day from Earth. EU proposes a",
            2, WHITE)
    img.text(36, ty + 50, "EUR 45bn Ukraine loan. Van Gogh sells for a record $190.4m.",
            2, WHITE)
    return img


def main():
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    img = build()
    write_png(img, os.path.join(outdir, 'entry.png'))


if __name__ == '__main__':
    main()
