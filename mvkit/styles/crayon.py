"""方案 蜡笔童画: hand-drawn crayon picture book; every scene is a new page that slides in."""
import numpy as np
from PIL import Image, ImageDraw

from mvkit.core import FPS, H, W, char_img, ease, eout, fbm2d, fit_font, font, paste_center, shake, star_pts, text_layer, value_noise2d, window

BLUE, ORANGE, DARK = (40, 110, 200), (235, 120, 40), (40, 40, 45)
PALETTE = [(235, 80, 60), (40, 110, 200), (245, 190, 50), (60, 160, 90), (170, 90, 190)]
MOODS = dict(default=[1, 1, 1], day=[1, 1, 0.97], dawn=[1, 0.95, 0.94], dusk=[1, 0.93, 0.84], night=[0.86, 0.89, 0.98], storm=[0.88, 0.88, 0.91])


def jline(d, pts, color, width, r, jit=3, n=3):
    for _ in range(n):
        q = [(x + r.normal() * jit, y + r.normal() * jit) for x, y in pts]
        d.line(q, fill=tuple(color[:3]) + (int(r.uniform(120, 220)),), width=max(1, int(width * r.uniform(0.6, 1.1))), joint='curve')


def hatch(layer, poly, color, r, spacing=9, angle=0.9, width=4, jit=2):
    m = Image.new('L', layer.size)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    tmp = Image.new('RGBA', layer.size)
    d = ImageDraw.Draw(tmp)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    L = (x1 - x0) + (y1 - y0)
    ca, sa = np.cos(angle), np.sin(angle)
    for k in np.arange(-L, L, spacing):
        cx, cy = (x0 + x1) / 2 + k * -sa, (y0 + y1) / 2 + k * ca
        d.line([(cx - ca * L + r.normal() * jit, cy - sa * L + r.normal() * jit), (cx + ca * L, cy + sa * L)], fill=color + (int(r.uniform(140, 230)),), width=width)
    tmp.putalpha(Image.fromarray(np.minimum(np.asarray(tmp.getchannel('A')), np.asarray(m))))
    layer.alpha_composite(tmp)


def poly_line(d, poly, color, r, width=6):
    jline(d, list(poly) + [poly[0]], color, width, r, 2.5, 2)


def pre(fn, seed=0):
    out = []
    for i in range(3):
        lay = Image.new('RGBA', (W, H))
        fn(lay, np.random.default_rng(seed * 10 + i))
        out.append(lay)
    return out


def wipe(lay, p, grad, soft=0.06):
    if p >= 1:
        return lay
    if p <= 0:
        return None
    a = np.asarray(lay.getchannel('A'), np.float32) * np.clip((p * (1 + soft) - grad) / soft, 0, 1)
    l2 = lay.copy()
    l2.putalpha(Image.fromarray(a.astype(np.uint8)))
    return l2


def fade(lay, a):
    if a >= 1:
        return lay
    l2 = lay.copy()
    l2.putalpha(l2.getchannel('A').point(lambda v: int(v * max(0, a))))
    return l2


A0, A1 = np.array([300., 700.]), np.array([780., 1500.])
AX = (A1 - A0) / np.linalg.norm(A1 - A0)
NX = np.array([-AX[1], AX[0]])


def ap(u, v):
    p = A0 + (A1 - A0) * u + NX * v
    return (float(p[0]), float(p[1]))


CLOAK = [(640, 800), (720, 700), (820, 720), (880, 820), (900, 1000), (930, 1300), (950, 1500), (905, 1470), (880, 1520), (850, 1470),
         (815, 1530), (785, 1470), (750, 1515), (725, 1450), (700, 1480), (690, 1300), (660, 1050), (630, 900)]
HOOD = [(680, 760), (730, 715), (800, 725), (840, 790), (790, 830), (720, 830)]
HOUSES = [(120, 1560, 170, 170, (235, 120, 40)), (320, 1560, 150, 210, (40, 110, 200)), (500, 1560, 180, 160, (200, 60, 60)),
          (710, 1560, 150, 200, (60, 150, 90)), (890, 1560, 130, 150, (160, 90, 180))]
PC = (540, 1080)
FC = (520, 1500)


