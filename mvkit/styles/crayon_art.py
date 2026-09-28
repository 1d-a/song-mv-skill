"""Crayon picture-book element library. Each element draws into its own RGBA canvas (local coords)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

DARK = (40, 38, 42)
RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE = (220, 60, 45), (238, 128, 40), (246, 196, 55), (70, 160, 90), (50, 115, 200), (160, 95, 185)
WOOD, WOODD, CREAM, GREY, BROWN = (190, 130, 75), (130, 85, 50), (245, 232, 195), (140, 140, 150), (120, 80, 50)
ROOFS = [RED, BLUE, ORANGE, GREEN, PURPLE]


def jline(d, pts, color, width, r, jit=3, n=3):
    for _ in range(n):
        q = [(x + r.normal() * jit, y + r.normal() * jit) for x, y in pts]
        d.line(q, fill=tuple(color[:3]) + (int(r.uniform(140, 230)),), width=max(1, int(width * r.uniform(0.7, 1.1))), joint='curve')


def hatch(lay, poly, color, r, spacing=9, angle=0.9, width=4, jit=2, amin=140, amax=230):
    m = Image.new('L', lay.size)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    tmp = Image.new('RGBA', lay.size)
    d = ImageDraw.Draw(tmp)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    L = (x1 - x0) + (y1 - y0) + 10
    ca, sa = np.cos(angle), np.sin(angle)
    for k in np.arange(-L, L, spacing):
        cx, cy = (x0 + x1) / 2 + k * -sa, (y0 + y1) / 2 + k * ca
        d.line([(cx - ca * L + r.normal() * jit, cy - sa * L + r.normal() * jit), (cx + ca * L, cy + sa * L)],
               fill=tuple(color[:3]) + (int(r.uniform(amin, amax)),), width=width)
    tmp.putalpha(Image.fromarray(np.minimum(np.asarray(tmp.getchannel('A')), np.asarray(m))))
    lay.alpha_composite(tmp)


def outline(lay, pts, color, r, width=5, closed=True):
    tmp = Image.new('RGBA', lay.size)
    jline(ImageDraw.Draw(tmp), list(pts) + ([pts[0]] if closed else []), color, width, r, 2.2, 2)
    lay.alpha_composite(tmp)


def stroke(lay, pts, color, r, width=5, jit=2.2, n=2):
    tmp = Image.new('RGBA', lay.size)
    jline(ImageDraw.Draw(tmp), pts, color, width, r, jit, n)
    lay.alpha_composite(tmp)


def shape(lay, poly, col, r, ang=0.9, sp=8, w=5, line=DARK, lw=5, base=110, col2=None):
    poly = [(float(x), float(y)) for x, y in poly]
    tmp = Image.new('RGBA', lay.size)
    ImageDraw.Draw(tmp).polygon(poly, fill=tuple(col[:3]) + (base,))
    lay.alpha_composite(tmp)
    hatch(lay, poly, col, r, sp, ang, w)
    if col2 is not None:
        hatch(lay, poly, col2, r, sp * 2.2, ang + 1.4, max(2, w - 2), amin=90, amax=170)
    if line is not None:
        outline(lay, poly, line, r, lw)


def blobs(lay, ells, col, r, ang=0.6, sp=8, w=5, line=DARK, lw=5, base=150, col2=None):
    """union of ellipses (cx, cy, rx, ry) filled with crayon hatch and a single outer contour"""
    m = Image.new('L', lay.size)
    dm = ImageDraw.Draw(m)
    for cx, cy, rx, ry in ells:
        dm.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    tmp = Image.new('RGBA', lay.size, tuple(col[:3]) + (0,))
    tmp.putalpha(m.point(lambda v: v * base // 255))
    lay.alpha_composite(tmp)
    box = m.getbbox()
    poly = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    for c2, a2, s2, w2 in [(col, ang, sp, w)] + ([(col2, ang + 1.4, sp * 2.2, max(2, w - 2))] if col2 is not None else []):
        t2 = Image.new('RGBA', lay.size)
        hatch(t2, poly, c2, r, s2, a2, w2)
        t2.putalpha(Image.fromarray(np.minimum(np.asarray(t2.getchannel('A')), np.asarray(m))))
        lay.alpha_composite(t2)
    if line is not None:
        ring = np.asarray(m.filter(ImageFilter.MaxFilter(2 * (lw // 2) + 1)), np.float32) - np.asarray(m, np.float32)
        ring = np.clip(ring * r.uniform(0.75, 0.95, ring.shape), 0, 255)
        t3 = Image.new('RGBA', lay.size, tuple(line[:3]) + (0,))
        t3.putalpha(Image.fromarray(ring.astype(np.uint8)))
        lay.alpha_composite(t3)


def cloud_ells(cx, cy, w, h, n=5, seed=0):
    rs = np.random.default_rng(seed)
    out = [(cx, cy + h * 0.15, w / 2, h * 0.3)]
    for k in range(n):
        x = cx - w / 2 + w * (k + 0.5) / n
        rr = w / n * rs.uniform(0.55, 0.8) * (1.25 if 0 < k < n - 1 else 0.95)
        out.append((x, cy - h * 0.05 - rr * 0.35 * (1 if 0 < k < n - 1 else 0), rr, rr * 0.85))
    return out


def ell(cx, cy, rx, ry, n=40, a0=0.0, a1=2 * np.pi, wob=0.0, seed=0):
    rs = np.random.default_rng(seed)
    ph = rs.uniform(0, 6, 3)
    out = []
    for a in np.linspace(a0, a1, n, endpoint=a1 - a0 < 2 * np.pi - 1e-6):
        k = 1 + wob * (0.5 * np.sin(3 * a + ph[0]) + 0.3 * np.sin(5 * a + ph[1]) + 0.2 * np.sin(7 * a + ph[2]))
        out.append((cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)))
    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def puff(cx, cy, w, h, n=6, seed=0):
    """cloud outline made of bumps"""
    pts = []
    rs = np.random.default_rng(seed)
    bumps = [(cx - w / 2 + w * (k + 0.5) / n, cy - h * (0.15 + 0.25 * rs.random())) for k in range(n)]
    for bx, by in bumps:
        rr = w / n * 0.75
        pts += [(bx + rr * np.cos(a), by + rr * 0.9 * np.sin(a)) for a in np.linspace(np.pi, 2 * np.pi, 8)]
    pts += [(cx + w / 2 + h * 0.3 * np.cos(a), cy + h * 0.3 * np.sin(a)) for a in np.linspace(-np.pi / 2, np.pi / 2, 8)]
    pts += [(cx + w / 2 - w * k / 12, cy + h * 0.3 + 6 * np.sin(k)) for k in range(13)]
    pts += [(cx - w / 2 + h * 0.3 * np.cos(a), cy + h * 0.3 * np.sin(a)) for a in np.linspace(np.pi / 2, 3 * np.pi / 2, 8)]
    return pts


# ---------------------------------------------------------------- elements
# every element: fn(lay, r, p) with p = item params; SIZE[name] = (w, h)
SIZE, FN = {}, {}


def el(name, w, h):
    def deco(fn):
        SIZE[name] = (w, h)
        FN[name] = fn
        return fn
    return deco


@el('sword', 260, 1000)
def _sword(lay, r, p):
    cx = 130
    blade = [(cx - 34, 330), (cx + 34, 330), (cx + 30, 900), (cx, 985), (cx - 30, 900)][::-1]
    blade = [(cx, 20), (cx + 34, 110), (cx + 36, 700), (cx - 36, 700), (cx - 34, 110)]
    shape(lay, blade, WOOD, r, 2.6, 7, 5, col2=WOODD)
    stroke(lay, [(cx, 60), (cx + 4, 680)], WOODD, r, 4)
    for y in (220, 420, 560):
        stroke(lay, [(cx - 20, y), (cx - 6, y + 14), (cx - 18, y + 30)], WOODD, r, 3, 1, 1)
    shape(lay, rect(cx - 120, 700, cx + 120, 745), (90, 60, 40), r, 0.3, 6, 5)
    shape(lay, rect(cx - 26, 745, cx + 26, 930), (150, 60, 45), r, 0.2, 6, 5)
    for y in range(760, 930, 26):
        stroke(lay, [(cx - 26, y), (cx + 26, y + 12)], (90, 40, 30), r, 4, 1, 1)
    shape(lay, ell(cx, 955, 38, 30), (90, 60, 40), r, 1, 6, 5)
    if p.get('tassel', True):
        stroke(lay, [(cx, 980), (cx - 12, 990), (cx - 30, 998)], RED, r, 5, 1, 2)


@el('robe', 560, 640)
def _robe(lay, r, p):
    body = [(180, 40), (380, 40), (470, 120), (540, 300), (470, 330), (430, 230), (440, 600), (400, 570), (370, 620), (330, 575),
            (290, 625), (250, 570), (210, 615), (170, 575), (130, 600), (130, 230), (90, 330), (20, 300), (90, 120)]
    shape(lay, body, (95, 120, 170), r, 1.3, 8, 5, col2=(120, 110, 130))
    stroke(lay, [(280, 40), (250, 200), (300, 380)], DARK, r, 4, 2, 1)
    stroke(lay, [(180, 40), (280, 150), (380, 40)], DARK, r, 5, 2, 1)
    for (x, y, c) in [(190, 330, (200, 150, 90)), (360, 420, (150, 170, 110)), (230, 480, (210, 120, 100))]:
        shape(lay, rect(x - 32, y - 28, x + 32, y + 28), c, r, 0.4, 6, 4, lw=3)
        for k in range(4):
            stroke(lay, [(x - 32 + k * 20, y - 34), (x - 30 + k * 20, y - 22)], DARK, r, 2, 0.5, 1)
    if p.get('blood'):
        for (x, y, rr) in [(300, 250, 70), (230, 330, 45), (340, 360, 40)]:
            shape(lay, ell(x, y, rr, rr * 1.3, wob=0.35, seed=x), (185, 30, 35), r, 0.8, 5, 5, line=None, base=150)


@el('crow', 240, 200)
def _crow(lay, r, p):
    body = ell(120, 120, 80, 55)
    shape(lay, body, (55, 55, 70), r, 0.6, 6, 5)
    shape(lay, ell(175, 75, 40, 36), (55, 55, 70), r, 0.6, 6, 5)
    beak = [(205, 62), (240, 72), (206, 80)] if not p.get('open', True) else [(205, 60), (240, 48), (212, 72), (240, 92), (206, 84)]
    shape(lay, beak, YELLOW, r, 0.3, 5, 4, lw=3)
    shape(lay, ell(185, 68, 9, 9), (250, 250, 250), r, 0, 3, 3, lw=2)
    shape(lay, [(60, 110), (0, 90), (40, 140)], (40, 40, 55), r, 0.4, 5, 4)
    stroke(lay, [(110, 172), (105, 198)], ORANGE, r, 4, 1, 1)
    stroke(lay, [(140, 172), (145, 198)], ORANGE, r, 4, 1, 1)


@el('fence', 900, 260)
def _fence(lay, r, p):
    shape(lay, rect(0, 90, 900, 120), WOOD, r, 0.1, 7, 4)
    shape(lay, rect(0, 180, 900, 210), WOOD, r, 0.1, 7, 4)
    for x in range(30, 900, 110):
        shape(lay, [(x, 60), (x + 25, 25), (x + 50, 60), (x + 50, 250), (x, 250)], (210, 160, 100), r, 1.5, 7, 4)


@el('tree', 520, 820)
def _tree(lay, r, p):
    shape(lay, [(230, 820), (245, 520), (190, 420), (215, 410), (255, 480), (270, 380), (295, 385), (285, 500), (340, 430), (355, 450), (300, 540), (300, 820)],
          BROWN, r, 1.6, 7, 5)
    if p.get('bare'):
        for pts in [[(270, 390), (230, 250), (180, 180)], [(290, 390), (350, 260), (420, 210)], [(200, 420), (110, 330)], [(345, 445), (450, 380)]]:
            stroke(lay, pts, BROWN, r, 9, 2, 2)
        return
    col = p.get('col', GREEN)
    for k, (x, y, rx, ry) in enumerate([(260, 260, 200, 170), (160, 360, 130, 110), (370, 350, 130, 110), (260, 140, 140, 110)]):
        shape(lay, ell(x, y, rx, ry, wob=0.12, seed=k + 3), col, r, 0.8 + k * 0.4, 8, 5, col2=(40, 120, 70))


@el('pine', 300, 700)
def _pine(lay, r, p):
    shape(lay, rect(135, 560, 165, 700), BROWN, r, 1.5, 6, 4)
    for k, (y, w) in enumerate([(120, 80), (260, 120), (400, 150), (540, 170)]):
        shape(lay, [(150, y - 120), (150 + w, y + 30), (150 - w, y + 30)], (50, 130, 80), r, 0.7 + k * 0.3, 7, 5)


@el('moon_sleep', 460, 460)
def _moon_sleep(lay, r, p):
    cx, cy = 230, 240
    poly = ell(cx, cy, 190, 190, 30, 0.5 * np.pi, 1.5 * np.pi) + ell(cx + 80, cy - 10, 150, 175, 30, 1.35 * np.pi, 0.65 * np.pi)
    poly = ell(cx, cy, 190, 190, 30, 0.45 * np.pi, 1.55 * np.pi) + [(cx + 80 + 150 * np.cos(a), cy - 5 + 175 * np.sin(a)) for a in np.linspace(1.4 * np.pi, 0.6 * np.pi, 30)]
    shape(lay, poly, YELLOW, r, 0.7, 7, 5, line=(215, 150, 40))
    stroke(lay, [(cx - 120 + 24 * np.cos(a), cy - 40 + 12 * np.sin(a)) for a in np.linspace(0.1, np.pi - 0.1, 10)], DARK, r, 5, 1, 2)
    stroke(lay, [(cx - 110 + 22 * np.cos(a), cy + 70 + 10 * np.sin(a)) for a in np.linspace(0.3, np.pi - 0.3, 10)], (200, 80, 60), r, 4, 1, 2)
    shape(lay, ell(cx - 135, cy + 20, 18, 12), (240, 150, 140), r, 0.2, 4, 3, line=None)
    cap = [(cx - 40, cy - 175), (cx + 60, cy - 205), (cx + 190, cy - 150), (cx + 230, cy - 60), (cx + 140, cy - 150), (cx + 10, cy - 130)]
    shape(lay, cap, BLUE, r, 0.5, 7, 5)
    shape(lay, ell(cx + 235, cy - 50, 26, 26), CREAM, r, 0.5, 5, 4)


@el('moon', 320, 320)
def _moon(lay, r, p):
    shape(lay, ell(160, 160, 130, 130), (250, 220, 110), r, 0.7, 7, 5, line=(215, 150, 40))
    for x, y, rr in [(120, 130, 18), (190, 200, 24), (200, 110, 12)]:
        outline(lay, ell(x, y, rr, rr), (215, 170, 70), r, 3)


@el('crescent', 300, 320)
def _crescent(lay, r, p):
    poly = ell(150, 160, 130, 130, 30, 0.45 * np.pi, 1.55 * np.pi) + [(205 + 105 * np.cos(a), 150 + 120 * np.sin(a)) for a in np.linspace(1.4 * np.pi, 0.6 * np.pi, 30)]
    shape(lay, poly, (250, 220, 110), r, 0.7, 7, 5, line=(215, 150, 40))


@el('sun', 420, 420)
def _sun(lay, r, p):
    shape(lay, ell(210, 210, 110, 110), p.get('col', (240, 95, 50)), r, 0.7, 7, 5, line=(210, 70, 40))
    for a in np.linspace(0, 2 * np.pi, 14, endpoint=False):
        stroke(lay, [(210 + np.cos(a) * 140, 210 + np.sin(a) * 140), (210 + np.cos(a) * 200, 210 + np.sin(a) * 200)], ORANGE, r, 8, 2, 2)


@el('cloud', 560, 260)
def _cloud(lay, r, p):
    blobs(lay, cloud_ells(280, 160, 440, 150, 5, p.get('seed', 1)), p.get('col', (252, 252, 255)), r, 0.4, 10, 4, line=p.get('line', (120, 150, 200)), base=235)


@el('darkcloud', 700, 320)
def _darkcloud(lay, r, p):
    blobs(lay, cloud_ells(350, 190, 580, 190, 6, p.get('seed', 2)), (70, 72, 96), r, 0.8, 7, 5, line=(25, 25, 35), lw=7, base=220, col2=(40, 44, 66))


@el('xiangyun', 560, 280)
def _xiangyun(lay, r, p):
    for k, (x, y, rr) in enumerate([(160, 170, 90), (300, 130, 110), (430, 170, 80)]):
        pts = [(x + rr * (1 - a / 12) * np.cos(a), y + rr * 0.8 * (1 - a / 12) * np.sin(a)) for a in np.linspace(0, 10, 50)]
        shape(lay, ell(x, y + 10, rr, rr * 0.75), (252, 245, 225), r, 0.4, 9, 4, line=None, base=210)
        stroke(lay, pts, (230, 160, 60), r, 6, 1.2, 2)
    stroke(lay, [(40, 240), (200, 250), (380, 238), (530, 250)], (230, 160, 60), r, 6, 1.5, 2)


@el('palace', 640, 520)
def _palace(lay, r, p):
    shape(lay, rect(140, 260, 500, 440), (235, 90, 70), r, 1.6, 7, 5)
    shape(lay, [(80, 270), (560, 270), (500, 190), (140, 190)], (245, 190, 60), r, 0.3, 7, 5)
    shape(lay, [(170, 190), (470, 190), (420, 110), (220, 110)], (235, 90, 70), r, 1.2, 7, 5)
    shape(lay, [(190, 115), (450, 115), (400, 50), (240, 50)], (245, 190, 60), r, 0.3, 7, 5)
    shape(lay, rect(270, 330, 370, 440), (120, 60, 40), r, 2, 6, 4)
    for x in (180, 460):
        shape(lay, rect(x - 18, 270, x + 18, 440), (200, 60, 50), r, 1.5, 6, 4)
    blobs(lay, cloud_ells(320, 470, 600, 90, 6, 5), (252, 248, 235), r, 0.4, 9, 4, line=(230, 160, 60), base=235)


@el('house', 340, 360)
def _house(lay, r, p):
    roof = ROOFS[p.get('c', 0) % 5]
    shape(lay, rect(40, 150, 300, 355), CREAM, r, 0.4, 9, 4, col2=(210, 190, 150))
    shape(lay, [(10, 160), (330, 160), (250, 40), (90, 40)], roof, r, 1.1, 7, 5)
    shape(lay, rect(140, 245, 200, 355), (130, 85, 55), r, 2.5, 6, 4)
    lit = p.get('lit', False)
    for x in (65, 225):
        shape(lay, rect(x, 195, x + 50, 245), (255, 205, 70) if lit else (90, 100, 130), r, 0.3, 5, 4, lw=3)
        stroke(lay, [(x + 25, 195), (x + 25, 245)], DARK, r, 3, 0.5, 1)
    if p.get('chimney', True):
        shape(lay, rect(235, 20, 270, 90), (170, 90, 70), r, 1.5, 5, 4)


@el('village', 1080, 560)
def _village(lay, r, p):
    lit = p.get('lit', True)
    specs = [(120, 300, 0.9, 1), (330, 250, 1.0, 0), (560, 310, 0.85, 2), (760, 240, 1.05, 3), (960, 300, 0.9, 4)]
    for x, y, s, c in specs:
        sub = Image.new('RGBA', (340, 360))
        _house(sub, r, dict(c=c, lit=lit))
        sub = sub.resize((int(340 * s), int(360 * s)), Image.LANCZOS)
        lay.alpha_composite(sub, (int(x - 170 * s), int(y + 180 - 360 * s + 60)))
    shape(lay, rect(0, 520, 1080, 560), (110, 160, 90), r, 2.8, 8, 4, line=None, base=150)


@el('pouch', 380, 460)
def _pouch(lay, r, p):
    cx, cy = 190, 260
    body = [(cx + 60, cy - 120)] + [(cx + 170 * np.cos(a), cy + 50 + 150 * np.sin(a)) for a in np.linspace(-0.3 * np.pi, 1.3 * np.pi, 30)] + [(cx - 60, cy - 120)]
    shape(lay, body, (175, 120, 65), r, 0.9, 7, 5, col2=(120, 80, 45))
    top = [(cx - 75, cy - 120), (cx - 100, cy - 185), (cx - 25, cy - 150), (cx, cy - 200), (cx + 35, cy - 150), (cx + 100, cy - 185), (cx + 75, cy - 120)]
    shape(lay, top, (200, 150, 90), r, 1.6, 7, 4)
    stroke(lay, [(cx - 80, cy - 118), (cx + 80, cy - 118)], RED, r, 9, 1.5, 3)
    shape(lay, ell(cx, cy + 60, 55, 55), (210, 60, 45), r, 0.4, 6, 4, lw=3)
    stroke(lay, [(cx - 25, cy + 35), (cx + 25, cy + 85)], CREAM, r, 5, 1, 1)
    stroke(lay, [(cx + 25, cy + 35), (cx - 25, cy + 85)], CREAM, r, 5, 1, 1)
    stroke(lay, [(cx, cy - 200), (cx + 20, cy - 230), (cx + 50, cy - 240)], DARK, r, 4, 1, 1)


@el('spool', 280, 300)
def _spool(lay, r, p):
    shape(lay, ell(140, 60, 110, 34), WOOD, r, 0.2, 6, 4)
    shape(lay, rect(60, 60, 220, 240), (215, 45, 50), r, 0.15, 5, 5, col2=(160, 25, 35))
    shape(lay, ell(140, 245, 110, 34), WOOD, r, 0.2, 6, 4)
    stroke(lay, [(220, 150), (250, 190), (270, 280)], (215, 45, 50), r, 5, 1, 2)


@el('table', 1000, 300)
def _table(lay, r, p):
    shape(lay, [(60, 40), (940, 40), (1000, 120), (0, 120)], WOOD, r, 0.15, 8, 5, col2=WOODD)
    for x in (60, 900):
        shape(lay, rect(x, 120, x + 45, 300), WOODD, r, 1.6, 6, 4)


@el('bolt', 320, 920)
def _bolt(lay, r, p):
    poly = [(190, 0), (60, 330), (170, 320), (40, 660), (150, 645), (20, 920), (270, 520), (150, 535), (290, 250), (180, 262), (300, 0)]
    shape(lay, poly, (255, 215, 50), r, 0.4, 6, 6, line=(230, 140, 30), base=200)


@el('mountains', 1080, 620)
def _mountains(lay, r, p):
    far = p.get('col', (120, 140, 190))
    shape(lay, [(0, 620), (0, 300), (180, 120), (330, 280), (520, 60), (720, 300), (880, 160), (1080, 330), (1080, 620)], far, r, 0.8, 9, 5, col2=(90, 110, 160), line=(60, 70, 110))
    shape(lay, [(0, 620), (0, 460), (250, 330), (460, 470), (700, 350), (1080, 480), (1080, 620)], p.get('near', (110, 165, 110)), r, 2.4, 8, 5, line=(50, 90, 60))
    for x, y in [(520, 60), (180, 120), (880, 160)]:
        shape(lay, [(x, y), (x + 55, y + 70), (x + 20, y + 55), (x, y + 80), (x - 25, y + 55), (x - 55, y + 70)], (250, 250, 255), r, 0.3, 6, 4, lw=3)


@el('hill', 1080, 420)
def _hill(lay, r, p):
    pts = [(0, 420), (0, 200)] + [(x, 200 - 150 * np.sin(np.pi * x / 1080) ** 1.5 + 8 * np.sin(x / 40)) for x in np.linspace(0, 1080, 30)] + [(1080, 420)]
    shape(lay, pts, p.get('col', (110, 170, 100)), r, 2.6, 8, 5, col2=(80, 130, 70), line=(50, 90, 50))
    for k in range(14):
        x = 60 + k * 75
        y = 200 - 150 * np.sin(np.pi * x / 1080) ** 1.5 + 30 + (k % 3) * 40
        stroke(lay, [(x - 12, y + 10), (x, y - 12), (x + 10, y + 10)], (60, 120, 60), r, 3, 1, 1)


@el('ground', 1080, 260)
def _ground(lay, r, p):
    shape(lay, rect(0, 40, 1080, 260), p.get('col', (125, 170, 95)), r, 2.7, 9, 5, line=None, base=140, col2=(140, 110, 70))
    stroke(lay, [(x, 40 + 6 * np.sin(x / 30)) for x in np.linspace(0, 1080, 40)], (70, 110, 60), r, 5, 1.5, 2)


@el('floor', 1080, 360)
def _floor(lay, r, p):
    shape(lay, rect(0, 0, 1080, 360), (200, 150, 100), r, 0.05, 10, 5, line=None, base=170, col2=(150, 105, 70))
    for y in range(40, 360, 70):
        stroke(lay, [(0, y), (1080, y + 8)], WOODD, r, 3, 1.5, 1)


@el('wall', 1080, 1300)
def _wall(lay, r, p):
    shape(lay, rect(0, 0, 1080, 1300), p.get('col', (235, 205, 160)), r, 1.2, 12, 5, line=None, base=150, col2=(210, 175, 130))


@el('torch', 90, 240)
def _torch(lay, r, p):
    shape(lay, rect(38, 90, 54, 240), WOODD, r, 1.5, 5, 4, lw=3)
    shape(lay, ell(46, 70, 34, 55, wob=0.2), ORANGE, r, 0.4, 5, 4, line=RED, lw=3)
    shape(lay, ell(46, 80, 16, 26), YELLOW, r, 0.4, 4, 4, line=None)


@el('bandit_flag', 260, 420)
def _bandit_flag(lay, r, p):
    stroke(lay, [(40, 420), (40, 20)], WOODD, r, 9, 1.5, 2)
    shape(lay, [(45, 30), (250, 60), (200, 120), (250, 180), (45, 170)], (60, 60, 70), r, 0.6, 6, 5)
    shape(lay, ell(140, 100, 32, 30), CREAM, r, 0.3, 5, 3, lw=3)
    stroke(lay, [(105, 140), (175, 60)], CREAM, r, 5, 1, 1)


@el('blade', 360, 110)
def _blade(lay, r, p):
    shape(lay, [(0, 50), (60, 20), (280, 30), (300, 60), (60, 75)], (200, 205, 215), r, 0.2, 5, 4)
    shape(lay, rect(290, 38, 360, 62), (120, 60, 40), r, 1.5, 5, 4)


@el('lantern', 150, 240)
def _lantern(lay, r, p):
    stroke(lay, [(75, 0), (75, 40)], DARK, r, 3, 0.5, 1)
    shape(lay, rect(50, 40, 100, 58), (60, 40, 30), r, 0.2, 4, 4, lw=3)
    shape(lay, ell(75, 125, 62, 70), p.get('col', (230, 60, 45)), r, 1.4, 6, 5, line=(150, 30, 30))
    for x in (45, 75, 105):
        stroke(lay, [(x, 62), (x + (x - 75) * 0.4, 125), (x, 188)], (150, 30, 30), r, 3, 0.5, 1)
    shape(lay, rect(50, 190, 100, 206), (60, 40, 30), r, 0.2, 4, 4, lw=3)
    for x in (62, 75, 88):
        stroke(lay, [(x, 206), (x, 238)], YELLOW, r, 3, 0.5, 1)


@el('sky_lantern', 130, 170)
def _sky_lantern(lay, r, p):
    shape(lay, [(25, 20), (105, 20), (118, 150), (12, 150)], (240, 110, 60), r, 1.4, 6, 5, line=(170, 50, 30))
    shape(lay, ell(65, 150, 30, 10), YELLOW, r, 0, 4, 4, line=None)


@el('drum', 320, 320)
def _drum(lay, r, p):
    shape(lay, rect(40, 90, 280, 250), RED, r, 1.3, 6, 5)
    shape(lay, ell(160, 90, 120, 40), CREAM, r, 0.2, 7, 4)
    shape(lay, ell(160, 250, 120, 40, 20, 0, np.pi), RED, r, 1.3, 6, 5)
    for x in (70, 160, 250):
        stroke(lay, [(x, 110), (x, 270)], YELLOW, r, 4, 1, 1)
    stroke(lay, [(210, 10), (170, 80)], WOODD, r, 8, 1, 2)
    shape(lay, ell(212, 10, 14, 12), RED, r, 0.3, 4, 3, lw=3)


@el('gong', 300, 340)
def _gong(lay, r, p):
    stroke(lay, [(30, 20), (270, 20)], WOODD, r, 10, 1, 2)
    for x in (40, 260):
        stroke(lay, [(x, 20), (x, 330)], WOODD, r, 10, 1, 2)
    shape(lay, ell(150, 170, 95, 95), (235, 170, 50), r, 0.6, 6, 5, line=(170, 110, 30))
    outline(lay, ell(150, 170, 40, 40), (190, 120, 30), r, 4)


@el('pinwheel', 260, 260)
def _pinwheel(lay, r, p):
    c = 130
    for k, col in enumerate([RED, YELLOW, BLUE, GREEN]):
        a = k * np.pi / 2
        tri = [(c, c), (c + 120 * np.cos(a), c + 120 * np.sin(a)), (c + 90 * np.cos(a + 0.9), c + 90 * np.sin(a + 0.9))]
        shape(lay, tri, col, r, a, 6, 4, lw=3)
    shape(lay, ell(c, c, 12, 12), CREAM, r, 0, 3, 3, lw=3)


@el('stick', 40, 360)
def _stick(lay, r, p):
    shape(lay, rect(12, 0, 28, 360), WOOD, r, 1.5, 5, 4, lw=3)


@el('shoes', 300, 150)
def _shoes(lay, r, p):
    for x0, col in [(20, RED), (160, (220, 90, 110))]:
        shape(lay, [(x0, 110), (x0 + 10, 60), (x0 + 60, 50), (x0 + 120, 80), (x0 + 125, 120), (x0, 125)], col, r, 0.4, 6, 4)
        stroke(lay, [(x0 + 30, 60), (x0 + 55, 90), (x0 + 80, 62)], YELLOW, r, 3, 1, 1)


@el('scroll', 460, 220)
def _scroll(lay, r, p):
    shape(lay, rect(60, 60, 400, 160), (240, 220, 170), r, 0.1, 8, 4, col2=(200, 170, 120))
    for x in (60, 400):
        shape(lay, ell(x, 110, 34, 60), (170, 110, 60), r, 1.6, 5, 4)
    stroke(lay, [(230, 50), (230, 170)], RED, r, 9, 1, 2)
    shape(lay, ell(230, 110, 36, 36), RED, r, 0.4, 5, 4, lw=3)
    stroke(lay, [(215, 100), (245, 100), (230, 125)], CREAM, r, 3, 0.5, 1)


@el('bread', 360, 240)
def _bread(lay, r, p):
    shape(lay, ell(180, 130, 160, 90, wob=0.06, seed=4), (225, 165, 80), r, 0.5, 7, 5, col2=(190, 120, 55))
    shape(lay, ell(180, 125, 110, 55, wob=0.08, seed=7), (240, 195, 110), r, 1.9, 7, 4, line=None, base=90)
    rs = np.random.default_rng(3)
    for _ in range(18):
        x, y = rs.uniform(90, 270), rs.uniform(90, 170)
        stroke(lay, [(x, y), (x + 8, y + 3)], CREAM, r, 4, 0.5, 1)
    if p.get('bite'):
        tmp = Image.new('L', lay.size, 255)
        d = ImageDraw.Draw(tmp)
        for k in range(3):
            d.ellipse([290 + k * 12, 50 + k * 45, 370 + k * 12, 120 + k * 45], fill=0)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel('A')), np.asarray(tmp))))


@el('cloth', 560, 200)
def _cloth(lay, r, p):
    shape(lay, [(20, 120), (120, 40), (440, 30), (540, 110), (470, 180), (90, 185)], (230, 120, 110), r, 0.5, 8, 4, col2=(250, 240, 220))
    for k in range(5):
        stroke(lay, [(100 + k * 80, 50), (80 + k * 80, 180)], (250, 240, 220), r, 5, 1, 1)


@el('bowl', 340, 260)
def _bowl(lay, r, p):
    if p.get('rice', True):
        shape(lay, ell(170, 110, 130, 60, 30, np.pi, 2 * np.pi) + [(300, 115), (40, 115)], (252, 250, 245), r, 0.3, 8, 3, line=(170, 170, 170), base=230)
        rs = np.random.default_rng(1)
        for _ in range(26):
            x, y = rs.uniform(70, 270), rs.uniform(70, 110)
            outline(lay, ell(x, y, 7, 4), (200, 200, 195), r, 2)
    shape(lay, [(30, 110), (310, 110), (270, 210), (70, 210)], (80, 130, 200), r, 0.4, 7, 5)
    stroke(lay, [(60, 150), (280, 150)], (240, 240, 250), r, 5, 1, 1)
    shape(lay, rect(120, 210, 220, 240), (60, 100, 170), r, 0.3, 5, 4, lw=3)
    if p.get('chopsticks', True):
        stroke(lay, [(40, 40), (320, 140)], (170, 110, 60), r, 7, 1, 2)
        stroke(lay, [(60, 20), (330, 125)], (170, 110, 60), r, 7, 1, 2)


@el('pot', 520, 520)
def _pot(lay, r, p):
    shape(lay, rect(60, 300, 460, 520), (170, 100, 70), r, 0.2, 9, 5, col2=(130, 70, 50))
    shape(lay, rect(200, 400, 320, 520), (60, 40, 35), r, 1.5, 6, 4)
    shape(lay, ell(260, 160, 190, 50), (80, 80, 90), r, 0.3, 7, 5)
    shape(lay, [(70, 165), (450, 165), (410, 300), (110, 300)], (70, 70, 80), r, 1.2, 7, 5, col2=(40, 40, 50))
    shape(lay, ell(260, 150, 160, 36), (130, 130, 140), r, 0.2, 7, 4)
    shape(lay, ell(260, 110, 30, 18), (100, 100, 110), r, 0.2, 5, 4, lw=3)


@el('bridge', 1080, 520)
def _bridge(lay, r, p):
    sag = lambda x, y0, dep: y0 + dep * np.sin(np.pi * x / 1080)
    for side, y0 in [(0, 120), (1, 150)]:
        stroke(lay, [(x, sag(x, y0, 150)) for x in np.linspace(0, 1080, 40)], (130, 90, 50), r, 6, 1, 2)
    xs = np.linspace(10, 1070, 26)
    for k, x in enumerate(xs):
        y = sag(x, 300, 170)
        shape(lay, [(x - 18, y - 10), (x + 18, y - 12), (x + 20, y + 22), (x - 16, y + 24)], (185 if k % 2 else 165, 125, 70), r, 1.6, 5, 4, lw=3)
        stroke(lay, [(x, sag(x, 120, 150)), (x, y - 10)], (130, 90, 50), r, 3, 0.5, 1)
    for x in (10, 1070):
        shape(lay, rect(x - 25, 60, x + 25, 330), WOODD, r, 1.5, 6, 5)
    if p.get('lanterns'):
        for x in np.linspace(140, 940, 5):
            y = sag(x, 120, 150)
            stroke(lay, [(x, y), (x, y + 30)], DARK, r, 2, 0.3, 1)
            shape(lay, ell(x, y + 58, 24, 30), (235, 70, 50), r, 1.3, 5, 4, line=(150, 30, 30), lw=3)
    if p.get('burning'):
        for x in np.linspace(60, 1020, 12):
            y = sag(x, 300, 170)
            shape(lay, ell(x, y - 40, 36, 60, wob=0.3, seed=int(x)), ORANGE, r, 0.3, 5, 4, line=RED, lw=3, base=170)


@el('cliff_l', 420, 1000)
def _cliff_l(lay, r, p):
    pts = [(0, 0), (260, 0), (300, 120), (340, 180), (330, 320), (380, 420), (300, 600), (330, 760), (240, 1000), (0, 1000)]
    shape(lay, pts, p.get('col', (150, 120, 95)), r, 1.8, 8, 5, col2=(110, 85, 70))
    shape(lay, [(0, 0), (270, 0), (300, 40), (0, 50)], (110, 165, 100), r, 2.8, 7, 4)


@el('cliff_r', 420, 1000)
def _cliff_r(lay, r, p):
    pts = [(420, 0), (160, 0), (120, 110), (60, 200), (100, 340), (40, 460), (120, 620), (80, 780), (180, 1000), (420, 1000)]
    shape(lay, pts, p.get('col', (150, 120, 95)), r, 1.0, 8, 5, col2=(110, 85, 70))
    shape(lay, [(420, 0), (150, 0), (120, 40), (420, 50)], (110, 165, 100), r, 2.8, 7, 4)


@el('abyss', 700, 700)
def _abyss(lay, r, p):
    w, h = lay.size
    ys = np.linspace(0, 1, h)[:, None]
    xs = np.linspace(-1, 1, w)[None, :]
    side = np.clip((1 - np.abs(xs)) / 0.25, 0, 1)
    a = np.clip(ys / 0.35, 0, 1) * side * 235
    g = np.zeros((h, w, 4), np.float32)
    for ch, (c0, c1) in enumerate(((70, 18), (80, 20), (120, 40))):
        g[..., ch] = c0 + (c1 - c0) * ys
    g[..., 3] = a
    lay.alpha_composite(Image.fromarray(g.astype(np.uint8), 'RGBA'))
    t2 = Image.new('RGBA', lay.size)
    hatch(t2, rect(0, 80, w, h), (30, 30, 60), r, 12, 0.9, 4, amin=40, amax=90)
    t2.putalpha(Image.fromarray(np.minimum(np.asarray(t2.getchannel('A')), a.astype(np.uint8))))
    lay.alpha_composite(t2)
    for y in (260, 420):
        stroke(lay, [(x, y + 18 * np.sin(x / 55)) for x in np.linspace(90, w - 90, 20)], (170, 180, 210), r, 6, 3, 1)


@el('eyes', 170, 80)
def _eyes(lay, r, p):
    col = p.get('col', (250, 210, 60))
    for x in (40, 130):
        shape(lay, [(x - 34, 40), (x, 18), (x + 34, 40), (x, 60)], col, r, 0.2, 4, 4, line=(200, 60, 40), lw=3, base=230)
        shape(lay, ell(x, 40, 6, 14), DARK, r, 0, 3, 3, line=None, base=255)


@el('monster', 760, 760)
def _monster(lay, r, p):
    body = [(80, 760), (60, 480), (120, 300), (170, 160), (220, 230), (300, 120), (380, 60), (460, 120), (540, 230), (590, 160), (640, 300), (700, 480), (680, 760)]
    shape(lay, body, (45, 40, 70), r, 0.9, 6, 5, line=(20, 20, 30), base=200, col2=(80, 50, 90))
    for x, y in [(290, 330), (470, 330)]:
        shape(lay, [(x - 55, y), (x, y - 30), (x + 55, y), (x, y + 26)], (250, 210, 60), r, 0.2, 4, 4, line=(220, 60, 40), base=240)
        shape(lay, ell(x, y, 8, 20), DARK, r, 0, 3, 3, line=None, base=255)
    stroke(lay, [(270, 470), (320, 500), (380, 470), (440, 500), (490, 470)], (240, 240, 240), r, 6, 1.5, 2)


@el('shadow', 360, 520)
def _shadow(lay, r, p):
    shape(lay, [(40, 520), (60, 250), (110, 120), (180, 60), (250, 120), (300, 250), (320, 520)], (50, 45, 75), r, 0.9, 6, 5, line=None, base=170)
    for x in (140, 220):
        shape(lay, ell(x, 190, 18, 10), (250, 210, 60), r, 0, 3, 3, line=None, base=250)


@el('peak', 1080, 520)
def _peak(lay, r, p):
    pts = [(0, 520), (0, 380), (300, 240), (460, 110), (620, 110), (780, 250), (1080, 360), (1080, 520)]
    shape(lay, pts, p.get('col', (140, 120, 100)), r, 1.4, 8, 5, col2=(100, 90, 80))
    shape(lay, [(430, 130), (650, 130), (620, 110), (460, 110)], (110, 165, 100), r, 2.8, 6, 4)


@el('talisman', 220, 480)
def _talisman(lay, r, p):
    shape(lay, rect(30, 20, 190, 460), (248, 215, 80), r, 0.1, 7, 4, line=(190, 140, 40))
    stroke(lay, [(110, 60), (70, 110), (150, 150), (60, 200), (160, 250), (80, 300), (140, 350), (100, 420)], RED, r, 7, 1.2, 2)
    outline(lay, ell(110, 110, 40, 40), RED, r, 4)
    if p.get('burnt'):
        tmp = Image.new('L', lay.size, 255)
        ImageDraw.Draw(tmp).polygon([(0, 480), (0, 260), (60, 300), (100, 240), (150, 310), (220, 250), (220, 480)], fill=0)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel('A')), np.asarray(tmp))))
        stroke(lay, [(30, 262), (60, 302), (100, 242), (150, 312), (190, 262)], (60, 40, 30), r, 8, 1.5, 2)


@el('altar', 640, 460)
def _altar(lay, r, p):
    broken = p.get('broken')
    top = [(20, 140), (620, 140), (600, 190), (40, 190)] if not broken else [(20, 180), (280, 140), (330, 200), (40, 230)]
    shape(lay, top, (170, 50, 40), r, 0.1, 7, 5)
    if broken:
        shape(lay, [(360, 250), (620, 190), (600, 250), (380, 300)], (170, 50, 40), r, 0.1, 7, 5)
        for pts in [[(80, 460), (120, 300), (200, 250)], [(560, 460), (520, 330), (430, 300)]]:
            stroke(lay, pts, DARK, r, 5, 2, 1)
        shape(lay, [(60, 460), (80, 250), (200, 260), (220, 460)], (140, 40, 35), r, 1.7, 7, 5)
        shape(lay, [(420, 460), (440, 320), (580, 280), (590, 460)], (140, 40, 35), r, 1.7, 7, 5)
        for x, y in [(300, 420), (360, 440), (250, 440)]:
            shape(lay, [(x, y), (x + 30, y - 20), (x + 45, y + 10), (x + 10, y + 20)], (140, 40, 35), r, 1, 5, 4, lw=3)
        return
    shape(lay, rect(60, 190, 580, 460), (140, 40, 35), r, 1.7, 7, 5, col2=(90, 25, 25))
    shape(lay, rect(160, 250, 480, 400), (230, 180, 60), r, 0.4, 7, 4, lw=4)
    outline(lay, ell(320, 325, 60, 50), RED, r, 4)
    shape(lay, [(250, 140), (390, 140), (370, 60), (270, 60)], (120, 120, 110), r, 0.4, 6, 4)
    for x in (295, 320, 345):
        stroke(lay, [(x, 60), (x, 0)], (200, 90, 60), r, 4, 0.5, 1)


@el('footprint', 420, 520)
def _footprint(lay, r, p):
    shape(lay, ell(210, 320, 140, 180, wob=0.1, seed=2), (55, 45, 70), r, 0.8, 7, 5, line=None, base=190)
    for k, a in enumerate(np.linspace(-2.4, -0.7, 4)):
        x, y = 210 + 170 * np.cos(a), 300 + 200 * np.sin(a)
        shape(lay, [(x - 25, y + 20), (x, y - 50), (x + 25, y + 20)], (55, 45, 70), r, 0.8, 5, 4, line=None, base=200)


@el('gate', 760, 860)
def _gate(lay, r, p):
    shape(lay, [(0, 170), (760, 170), (680, 60), (80, 60)], (60, 70, 90), r, 1.2, 7, 5)
    shape(lay, rect(60, 170, 700, 860), (180, 60, 45), r, 1.6, 8, 5, col2=(130, 40, 35))
    if p.get('open'):
        shape(lay, rect(160, 260, 600, 860), (40, 35, 50), r, 0.8, 6, 5)
    else:
        for x0 in (160, 380):
            shape(lay, rect(x0, 260, x0 + 220, 860), (200, 120, 60), r, 0.2, 8, 5)
            for y in range(320, 860, 90):
                for x in range(x0 + 40, x0 + 220, 70):
                    shape(lay, ell(x, y, 10, 10), YELLOW, r, 0, 3, 3, lw=2)
        for x in (355, 405):
            outline(lay, ell(x, 560, 22, 22), (230, 170, 50), r, 5)


@el('bed', 880, 380)
def _bed(lay, r, p):
    shape(lay, rect(40, 180, 840, 280), (215, 180, 100), r, 0.1, 6, 5, col2=(170, 130, 60))
    for x in range(60, 840, 40):
        stroke(lay, [(x, 185), (x + 10, 275)], (170, 130, 60), r, 3, 0.8, 1)
    for x in (60, 790):
        shape(lay, rect(x, 280, x + 30, 380), WOODD, r, 1.6, 5, 4)
    shape(lay, [(250, 190), (820, 180), (840, 250), (240, 260), (210, 210)], (90, 130, 190), r, 0.6, 8, 5, col2=(240, 230, 210))
    for x in range(300, 820, 90):
        stroke(lay, [(x, 185), (x + 20, 255)], (240, 230, 210), r, 6, 1, 1)
    shape(lay, ell(150, 175, 100, 45), CREAM, r, 0.3, 7, 4)


@el('bandage', 320, 220)
def _bandage(lay, r, p):
    shape(lay, [(20, 80), (300, 40), (310, 130), (30, 170)], (250, 248, 240), r, 0.9, 8, 4, line=(160, 160, 170), base=230)
    for k in range(5):
        stroke(lay, [(60 + k * 50, 70 - k * 6), (70 + k * 50, 160 - k * 6)], (200, 200, 205), r, 3, 0.8, 1)
    shape(lay, ell(165, 105, 55, 35, wob=0.3, seed=9), (200, 35, 40), r, 0.6, 5, 5, line=None, base=170)


@el('candle', 140, 340)
def _candle(lay, r, p):
    shape(lay, rect(40, 120, 100, 300), (250, 240, 220), r, 1.5, 7, 4, col2=(230, 200, 170))
    shape(lay, ell(70, 310, 65, 25), (200, 160, 80), r, 0.2, 6, 4)
    stroke(lay, [(70, 120), (70, 100)], DARK, r, 3, 0.3, 1)


@el('crane', 340, 240)
def _crane(lay, r, p):
    shape(lay, [(20, 150), (170, 120), (320, 60), (220, 150), (170, 200)], (245, 245, 250), r, 0.4, 7, 4, line=(90, 110, 160), base=220)
    shape(lay, [(170, 120), (120, 20), (230, 110)], (230, 235, 245), r, 1.2, 7, 4, line=(90, 110, 160), base=220)
    shape(lay, [(170, 130), (240, 10), (220, 130)], (215, 225, 245), r, 1.8, 7, 4, line=(90, 110, 160), base=220)
    stroke(lay, [(320, 60), (330, 40), (315, 45)], (90, 110, 160), r, 4, 0.5, 1)


@el('window', 460, 520)
def _window(lay, r, p):
    shape(lay, rect(20, 20, 440, 500), WOODD, r, 1.6, 7, 5)
    if p.get('shut'):
        for x0 in (40, 230):
            shape(lay, rect(x0, 40, x0 + 190, 480), (170, 110, 70), r, 0.1, 7, 4)
            for y in range(70, 470, 40):
                stroke(lay, [(x0 + 10, y), (x0 + 180, y + 10)], WOODD, r, 3, 0.8, 1)
    else:
        shape(lay, rect(40, 40, 420, 480), p.get('glass', (40, 55, 110)), r, 0.8, 8, 4)
        stroke(lay, [(230, 40), (230, 480)], WOODD, r, 8, 1, 2)
        stroke(lay, [(40, 260), (420, 260)], WOODD, r, 8, 1, 2)


@el('whetstone', 460, 170)
def _whetstone(lay, r, p):
    shape(lay, [(20, 80), (440, 70), (450, 150), (30, 160)], (120, 125, 140), r, 0.2, 7, 5, col2=(90, 95, 110))
    shape(lay, [(40, 40), (420, 30), (440, 70), (20, 80)], (160, 165, 180), r, 0.2, 7, 4)


@el('book', 820, 540)
def _book(lay, r, p):
    torn = p.get('torn')
    shape(lay, [(20, 80), (410, 40), (410, 520), (20, 500)], (180, 80, 50), r, 0.5, 8, 5)
    shape(lay, [(410, 40), (800, 80), (800, 500), (410, 520)], (180, 80, 50), r, 0.5, 8, 5)
    shape(lay, [(45, 95), (400, 60), (400, 495), (45, 480)], (245, 230, 190), r, 0.1, 9, 4, col2=(220, 195, 150))
    shape(lay, [(420, 60), (775, 95), (775, 480), (420, 495)], (245, 230, 190), r, 0.1, 9, 4, col2=(220, 195, 150))
    if torn:
        for pts in [[(60, 470), (110, 420), (90, 380), (150, 350)], [(700, 100), (740, 160), (720, 200)]]:
            stroke(lay, pts, (120, 80, 50), r, 5, 1.5, 1)
        shape(lay, [(600, 400), (780, 380), (780, 480), (620, 490)], (150, 110, 70), r, 1.1, 6, 4, line=None, base=90)
    if p.get('tricks'):
        for k, (x, y) in enumerate([(230, 170), (230, 350), (600, 250)]):
            outline(lay, ell(x, y, 90, 70), (170, 120, 80), r, 3)
        poly = [(240, 120), (205, 175), (235, 172), (210, 225), (262, 158), (232, 160), (258, 120)]
        shape(lay, poly, YELLOW, r, 0.4, 4, 4, line=ORANGE, lw=3)
        stroke(lay, [(180, 350), (230, 320), (280, 360)], RED, r, 4, 1, 1)
        stroke(lay, [(600, 180), (600, 330)], (120, 120, 130), r, 2, 0.3, 1)
        shape(lay, [(590, 330), (610, 330), (605, 400), (600, 420), (595, 400)], WOOD, r, 1.5, 4, 3, lw=3)
    else:
        for side in (0, 1):
            for y in range(120, 460, 42):
                x0 = 80 + side * 380
                stroke(lay, [(x0, y), (x0 + 280, y + 4)], (170, 140, 110), r, 3, 1.2, 1)


@el('page', 200, 240)
def _page(lay, r, p):
    shape(lay, [(20, 20), (180, 30), (170, 220), (30, 210)], (245, 230, 190), r, 0.1, 8, 4, line=(170, 140, 100), col2=(220, 195, 150))
    for y in range(60, 200, 30):
        stroke(lay, [(40, y), (150, y + 5)], (170, 140, 110), r, 3, 1, 1)


@el('crystals', 400, 260)
def _crystals(lay, r, p):
    for k, (x, h, w) in enumerate([(90, 150, 60), (170, 210, 70), (250, 170, 60), (320, 120, 50), (140, 110, 50), (230, 100, 50)]):
        base = 240
        shape(lay, [(x - w / 2, base), (x - w / 2, base - h * 0.7), (x, base - h), (x + w / 2, base - h * 0.7), (x + w / 2, base)],
              (235, 240, 250) if k % 2 else (205, 220, 240), r, 1.2, 6, 4, line=(110, 130, 170), base=220)


@el('bundle', 440, 460)
def _bundle(lay, r, p):
    stroke(lay, [(20, 440), (420, 40)], WOODD, r, 12, 1.5, 2)
    shape(lay, ell(330, 170, 110, 100, wob=0.08, seed=5), (70, 120, 170), r, 0.6, 7, 5, col2=(240, 240, 250))
    shape(lay, [(330, 70), (300, 20), (360, 30), (390, 10), (380, 70)], (70, 120, 170), r, 1.2, 6, 4)
    for k in range(6):
        outline(lay, ell(290 + (k % 3) * 40, 150 + (k // 3) * 50, 10, 10), (240, 240, 250), r, 3)


@el('path', 1080, 900)
def _path(lay, r, p):
    left = [(420 + 200 * np.sin(y / 180) * (y / 900), y) for y in np.linspace(0, 900, 30)]
    pts = [(x - 40 - 200 * (y / 900), y) for x, y in left] + [(x + 40 + 200 * (y / 900), y) for x, y in left[::-1]]
    shape(lay, pts, (215, 185, 130), r, 0.4, 9, 4, line=(160, 120, 80), col2=(180, 150, 100))


@el('cart', 520, 360)
def _cart(lay, r, p):
    shape(lay, [(20, 140), (460, 140), (440, 250), (40, 250)], WOOD, r, 0.1, 7, 5, col2=WOODD)
    for x in (130, 360):
        shape(lay, ell(x, 280, 70, 70), WOODD, r, 1, 7, 5)
        for a in np.linspace(0, np.pi, 4, endpoint=False):
            stroke(lay, [(x + 60 * np.cos(a), 280 + 60 * np.sin(a)), (x - 60 * np.cos(a), 280 - 60 * np.sin(a))], (90, 60, 40), r, 3, 0.5, 1)
    stroke(lay, [(460, 160), (520, 120)], WOODD, r, 9, 1, 2)
    shape(lay, ell(160, 110, 90, 60, wob=0.1, seed=3), (220, 120, 90), r, 0.5, 7, 4)
    shape(lay, ell(320, 100, 100, 70, wob=0.1, seed=6), (90, 150, 110), r, 1.3, 7, 4)


@el('basket', 240, 230)
def _basket(lay, r, p):
    shape(lay, [(20, 80), (220, 80), (190, 220), (50, 220)], (200, 150, 80), r, 0.1, 6, 4, col2=(160, 110, 50))
    for x in range(40, 220, 30):
        stroke(lay, [(x, 85), (x + 5, 215)], (150, 100, 50), r, 3, 0.8, 1)
    stroke(lay, [(40, 80), (120, 0), (200, 80)], (150, 100, 50), r, 6, 1, 2)
    for k, c in enumerate([RED, ORANGE, GREEN]):
        shape(lay, ell(80 + k * 45, 70, 26, 24), c, r, 0.5, 5, 4, lw=3)


@el('stele', 420, 820)
def _stele(lay, r, p):
    shape(lay, rect(40, 700, 380, 820), (150, 150, 155), r, 0.2, 8, 5)
    shape(lay, [(80, 700), (80, 140), (140, 60), (280, 60), (340, 140), (340, 700)], (175, 175, 180), r, 1.5, 9, 5, col2=(140, 140, 150))
    carve = (105, 105, 115)
    outline(lay, [(210, 120), (232, 170), (232, 480), (188, 480), (188, 170)], carve, r, 5)
    outline(lay, rect(140, 480, 280, 510), carve, r, 5)
    outline(lay, rect(196, 510, 224, 620), carve, r, 5)
    outline(lay, ell(210, 640, 22, 18), carve, r, 5)
    for y0 in (200, 300, 400):
        stroke(lay, [(300, y0), (304, y0 + 40)], (150, 150, 158), r, 3, 1, 1)
    stroke(lay, [(95, 300), (120, 340), (110, 380)], (140, 140, 150), r, 3, 1, 1)


@el('incense', 220, 300)
def _incense(lay, r, p):
    shape(lay, [(20, 170), (200, 170), (170, 280), (50, 280)], (190, 140, 60), r, 0.3, 6, 5)
    shape(lay, ell(110, 170, 90, 22), (160, 110, 50), r, 0.2, 5, 4)
    for x in (80, 110, 140):
        stroke(lay, [(x, 170), (x + (x - 110) * 0.3, 40)], (190, 70, 50), r, 4, 0.5, 1)
        shape(lay, ell(x + (x - 110) * 0.3, 38, 5, 5), ORANGE, r, 0, 2, 2, line=None, base=250)


@el('signpost', 360, 520)
def _signpost(lay, r, p):
    shape(lay, rect(165, 80, 195, 520), WOODD, r, 1.5, 6, 4)
    shape(lay, [(20, 110), (170, 100), (170, 170), (20, 180), (-10, 145)], WOOD, r, 0.1, 6, 4)
    shape(lay, [(190, 200), (340, 210), (370, 245), (340, 280), (190, 270)], WOOD, r, 0.1, 6, 4)


@el('boom', 620, 620)
def _boom(lay, r, p):
    from mvkit.core import star_pts
    shape(lay, star_pts(310, 310, 300, 140, n=12), YELLOW, r, 0.5, 7, 5, line=RED, lw=8, base=220)
    shape(lay, star_pts(310, 310, 170, 80, n=9, rot=0.3), (235, 80, 60), r, 1.2, 6, 5, line=None, base=230)


@el('firewall', 1080, 520)
def _firewall(lay, r, p):
    for k in range(9):
        x = 60 + k * 120
        shape(lay, ell(x, 300, 110, 220, wob=0.35, seed=k), [RED, ORANGE][k % 2], r, 0.4, 6, 5, line=(180, 40, 30), base=190)
    for k in range(8):
        x = 120 + k * 120
        shape(lay, ell(x, 380, 60, 120, wob=0.3, seed=k + 20), YELLOW, r, 0.4, 5, 4, line=None, base=210)


@el('grass', 360, 120)
def _grass(lay, r, p):
    for k in range(12):
        x = 20 + k * 28
        stroke(lay, [(x, 120), (x + 10 * np.sin(k), 30 + 30 * (k % 3))], (60, 140, 70), r, 5, 1, 1)


@el('stars', 1080, 900)
def _stars(lay, r, p):
    rs = np.random.default_rng(p.get('seed', 11))
    for _ in range(p.get('n', 16)):
        x, y, s = rs.uniform(60, 1020), rs.uniform(60, 860), rs.uniform(10, 20)
        stroke(lay, [(x - s, y), (x + s, y)], (250, 215, 90), r, 4, 1, 1)
        stroke(lay, [(x, y - s), (x, y + s)], (250, 215, 90), r, 4, 1, 1)


@el('rock', 360, 220)
def _rock(lay, r, p):
    shape(lay, ell(180, 130, 160, 85, wob=0.15, seed=p.get('seed', 3)), (150, 145, 140), r, 1.1, 8, 5, col2=(110, 105, 100))


@el('frost', 1080, 240)
def _frost(lay, r, p):
    shape(lay, rect(0, 60, 1080, 240), (225, 235, 250), r, 0.2, 10, 4, line=None, base=170, col2=(190, 205, 235))
    for x in range(30, 1080, 70):
        stroke(lay, [(x, 70), (x + 12, 40), (x + 24, 70)], (170, 190, 230), r, 3, 0.8, 1)


@el('chime', 200, 360)
def _chime(lay, r, p):
    stroke(lay, [(100, 0), (100, 60)], DARK, r, 3, 0.5, 1)
    shape(lay, [(60, 60), (140, 60), (160, 150), (40, 150)], (200, 150, 70), r, 0.4, 6, 4)
    stroke(lay, [(100, 150), (100, 260)], DARK, r, 3, 0.5, 1)
    shape(lay, [(70, 260), (130, 260), (120, 350), (80, 350)], (240, 230, 200), r, 0.2, 6, 4, lw=3)


@el('stove', 520, 380)
def _stove(lay, r, p):
    shape(lay, rect(20, 60, 500, 380), (190, 120, 90), r, 0.2, 9, 5, col2=(150, 90, 70))
    for y in range(100, 380, 60):
        stroke(lay, [(20, y), (500, y + 4)], (140, 80, 60), r, 3, 1, 1)
    shape(lay, ell(260, 300, 90, 70, 20, np.pi, 2 * np.pi) + [(350, 380), (170, 380)], (40, 30, 30), r, 1, 6, 4)


@el('knot', 300, 300)
def _knot(lay, r, p):
    for k in range(7):
        a = k * 0.9
        stroke(lay, [(150 + 110 * np.cos(a + q) * (0.6 + 0.4 * np.sin(q * 2)), 150 + 60 * np.sin(a + q)) for q in np.linspace(0, 3, 14)],
               (215, 40, 45), r, 6, 1.5, 1)