class Style:
    name = '蜡笔童画'

    def __init__(self, P):
        self.P = P
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.XN, self.YN = xx / W, yy / H
        self.paper = np.full((H, W, 3), 250, np.float32) * (0.95 + 0.05 * fbm2d(H, W, 200, 5, 1)[..., None])
        self.paper[..., 2] *= 0.96
        self.grains = [np.clip((value_noise2d(H, W, 1.6, 50 + i) - 0.22) * 2.2, 0, 1) for i in range(3)]
        ax = (A1 - A0)
        self.proj = ((xx - A0[0]) * AX[0] + (yy - A0[1]) * AX[1]) / np.linalg.norm(ax)
        self.cproj = (yy - 700) / 830
        self.BORDER = pre(self._border, 1)
        self.GROUND = pre(self._ground, 31)
        self.MOON = pre(self._moon_small, 2)
        self.SUN = pre(self._sun, 4)
        self.STARS = pre(self._stars, 5)
        self.SWORD = pre(self._sword, 6)
        self.CLOAKL = pre(self._cloak, 7)
        self.STORM = pre(self._storm, 8)
        self.MOONP = pre(self._moonpage, 3)
        self.HOUSEL = [pre(lambda lay, r, h=h: self._house(lay, r, h), 20 + k) for k, h in enumerate(HOUSES)]
        self.WING = pre(self._winglow, 30)
        self.POUCH = pre(self._pouch, 40)
        self.CLOUDT = pre(self._cloudtop, 50)
        self.BOLT = pre(self._bolt, 51)
        self.HONG = self._boom(np.random.default_rng(52))
        self.tones = [self.tone_of(ts[0]) for _, ts, _ in P.lyr]
        self.impacts = [(tc, tn) for (_, ts, _), tn in zip(P.lyr, self.tones) if tn in ('final', 'tragic') for tc in ts]
        size = fit_font('zhimang', P.title, 940, 230)
        self.title = text_layer(P.title, font('zhimang', size), (35, 35, 40, 255), spacing=10)
        size = fit_font('kai', P.subtitle, 900, 56) if P.subtitle else 48
        self.sub = text_layer(P.subtitle, font('kai', size), (230, 110, 40, 255), spacing=6) if P.subtitle else None
        self.page_starts = [s['start'] for s in P.scenes]

    # ------------------------------------------------------------ static drawings
    def _border(self, lay, r):
        d = ImageDraw.Draw(lay)
        for i in range(14):
            side = i % 4
            c = [BLUE, ORANGE][i % 2]
            if side == 0:
                pts = [(r.uniform(-50, 200), r.uniform(20, 90)), (r.uniform(880, 1130), r.uniform(20, 90))]
            elif side == 1:
                pts = [(r.uniform(-50, 200), r.uniform(H - 90, H - 20)), (r.uniform(880, 1130), r.uniform(H - 90, H - 20))]
            elif side == 2:
                pts = [(r.uniform(20, 80), r.uniform(-50, 300)), (r.uniform(20, 80), r.uniform(1600, 1970))]
            else:
                pts = [(r.uniform(W - 80, W - 20), r.uniform(-50, 300)), (r.uniform(W - 80, W - 20), r.uniform(1600, 1970))]
            jline(d, pts, c, 5, r, 4, 1)

    def _ground(self, lay, r):
        g = [(60, 1560), (1020, 1560), (1020, 1640), (60, 1640)]
        hatch(lay, g, (120, 160, 90), r, 12, 2.8, 4)
        hatch(lay, g, (130, 95, 60), r, 12, 0.2, 3)

    def _moon_small(self, lay, r):
        moon = [(215 + 85 * np.cos(k), 560 + 85 * np.sin(k)) for k in np.linspace(0, 2 * np.pi, 30)]
        hatch(lay, moon, (245, 200, 70), r, 9, 0.7, 4)
        poly_line(ImageDraw.Draw(lay), moon, (220, 150, 40), r, 4)

    def _sun(self, lay, r):
        d = ImageDraw.Draw(lay)
        sun = [(215 + 90 * np.cos(k), 560 + 90 * np.sin(k)) for k in np.linspace(0, 2 * np.pi, 30)]
        hatch(lay, sun, (240, 90, 50), r, 8, 0.7, 5)
        poly_line(d, sun, (220, 70, 40), r, 4)
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            jline(d, [(215 + np.cos(a) * 115, 560 + np.sin(a) * 115), (215 + np.cos(a) * 160, 560 + np.sin(a) * 160)], (240, 150, 40), 6, r, 2, 1)

    def _stars(self, lay, r):
        d = ImageDraw.Draw(lay)
        for sx, sy in [(420, 520), (560, 610), (160, 800), (950, 470), (880, 1100), (120, 1150), (760, 300)]:
            jline(d, [(sx - 14, sy), (sx + 14, sy)], (240, 170, 50), 4, r, 1.5, 1)
            jline(d, [(sx, sy - 14), (sx, sy + 14)], (240, 170, 50), 4, r, 1.5, 1)

    def _sword(self, lay, r):
        grip = [ap(0, -20), ap(0, 20), ap(0.22, 20), ap(0.22, -20)]
        guard = [ap(0.2, -95), ap(0.2, 95), ap(0.25, 95), ap(0.25, -95)]
        blade = [ap(0.25, -32), ap(0.25, 32), ap(0.93, 30), ap(1.0, 0), ap(0.93, -30)]
        for poly, col in [(blade, (130, 75, 45)), (grip, (95, 55, 35)), (guard, (40, 40, 45))]:
            hatch(lay, poly, col, r, 7, 2.6, 5)
            poly_line(ImageDraw.Draw(lay), poly, (25, 20, 20), r, 6)

    def _cloak(self, lay, r):
        hatch(lay, CLOAK, (90, 130, 180), r, 8, 1.4, 4)
        hatch(lay, CLOAK, (120, 120, 130), r, 17, 1.2, 3)
        d = ImageDraw.Draw(lay)
        poly_line(d, CLOAK, (30, 30, 35), r, 5)
        hatch(lay, HOOD, (70, 90, 120), r, 7, 0.5, 4)
        poly_line(d, HOOD, (30, 30, 35), r, 4)
        for k in range(6):
            x = 700 + k * 38
            jline(d, [(x, 880 + k * 10), (x + 10, 1250), (x + 18, 1440)], (60, 80, 110), 3, r, 3, 1)

    def _storm(self, lay, r):
        for cx, cy, s in [(200, 600, 1.0), (520, 540, 1.25), (850, 610, 1.05)]:
            poly = [(cx + np.cos(a) * s * (120 + 30 * np.sin(a * 5 + cx)) * 1.5, cy + np.sin(a) * s * (120 + 30 * np.sin(a * 5 + cx)) * 0.7) for a in np.linspace(0, 2 * np.pi, 26)]
            hatch(lay, poly, (80, 85, 110), r, 8, 0.8, 5)
            hatch(lay, poly, (50, 60, 90), r, 16, 2.2, 3)
            poly_line(ImageDraw.Draw(lay), poly, (30, 30, 40), r, 5)

    def _moonpage(self, lay, r):
        d = ImageDraw.Draw(lay)
        cx, cy = 540, 640
        outer = [(cx + 260 * np.cos(a), cy + 260 * np.sin(a)) for a in np.linspace(0.5 * np.pi, 1.5 * np.pi, 30)]
        inner = [(cx + 90 + 200 * np.cos(a), cy - 10 + 230 * np.sin(a)) for a in np.linspace(1.35 * np.pi, 0.65 * np.pi, 30)]
        poly = outer + inner
        hatch(lay, poly, (245, 200, 70), r, 8, 0.7, 5)
        poly_line(d, poly, (220, 150, 40), r, 5)
        jline(d, [(cx - 170 + 30 * np.cos(a), cy - 40 + 14 * np.sin(a)) for a in np.linspace(0.1, np.pi - 0.1, 10)], (60, 50, 40), 5, r, 1, 2)
        jline(d, [(cx - 150 + 25 * np.cos(a), cy + 80 + 12 * np.sin(a)) for a in np.linspace(0.3, np.pi - 0.3, 10)], (200, 80, 60), 4, r, 1, 2)

    def _house(self, lay, r, h):
        x, y, w_, h_, roof = h
        d = ImageDraw.Draw(lay)
        wall = [(x, y), (x + w_, y), (x + w_, y - h_), (x, y - h_)]
        rf = [(x - 25, y - h_), (x + w_ + 25, y - h_), (x + w_ / 2, y - h_ - 110)]
        hatch(lay, wall, (240, 225, 180), r, 10, 0.4, 4)
        poly_line(d, wall, (40, 40, 45), r, 5)
        hatch(lay, rf, roof, r, 8, 1.1, 5)
        poly_line(d, rf, (40, 40, 45), r, 5)
        dr = [(x + w_ * 0.38, y), (x + w_ * 0.62, y), (x + w_ * 0.62, y - 70), (x + w_ * 0.38, y - 70)]
        hatch(lay, dr, (120, 80, 50), r, 7, 2.5, 4)

    def _winglow(self, lay, r):
        d = ImageDraw.Draw(lay)
        for x, y, w_, h_, _ in HOUSES:
            wx, wy = x + w_ * 0.12, y - h_ * 0.75
            poly = [(wx, wy), (wx + 36, wy), (wx + 36, wy + 36), (wx, wy + 36)]
            hatch(lay, poly, (255, 200, 60), r, 6, 0.3, 5)
            poly_line(d, poly, (60, 50, 40), r, 3)

    def _pouch(self, lay, r):
        d = ImageDraw.Draw(lay)
        cx, cy = PC
        body = [(cx + 70, cy - 150)] + [(cx + 230 * np.cos(a), cy + 60 + 210 * np.sin(a)) for a in np.linspace(-0.3 * np.pi, 1.3 * np.pi, 30)] + [(cx - 70, cy - 150)]
        hatch(lay, body, (170, 115, 60), r, 8, 0.9, 5)
        hatch(lay, body, (120, 80, 45), r, 16, 2.3, 3)
        poly_line(d, body, (40, 30, 25), r, 6)
        top = [(cx - 90, cy - 150), (cx - 120, cy - 230), (cx - 30, cy - 190), (cx, cy - 250), (cx + 40, cy - 190), (cx + 120, cy - 230), (cx + 90, cy - 150)]
        hatch(lay, top, (190, 140, 80), r, 8, 1.6, 4)
        poly_line(d, top, (40, 30, 25), r, 5)
        jline(d, [(cx - 95, cy - 150), (cx + 95, cy - 150)], (200, 50, 40), 9, r, 2, 3)

    def _cloudtop(self, lay, r):
        for cx, cy, s in [(180, 330, 1.0), (520, 270, 1.3), (880, 340, 1.0)]:
            poly = [(cx + np.cos(a) * s * (120 + 30 * np.sin(a * 5 + cx)) * 1.5, cy + np.sin(a) * s * (120 + 30 * np.sin(a * 5 + cx)) * 0.7) for a in np.linspace(0, 2 * np.pi, 26)]
            hatch(lay, poly, (70, 75, 100), r, 7, 0.8, 5)
            poly_line(ImageDraw.Draw(lay), poly, (30, 30, 40), r, 5)

    def _bolt(self, lay, r):
        poly = [(560, 400), (440, 720), (560, 710), (420, 1080), (545, 1065), (400, 1420), (640, 960), (510, 975), (660, 640), (540, 650), (650, 400)]
        hatch(lay, poly, (255, 215, 50), r, 6, 0.4, 6)
        poly_line(ImageDraw.Draw(lay), poly, (230, 140, 30), r, 6)

    # ------------------------------------------------------------ dynamic pieces
    def tone_of(self, ts):
        for e in self.P.ev('lyricfx'):
            if e['start'] - 0.3 <= ts < e['end']:
                return e.get('tone', 'bold')
        return None

    def _boom(self, r):
        lay = Image.new('RGBA', (560, 560))
        d = ImageDraw.Draw(lay)
        pts = star_pts(280, 280, 260, 120, n=11)
        d.polygon(pts, fill=(245, 190, 50, 235))
        poly_line(d, pts, (220, 50, 40), r, 10)
        inner = star_pts(280, 280, 140, 70, n=9, rot=0.3)
        d.polygon(inner, fill=(235, 80, 60, 240))
        return lay

    def fire(self, c, t, r, beat, a0, fa, pos=FC):
        d = ImageDraw.Draw(c)
        s = (0.4 + 0.6 * eout((t - a0) / 0.4)) * (1 + 0.25 * beat)
        for col, sc, n in [((225, 50, 40), 1.0, 1), ((245, 140, 40), 0.72, 1), ((255, 215, 70), 0.42, 1)]:
            pts = []
            for k in np.linspace(0, 2 * np.pi, 14):
                rad = 85 * sc * s * (1 + 0.1 * r.normal())
                y = np.sin(k) * rad * (1.2 if np.sin(k) > 0 else 1.55 + 0.3 * r.random())
                pts.append((pos[0] + np.cos(k) * rad * 0.85, pos[1] + y * 0.9))
            for _ in range(3):
                d.line(pts, fill=col + (int(r.uniform(90, 170) * fa),), width=5)
        d.ellipse((pos[0] - 110 * s, pos[1] + 55, pos[0] + 110 * s, pos[1] + 85), fill=(235, 120, 40, int(60 * fa)))

    def rays(self, d, cx, cy, tc, t, r, big=1.0):
        k = t - tc
        rr = (120 + 260 * eout(k / 0.4)) * big
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            a += tc
            jline(d, [(cx + np.cos(a) * rr * 0.6, cy + np.sin(a) * rr * 0.6), (cx + np.cos(a) * rr, cy + np.sin(a) * rr)], [(245, 190, 50), (235, 110, 40)][int(a * 3) % 2], 7, r, 2, 1)

    def glyph(self, c, e, t, r, beat, fa, vi):
        txt = e.get('text', '？')
        if e.get('action') == 'swarm':
            hits = e['hits'] or list(np.linspace(e['start'], e['end'] - 0.5, 8))
            rs = np.random.default_rng(e['seed'])
            for k, tc in enumerate(hits):
                x, y, rot = rs.uniform(180, 900), rs.uniform(640, 1500), rs.uniform(-25, 25)
                if t < tc:
                    continue
                p = eout((t - tc) / 0.2)
                paste_center(c, char_img(txt, 'zhimang', 120, PALETTE[k % 5] + (255,)), x + r.normal() * 2, y + r.normal() * 2, alpha=fa,
                             scale=1.6 - 0.6 * p + 0.06 * np.sin(t * 20 + k), rot=rot)
            return
        px, py = e.get('pos', [540, 1050])
        p = eout((t - e['start']) / 0.45)
        col = PALETTE[e['seed'] % 5]
        d = ImageDraw.Draw(c)
        n = int(30 * eout((t - e['start']) / 0.8))
        circ = [(px + 300 * np.cos(a), py + 290 * np.sin(a)) for a in np.linspace(-1.2, -1.2 + 2 * np.pi, 30)][:max(2, n)]
        jline(d, circ, (245, 190, 50) if col != (245, 190, 50) else BLUE, 8, r, 3, 2)
        g = char_img(txt, 'zhimang', 360 if len(txt) == 1 else 240, col + (255,))
        paste_center(c, g, px + r.normal() * 2, py + r.normal() * 2, alpha=p * fa, scale=1.5 - 0.5 * p + 0.04 * beat, rot=r.normal() * 1.5 + 4 * np.sin(t * 2))

    def events(self, c, t, vi, r, beat, jit, lo, hi):
        """draw all events that overlap the page [lo, hi)"""
        P = self.P
        d = ImageDraw.Draw(c)
        for e in P.events:
            ty = e['type']
            s0, s1 = e['start'], e['end']
            if s0 >= hi or s1 + 1.5 < lo or t < s0 - 0.1:
                continue
            fa = 1 - ease((t - s1) / 0.6)
            if fa <= 0 and ty not in ('fireworks', 'burst', 'thunder', 'scatter'):
                continue
            if ty == 'prop':
                sh = e.get('shape')
                if sh == 'sword':
                    m = np.clip((eout((t - s0) / 2.2) * 1.15 - self.proj) * 10, 0, 1)
                    lay = self.SWORD[vi].copy()
                    lay.putalpha(Image.fromarray((np.asarray(lay.getchannel('A'), np.float32) * m * fa).astype(np.uint8)))
                    lift = e.get('lift', s0 + min(3.6, (s1 - s0) * 0.5))
                    wob = 4 * np.sin((t - s0) * 9) if t < lift else 0
                    lay = lay.rotate(wob - 8 * ease((t - lift) / 0.8), Image.BICUBIC, center=(540, 1100))
                    c.alpha_composite(lay)
                    if t > lift:
                        n = int(40 * eout((t - lift) / 1.6))
                        for k in range(n):
                            u = k / 40
                            o = 70 + 20 * np.sin(k * 1.7)
                            jline(d, [ap(u * 1.05, 0), ap(u * 1.05, o * (1 if k % 2 else -1))], (250, 200, 40), 5, r, 3, int(fa > 0.5) + 0)
                elif sh == 'cloak':
                    m = np.clip((eout((t - s0) / 2.0) * 1.2 - self.cproj) * 8, 0, 1)
                    lay = self.CLOAKL[vi].copy()
                    lay.putalpha(Image.fromarray((np.asarray(lay.getchannel('A'), np.float32) * m * fa).astype(np.uint8)))
                    c.alpha_composite(lay.rotate(2 * np.sin(t * 1.3), Image.BICUBIC, center=(800, 720)))
                elif sh == 'fire':
                    self.fire(c, t, r, beat, s0, fa, e.get('pos', FC))
                elif sh == 'pouch':
                    yo = -500 * (1 - eout((t - s0) / 1.0)) if e.get('action') == 'drop' else 0
                    m = wipe(self.POUCH[vi], eout((t - s0) / 1.3), 1 - self.YN)
                    if m is not None:
                        c.alpha_composite(fade(m, fa), (0, int(yo)))
                    if t > s0 + 1.2:
                        lab = text_layer(e.get('text', ''), font('zhimang', 150), (200, 45, 35, 255), spacing=8) if e.get('text') else None
                        if lab is not None:
                            paste_center(c, lab, PC[0] + jit[0], PC[1] + 70 + jit[1] + yo, alpha=eout((t - s0 - 1.2) / 0.3) * fa, rot=r.normal())
                else:
                    self.glyph(c, e, t, r, beat, fa, vi)
            elif ty == 'clouds':
                s_ = wipe(self.STORM[vi], eout((t - s0) / 1.8), self.XN)
                if s_ is not None:
                    c.alpha_composite(fade(s_, fa))
            elif ty == 'dim':
                m = wipe(self.MOONP[vi], eout((t - s0) / 0.9), self.YN)
                if m is not None:
                    c.alpha_composite(fade(m, fa))
                for k, tc in enumerate(np.arange(s0 + 0.3, s1, 0.9)):
                    a = t - tc
                    if 0 <= a < 3:
                        bx, by, br = 700 + a * 60 + 20 * np.sin(a * 3), 520 - a * 110, 14 + 9 * (k % 3) + 6 * a
                        d.ellipse([bx - br, by - br, bx + br, by + br], outline=BLUE + (int(200 * (1 - ease((a - 2.2) / 0.8)) * fa),), width=5)
            elif ty == 'village':
                g = wipe(self.GROUND[vi], eout((t - s0) / 0.6), self.XN)
                if g is not None:
                    c.alpha_composite(fade(g, fa))
                hits = e['hits'] or list(np.linspace(s0 + 0.3, s0 + 2.0, 5))
                idx = np.linspace(0, len(hits) - 1, 5).astype(int) if len(hits) >= 5 else list(range(len(hits))) + [len(hits) - 1] * (5 - len(hits))
                for k in range(5):
                    tc = hits[idx[k]] + (0.15 * k if len(hits) < 5 else 0)
                    if t < tc - 0.1:
                        continue
                    h_ = wipe(self.HOUSEL[k][vi], eout((t - tc + 0.1) / 0.5), 1 - self.YN)
                    if h_ is not None:
                        c.alpha_composite(fade(h_, fa))
                if t > hits[-1] + 0.3:
                    c.alpha_composite(fade(self.WING[vi], fa * (0.8 + 0.2 * beat)))
            elif ty == 'thread':
                g1 = e.get('grow', s0 + 2.1)
                pouch_on = any(x['type'] == 'prop' and x.get('shape') == 'pouch' and x['start'] <= t <= x['end'] for x in P.events)
                x0, y0 = (PC[0] + 95, PC[1] - 150) if pouch_on else (120, 1400)
                pts = [(x0 + a * (330 if pouch_on else 800) + 80 * np.sin(a * 14), y0 - a * (780 if pouch_on else 900) + 70 * np.cos(a * 14)) for a in np.linspace(0, 1, 160)]
                n = int(160 * eout((t - s0) / max(0.3, g1 - s0)))
                if fa > 0:
                    jline(d, pts[:max(2, n)], (215, 40, 40), 9, r, 2, 3)
                    if n >= 159:
                        bx, by = pts[-1]
                        for s_ in (-1, 1):
                            jline(d, [(bx, by), (bx + s_ * 60, by - 40), (bx + s_ * 70, by + 20), (bx, by)], (215, 40, 40), 8, r, 2, 2)
            elif ty == 'burst':
                pouch_on = any(x['type'] == 'prop' and x.get('shape') == 'pouch' and x['start'] <= t <= x['end'] for x in P.events)
                rs = np.random.default_rng(e['seed'])
                for k, tc in enumerate(e['hits']):
                    cx, cy = (PC[0], PC[1] - 240) if pouch_on else (rs.uniform(250, 830), rs.uniform(600, 1300))
                    if tc <= t < tc + 0.8:
                        self.rays(d, cx, cy, tc, t, r)
            elif ty == 'thunder':
                ca = 1 - ease((t - s0 - 2.5) / 0.8)
                if ca > 0:
                    cl = wipe(self.CLOUDT[vi], eout((t - s0 + 0.3) / 0.6), 1 - self.XN)
                    if cl is not None:
                        c.alpha_composite(fade(cl, ca))
                if s0 - 0.05 < t < s0 + 1.3:
                    b = fade(self.BOLT[vi], 1 - max(0, (t - s0 - 0.9) / 0.4))
                    b = wipe(b, eout((t - s0 + 0.05) / 0.12), self.YN)
                    if b is not None:
                        c.alpha_composite(b)
                if s0 + 0.3 < t < s0 + 2.8:
                    p = eout((t - s0 - 0.3) / 0.25)
                    paste_center(c, self.HONG, 760, 720, alpha=1 - ease((t - s0 - 2.4) / 0.4), scale=1.8 - 0.8 * p, rot=-12 + r.normal())
            elif ty == 'scatter':
                k = t - s0
                if 0 <= k < 3:
                    for i in range(8):
                        if k < i * 0.12:
                            continue
                        fx, fy = 640 + i * 70 + k * 60, 1500 + (i % 2) * 30
                        d.ellipse((fx - 16, fy - 10, fx + 16, fy + 10), fill=(90, 70, 50, 200))
                    for i in range(5):
                        a = k - i * 0.15
                        if a < 0:
                            continue
                        x, y, rr = 900 + a * 380 + i * 20, 1480 - i * 20, 40 + a * 40
                        jline(d, [(x + np.cos(q) * rr, y + np.sin(q) * rr * 0.6) for q in np.linspace(0, 2 * np.pi, 16)], (150, 140, 130), 5, r, 4, 1)
            elif ty == 'fireworks':
                rs = np.random.default_rng(e['seed'])
                for k, tc in enumerate(e['hits']):
                    x, y = rs.uniform(180, 900), rs.uniform(500, 1150)
                    col = PALETTE[k % 5]
                    kk = t - tc
                    if kk < 0:
                        continue
                    rr = 40 + 170 * eout(kk / 0.5)
                    f2 = 1 - ease((kk - 1.5) / 0.8)
                    if f2 <= 0:
                        continue
                    for a in np.linspace(0, 2 * np.pi, 14, endpoint=False):
                        jline(d, [(x + np.cos(a) * rr * 0.45, y + np.sin(a) * rr * 0.45), (x + np.cos(a) * rr, y + np.sin(a) * rr + 20 * kk * kk)], col, 6, r, 2, 1)
                    if kk < 0.3:
                        jline(d, star_pts(x, y, 40, 16) + [star_pts(x, y, 40, 16)[0]], (245, 190, 50), 5, r, 2, 1)
            elif ty == 'lanterns':
                rs = np.random.default_rng(e['seed'])
                for i in range(10):
                    x, dl, sp = rs.uniform(150, 930), rs.uniform(0, 1.8), rs.uniform(0.7, 1.2)
                    k = t - s0 - dl
                    if k < 0:
                        continue
                    y = 1550 - k * 230 * sp
                    x_ = x + 25 * np.sin(k * 1.5 + i)
                    box = [(x_ - 34, y - 45), (x_ + 34, y - 45), (x_ + 28, y + 45), (x_ - 28, y + 45)]
                    d.polygon(box, fill=(235, 80, 50, int(170 * fa)))
                    poly_line(d, box, (170, 40, 30), r, 4)
                    jline(d, [(x_ - 12, y + 40), (x_ + 12, y + 40)], (255, 200, 60), 6, r, 1, 1)
            elif ty == 'stamp':
                p = eout((t - s0) / 0.25)
                txt = e.get('text', P.title[:4])
                size = 260 if len(txt) <= 2 else int(900 / len(txt))
                paste_center(c, text_layer(txt, font('zhimang', size), (220, 50, 40, 255)), *e.get('pos', [540, 800]), alpha=fa * p, scale=1.8 - 0.8 * p, rot=-8 + r.normal())
            elif ty == 'weather':
                wa = window(t, s0, s1, 1.0, 1.0)
                kind = e.get('kind', 'rain')
                rs = np.random.default_rng(e['seed'])
                for _ in range(60):
                    x, y, v = rs.random(), rs.random(), rs.random()
                    k = t - s0
                    if kind == 'rain':
                        yy_ = (y * H + k * (900 + 400 * v)) % H
                        jline(d, [(x * W, yy_), (x * W - 10, yy_ + 50)], BLUE, 4, r, 1, 1) if wa > 0.3 else None
                    else:
                        col = {'snow': (150, 170, 210), 'petals': (240, 130, 160), 'embers': (240, 120, 40)}.get(kind, BLUE)
                        yy_ = (y * H + (k * (70 + 60 * v) * (-1 if kind == 'embers' else 1))) % H
                        xx_ = x * W + 30 * np.sin(k + v * 6)
                        if wa > 0.3:
                            jline(d, [(xx_ + 10 * np.cos(q), yy_ + 8 * np.sin(q)) for q in np.linspace(0, 2 * np.pi, 8)], col, 4, r, 1, 1)

    def page(self, pg, t, vi, r, beat, jit):
        P = self.P
        lo = self.page_starts[pg]
        hi = self.page_starts[pg + 1] if pg + 1 < len(self.page_starts) else P.dur + 5
        c = Image.new('RGBA', (W, H))
        if pg == 0:
            c.alpha_composite(fade(self.BORDER[vi], ease(t / 0.8)))
        else:
            c.alpha_composite(self.BORDER[vi])
        mood = P.scenes[pg].get('mood', 'default')
        dimmed = any(e['type'] == 'dim' and e['start'] < hi and e['end'] > lo for e in P.events)
        if not dimmed:
            if mood in ('day', 'dawn', 'dusk'):
                c.alpha_composite(self.SUN[vi])
            elif mood != 'storm':
                c.alpha_composite(self.MOON[vi])
        if mood in ('default', 'night') and not dimmed:
            c.alpha_composite(self.STARS[vi])
        if pg == 0:
            c.alpha_composite(self.GROUND[vi])
        self.events(c, t, vi, r, beat, jit, lo, hi)
        return c

    def compose(self, c, g, tint):
        ca = np.asarray(c, np.float32)
        a = ca[..., 3:] / 255 * (0.55 + 0.45 * g[..., None])
        return self.paper * tint * (1 - a) + ca[..., :3] * a

    def frame(self, t):
        P = self.P
        fi = int(round(t * FPS))
        beat = P.beat(t)
        vi = (fi // 4) % 3
        g = self.grains[vi]
        r = np.random.default_rng(fi // 4)
        jit = r.normal(0, 1.5, 2)
        tint = P.mood_at(t, MOODS)
        pg = P.scene_at(t)
        out = self.compose(self.page(pg, t, vi, r, beat, jit), g, tint)
        tt = t - self.page_starts[pg]
        if pg > 0 and tt < 0.5:
            p = ease(tt / 0.5)
            old = self.compose(self.page(pg - 1, t, vi, r, beat, jit), g, tint)
            xo = int(W * (1 - p))
            new = out
            out = np.roll(old, -int(W * 0.3 * p), 1)
            out[:, xo:] = new[:, :W - xo]
            sh = np.clip(1 - (np.arange(W) - xo + 60) / 60, 0, 1)[None, :, None] * (np.arange(W) < xo)[None, :, None]
            out = out * (1 - 0.35 * sh)
        zoom = sum(e.get('amount', 0.3) * window(t, e['start'], e['end'], 1.2, 1.0) for e in P.ev('zoom'))
        if zoom > 0.005:
            s = 1 + zoom * 0.6
            im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((int(W * s), int(H * s)), Image.BILINEAR)
            x0, y0 = (im.width - W) // 2, (im.height - H) // 2
            out = np.asarray(im.crop((x0, y0, x0 + W, y0 + H)), np.float32)
        canvas = Image.new('RGBA', (W, H))
        self.overlay(canvas, t, r, jit)
        ca = np.asarray(canvas, np.float32)
        a = ca[..., 3:] / 255
        out = out * (1 - a) + ca[..., :3] * a
        for e in P.ev('thunder'):
            k = t - e['start']
            if 0 <= k < 0.4:
                fl = 0.85 * (1 - k / 0.4)
                out = out * (1 - fl) + 255 * fl
                out = shake(out, e['start'], t, 0.4, 20, fi)
        for e in P.ev('stamp'):
            out = shake(out, e['start'], t, 0.3, 14, 3)
        for tc, tn in self.impacts:
            k = t - tc
            if 0 <= k < 0.35:
                if tn == 'final':
                    fl = 0.55 * (1 - k / 0.35) ** 2
                    out = out * (1 - fl) + np.array([255, 235, 190]) * fl
                out = shake(out, tc, t, 0.35 if tn == 'final' else 0.2, 26 if tn == 'final' else 7, fi)
        fo = ease((t - P.dur + 1.2) / 1.0)
        return out * (1 - fo) + 250 * fo * ease(t / 0.01)

    def overlay(self, canvas, t, r, jit):
        P = self.P
        fa = 1 - ease((t - P.title_out) / 0.5)
        if fa > 0:
            tpos = 300
            if t > 0.3:
                p = eout((t - 0.3) / 0.6)
                paste_center(canvas, self.title, W / 2 + jit[0], tpos + (1 - p) * -80 + jit[1], alpha=p * fa, rot=r.normal() * 0.8)
            if self.sub is not None and t > 1.5:
                paste_center(canvas, self.sub, W / 2, tpos + 60 + self.title.height / 2 + 50, alpha=eout((t - 1.5) / 0.6) * fa)
        st = P.lyric_state(t)
        sung = [x for x in st if x[3] > 0]
        plain = [x for x in st if self.tones[x[0]] is None]
        for li_, j, ch, p, la, dt in plain:
            if p <= 0:
                continue
            nn = len(P.lyr[li_][0])
            step = min(104, 960 / nn)
            x = W / 2 + (j - (nn - 1) / 2) * step + jit[0]
            pe = eout(p)
            cc = char_img(ch, 'zhimang', int(step * 1.06), (40, 40, 45, 255))
            paste_center(canvas, cc, x, 1735 - 30 * (1 - pe) + r.normal() * 1.5, alpha=pe * la, rot=r.normal() * 2)
        for x in st:
            if self.tones[x[0]] is not None:
                self.climax_char(canvas, t, r, jit, *x)
        if sung and self.tones[sung[-1][0]] not in ('final',):
            li_ = sung[-1][0]
            tn = self.tones[li_]
            nn = len(P.lyr[li_][0])
            step = self.step(tn, nn)
            la = sung[-1][4]
            cur = [x for x in sung if x[0] == li_]
            x0 = W / 2 - nn * step / 2
            xe = x0 + step * (len(cur) - 1 + cur[-1][3])
            ul = Image.new('RGBA', (W, 60))
            col = dict(bold=(235, 80, 60), fragile=(120, 160, 220), tragic=(150, 25, 25), rise=(220, 50, 40)).get(tn, ORANGE)
            if tn == 'bold':
                n = max(2, int((xe - x0) / 22))
                pts = [(x0 + (xe - x0) * k / n, 24 + 14 * (k % 2)) for k in range(n + 1)]
            else:
                pts = [(x0, 30), (xe, 34)]
            jline(ImageDraw.Draw(ul), pts, col, 11 if tn in ('bold', 'tragic') else 7, r, 3, 2)
            canvas.alpha_composite(fade(ul, la), (0, self.lyr_y(tn) + 65))

    @staticmethod
    def step(tn, nn):
        if tn == 'final':
            return min(235, 980 / nn)
        if tn in ('bold', 'tragic', 'rise'):
            return min(124, 1000 / nn)
        return min(104, 960 / nn)

    @staticmethod
    def lyr_y(tn):
        return dict(final=1420, bold=1700, tragic=1700, rise=1700).get(tn, 1735)

    def climax_char(self, canvas, t, r, jit, li_, j, ch, p, la, dt):
        tn = self.tones[li_]
        nn = len(self.P.lyr[li_][0])
        step = self.step(tn, nn)
        x = W / 2 + (j - (nn - 1) / 2) * step + jit[0]
        y = self.lyr_y(tn) + jit[1]
        beat = self.P.beat(t)
        d = ImageDraw.Draw(canvas, 'RGBA')
        rs = np.random.default_rng(li_ * 100 + j)
        if tn == 'fragile':
            pe = eout(float(np.clip(dt / 0.8, 0, 1)))
            if pe <= 0:
                return
            cc = char_img(ch, 'zhimang', int(step * 1.0), (60, 95, 165, 255), stroke=6, stroke_fill=(255, 255, 255, 170))
            tr = 3.5 * np.sin(t * 11 + j * 1.7) + r.normal() * 1.5
            sink = 10 * max(0.0, dt - 0.8) if dt > 0.8 else 0
            paste_center(canvas, cc, x + tr, y - 20 * (1 - pe) + min(sink, 18), alpha=pe * la * 0.92, rot=4 * np.sin(t * 3 + j))
            if j % 3 == 1 and 0.4 < dt < 2.6:
                k = (dt - 0.4) / 2.2
                d.ellipse([x - 7, y + 55 + 90 * k - 10, x + 7, y + 55 + 90 * k + 10], fill=(120, 160, 220, int(200 * (1 - k) * la)))
            return
        if p <= 0:
            return
        if tn == 'bold':
            pop = 1 + 0.6 * np.exp(-dt * 7) * np.cos(dt * 18) + 0.05 * beat
            col = [(235, 80, 60), (235, 120, 40), (40, 110, 200), (60, 160, 90)][j % 4]
            cc = char_img(ch, 'zhimang', int(step * 1.02), col + (255,), stroke=7, stroke_fill=(255, 255, 255, 255))
            paste_center(canvas, cc, x, y - 26 * np.exp(-dt * 6) + r.normal(), alpha=la, scale=max(0.3, pop), rot=(-6 if j % 2 else 6) * np.exp(-dt * 4) + r.normal())
            if dt < 0.6:
                k = dt / 0.6
                for a in np.linspace(0, 2 * np.pi, 8, endpoint=False) + rs.uniform(0, 1):
                    r0, r1 = step * (0.55 + 0.5 * k), step * (0.75 + 0.8 * k)
                    d.line([(x + r0 * np.cos(a), y + r0 * np.sin(a)), (x + r1 * np.cos(a), y + r1 * np.sin(a))],
                           fill=(245, 190, 50, int(230 * (1 - k) * la)), width=6)
        elif tn == 'tragic':
            pe = eout(float(np.clip(dt / 0.16, 0, 1)))
            cc = char_img(ch, 'zhimang', int(step * 1.04), (165, 25, 25, 255), stroke=6, stroke_fill=(35, 30, 30, 255))
            paste_center(canvas, cc, x, y - 140 * (1 - pe) + r.normal(), alpha=la * min(1, pe * 2), scale=1.5 - 0.5 * pe + 0.03 * beat, rot=r.normal() * 1.5)
            for k in range(3):
                a = (dt * 0.9 + k / 3 + rs.uniform()) % 1.0
                if dt > 0.15:
                    ex, ey = x + rs.uniform(-40, 40) + 12 * np.sin(t * 3 + k), y - 40 - 170 * a
                    d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=(245, 140 - 60 * k % 120, 40, int(220 * (1 - a) * la)))
            if dt < 0.3:
                k = dt / 0.3
                d.ellipse([x - step * (0.5 + k), y + 40 - 18 * (0.5 + k), x + step * (0.5 + k), y + 40 + 18 * (0.5 + k)], outline=(90, 60, 50, int(200 * (1 - k))), width=5)
        elif tn == 'rise':
            f = j / max(1, nn - 1)
            col = tuple(int(a + (b - a) * f) for a, b in zip((60, 60, 70), (220, 50, 40)))
            pe = eout(p)
            sc = (0.8 + 0.45 * f) * (1.2 - 0.2 * pe)
            cc = char_img(ch, 'zhimang', int(step), col + (255,), stroke=int(2 + 5 * f), stroke_fill=(255, 245, 225, 255))
            paste_center(canvas, cc, x, y - 30 * (1 - pe) - 30 * f + r.normal() * (1 + 3 * f), alpha=pe * la, scale=sc, rot=r.normal() * 2)
        elif tn == 'final':
            pe = eout(float(np.clip(dt / 0.18, 0, 1)))
            if dt < 0.9:
                k = dt / 0.9
                for m, a in enumerate(np.linspace(0, 2 * np.pi, 16, endpoint=False) + rs.uniform(0, 0.4)):
                    r0, r1 = step * 0.6, step * (0.9 + 1.6 * eout(k)) * (1 if m % 2 else 0.7)
                    d.line([(x + r0 * np.cos(a), y + r0 * np.sin(a)), (x + r1 * np.cos(a), y + r1 * np.sin(a))],
                           fill=((245, 190, 50) if m % 2 else (220, 50, 40)) + (int(240 * (1 - k) * la),), width=9)
                rr = step * (0.5 + 1.8 * eout(k))
                d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(220, 50, 40, int(220 * (1 - k) * la)), width=10)
            col = (215, 40, 30) if j % 2 == 0 else (235, 150, 20)
            glow = char_img(ch, 'zhimang', int(step * 0.98), (245, 190, 50, 150), stroke=22, stroke_fill=(245, 190, 50, 110))
            cc = char_img(ch, 'zhimang', int(step * 0.98), col + (255,), stroke=9, stroke_fill=(35, 30, 30, 255))
            sc = 3.2 - 2.2 * pe + 0.06 * beat + 0.02 * np.sin(t * 6 + j)
            paste_center(canvas, glow, x, y, alpha=la * pe * (0.5 + 0.5 * beat), scale=sc * 1.04)
            paste_center(canvas, cc, x + r.normal() * 2, y + r.normal() * 2, alpha=la * min(1, pe * 1.6), scale=sc, rot=(-10 if j % 2 else 10) * (1 - pe) + r.normal())
