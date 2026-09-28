"""方案 水墨江湖: rice paper, parallax ink mountains, mist, red sun, brush lyrics in vertical columns."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from mvkit.core import (H, W, char_img, ease, eout, fbm1d, fbm2d, fit_font, font, paste_center, pingpong, shake,
                        text_layer, value_noise2d, window)

INK = np.array([22, 22, 26], np.float32)
RED = (196, 52, 40)
# mood -> paper tint (rgb multiplier), sun colour
MOODS = dict(
    default=[1, 1, 1, 196, 58, 42], day=[1, 1, 1, 196, 58, 42], dawn=[1.0, 0.95, 0.94, 214, 96, 80],
    dusk=[1.0, 0.92, 0.80, 222, 110, 40], night=[0.70, 0.73, 0.82, 226, 224, 206], storm=[0.76, 0.76, 0.78, 120, 116, 116])


def _dry(h, w, seed):
    return np.asarray(Image.fromarray((value_noise2d(h // 10 + 3, w, 1, seed) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def ink_piece(mask, seed, color=(28, 24, 22), dry=0.6):
    """L mask -> RGBA ink brush texture"""
    a = np.asarray(mask, np.float32) / 255
    h, w = a.shape
    a = np.clip(a * (1 - dry * 0.6 + dry * _dry(h, w, seed)), 0, 1)
    edge = np.asarray(mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5)), np.float32) / 255
    a = np.clip(a + edge * 0.5, 0, 1)
    rgb = np.zeros((h, w, 3), np.float32) + np.array(color, np.float32)
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8))


class Style:
    name = '水墨江湖'

    def __init__(self, P):
        self.P = P
        rng = np.random.default_rng(1)
        self.yy, self.xx = np.mgrid[0:H, 0:W].astype(np.float32)
        yy, xx = self.yy, self.xx
        paper = np.zeros((H, W, 3), np.float32) + np.array([238, 231, 214], np.float32)
        paper *= (0.94 + 0.08 * fbm2d(H, W, 300, 6, 3)[..., None] + 0.03 * value_noise2d(H, W, 3, 9)[..., None])
        vig = 1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2) * 2.2
        self.paper = paper * vig[..., None]
        self.WL = 3000
        self.layers = [(self._mountain(11, 1050, 420, 160, 0.28, 6, 4), 6), (self._mountain(12, 1220, 380, 140, 0.45, 3, 3), 12),
                       (self._mountain(13, 1400, 330, 120, 0.68, 1.5, 3), 22), (self._mountain(14, 1640, 260, 90, 0.95, 0, 2), 40)]
        mist = fbm2d(H, self.WL + 600, 260, 5, 21)
        self.mist = np.clip((mist - 0.45) * 2.2, 0, 1)
        # title
        size = fit_font('brush', P.title, 330, 250, vertical=True, max_h=1100)
        self.title = text_layer(P.title, font('brush', size), (18, 18, 20, 255), vertical=True, spacing=-10)
        self.tarr = np.asarray(self.title).copy()
        th, tw = self.tarr.shape[:2]
        self.wipe_noise = fbm1d(tw, 5, 5, 0.6) * 25
        self.credits = text_layer(P.credits, font('kai', 38), (70, 60, 55, 255), vertical=True, spacing=4) if P.credits else None
        sub = [s for s in P.subtitle.replace('，', ' ').replace(',', ' ').split() if s]
        if len(sub) == 1 and len(sub[0]) > 5:
            s0 = sub[0]
            sub = [s0[:len(s0) // 2 + len(s0) % 2], s0[len(s0) // 2 + len(s0) % 2:]]
        self.tag = sub[:3]
        self.seal = self._seal(P.seal) if P.seal else None
        self.birds = [(rng.uniform(-200, 400), rng.uniform(500, 800), rng.uniform(50, 80), rng.uniform(0, 6)) for _ in range(5)]
        self.halo = self._halo(220)
        self.grid_after_drop = [g for g in P.F['grid'] if g >= P.drop - 0.05]
        self._clouds = fbm2d(1000, W + 900, 220, 5, 88)
        self._assets()

    # ------------------------------------------------------------ assets
    def _mountain(self, seed, base, amp, fall, dark, blur, peaks=3):
        WL = self.WL
        r = np.random.default_rng(seed)
        x = np.arange(WL)
        ridge = fbm1d(WL, 7, seed, 0.55) * amp * 0.35
        for _ in range(peaks * 2):
            c = r.uniform(0, WL)
            w = r.uniform(120, 320)
            ridge -= r.uniform(0.6, 1.0) * amp * np.exp(-((x - c) / w) ** 2) * (1 + 0.15 * np.sin(x / 13))
        ridge += base
        d = np.arange(H)[:, None].astype(np.float32) - ridge[None, :]
        cun = np.asarray(Image.fromarray((value_noise2d(H // 14 + 2, WL, 1, seed + 11) * 255).astype(np.uint8)).resize((WL, H), Image.BICUBIC), np.float32) / 255
        a = np.where(d > 0, np.exp(-d / fall) * (0.75 + 0.35 * cun) + 0.12 * np.exp(-d / (fall * 4)), 0)
        edge = np.where(d > 0, np.exp(-d / 6), 0) * 0.5
        a = np.clip((a + edge) * dark * (0.85 + 0.3 * fbm2d(H, WL, 90, 4, seed)), 0, 1)
        img = Image.fromarray((a * 255).astype(np.uint8))
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur))
        return np.asarray(img, np.float32) / 255

    def _seal(self, txt):
        txt = (txt + '    ')[:4] if len(txt) <= 4 else txt[:4]
        s = 170
        im = Image.new('RGBA', (s, s))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, s - 4, s - 4), 14, fill=(178, 34, 30, 235))
        f = font('serif', 70)
        for i, c in enumerate(txt):
            d.text((s // 2 + (38 if i < 2 else -38), 48 + (i % 2) * 78), c, font=f, fill=(245, 230, 215, 255), anchor='mm')
        a = np.asarray(im).copy()
        a[..., 3] = (a[..., 3] * np.clip(value_noise2d(s, s, 6, 4) * 1.6 - 0.1, 0, 1)).astype(np.uint8)
        return Image.fromarray(a)

    def _halo(self, s):
        halo = Image.new('RGBA', (s, s), (236, 229, 212, 0))
        hm = Image.new('L', (s, s))
        ImageDraw.Draw(hm).ellipse((30, 30, s - 30, s - 30), fill=200)
        halo.putalpha(hm.filter(ImageFilter.GaussianBlur(24)))
        return halo

    def _assets(self):
        # sword (tip up)
        SW, SH = 240, 1000
        m = Image.new('L', (SW, SH))
        d = ImageDraw.Draw(m)
        cx = SW // 2
        d.polygon([(cx - 34, 300), (cx + 34, 300), (cx + 30, 70), (cx, 0), (cx - 30, 70)], fill=255)
        d.rectangle((cx - 110, 300, cx + 110, 336), fill=255)
        d.rectangle((cx - 20, 336, cx + 20, 560), fill=255)
        d.ellipse((cx - 30, 555, cx + 30, 610), fill=255)
        self.sword_a = np.asarray(ink_piece(m, 71).getchannel('A'), np.float32) / 255
        self.sword_y = np.linspace(1, 0, SH)[:, None]
        # cloak
        m = Image.new('L', (420, 900))
        d = ImageDraw.Draw(m)
        body = [(160, 90), (260, 90), (330, 200), (350, 450), (390, 820), (340, 790), (310, 860), (270, 800), (230, 870), (190, 800),
                (150, 860), (110, 790), (60, 830), (80, 450), (100, 200)]
        d.polygon(body, fill=255)
        d.polygon([(150, 20), (270, 20), (310, 120), (210, 160), (110, 120)], fill=255)
        for k in range(5):
            d.line([(150 + k * 30, 200), (130 + k * 40, 820)], fill=120, width=6)
        self.cloak = ink_piece(m, 72, dry=0.8)
        # pouch
        m = Image.new('L', (320, 360))
        d = ImageDraw.Draw(m)
        d.ellipse((20, 90, 300, 350), fill=255)
        d.polygon([(110, 120), (60, 20), (130, 60), (160, 0), (190, 60), (260, 20), (210, 120)], fill=255)
        self.pouch = ink_piece(m, 73, dry=0.5)
        # village
        VH = 520
        lay = Image.new('RGBA', (W, VH))
        d = ImageDraw.Draw(lay)
        r = np.random.default_rng(7)
        xs = [30, 190, 340, 520, 690, 860]
        self.wins = []
        for i, x in enumerate(xs):
            w_ = r.uniform(130, 170)
            y0 = 260 + (i % 2) * 60 + r.uniform(-20, 20)
            h_ = r.uniform(110, 150)
            d.rectangle((x, y0, x + w_, y0 + h_), fill=(222, 214, 196, 255), outline=(40, 38, 40, 255), width=4)
            d.polygon([(x - 40, y0 + 10), (x + w_ / 2, y0 - 70), (x + w_ + 40, y0 + 10), (x + w_ + 20, y0 + 20), (x + w_ / 2, y0 - 40), (x - 20, y0 + 20)], fill=(30, 30, 34, 255))
            d.rectangle((x + w_ * 0.3, y0 + 40, x + w_ * 0.3 + 34, y0 + 84), fill=(40, 38, 40, 255))
            self.wins.append((x + w_ * 0.3 + 17, y0 + 62))
        d.rectangle((0, VH - 110, W, VH), fill=(30, 30, 34, 255))
        a = np.asarray(lay).copy()
        a[..., 3] = (a[..., 3] * np.clip(0.6 + 0.6 * value_noise2d(VH, W, 3, 5), 0, 1)).astype(np.uint8)
        self.village = Image.fromarray(a)
        self.VH = VH
        self.enso = [(185 * np.cos(a), 185 * np.sin(a), 10 + 9 * np.sin(k / 9) + 5 * (k / 120))
                     for k, a in enumerate(np.linspace(-2.2, -2.2 + 2 * np.pi * 0.86, 120))]
        self.thread = [(x, 900 + 170 * np.sin(x / 170) + 60 * np.sin(x / 57)) for x in np.linspace(-40, W + 40, 220)]
        rr = np.random.default_rng(5)
        self.weather = rr.random((160, 4))

    def sword_layer(self, prog, glow=0.0):
        m = np.clip((prog * 1.15 - self.sword_y) * 12, 0, 1)
        a = self.sword_a * m
        rgb = np.zeros(a.shape + (3,), np.float32) + np.array([28, 24, 22], np.float32)
        lay = Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8))
        if glow > 0:
            g = Image.new('RGBA', (lay.width + 200, lay.height + 200))
            gm = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
            gl = Image.new('RGBA', gm.size, (220, 70, 40, 0))
            gl.putalpha(gm.point(lambda v: int(v * glow)))
            g.alpha_composite(gl, (100, 100))
            g = g.filter(ImageFilter.GaussianBlur(26))
            g.alpha_composite(lay, (100, 100))
            return g
        return lay

    # ------------------------------------------------------------ events
    def draw_prop(self, pil, e, t, beat):
        a0, a1 = e['start'], e['end']
        if not (a0 - 0.1 < t < a1 + 0.9):
            return
        fa = 1 - ease((t - a1) / 0.8)
        lift = e.get('lift', a0 + min(3.6, (a1 - a0) * 0.5))
        up = ease((t - lift) / 1.2)
        px, py = e.get('pos', [680, 1050])
        shape, act = e.get('shape'), e.get('action', 'rise')
        sw = np.sin(t * 1.3 + e['seed'])
        if shape == 'sword':
            prog = eout((t - a0) / 2.4)
            rot = -38 * (1 - up) + 2 * sw
            lay = self.sword_layer(prog, glow=180 * up * fa * (0.7 + 0.3 * beat))
            paste_center(pil, lay, px, py - 250 * up + 10 * np.sin(t * 1.7), alpha=fa, rot=rot, scale=1.45 + 0.1 * up)
            return
        app = eout((t - a0) / 0.9)
        if act == 'drop':
            py = -300 + (py + 300) * eout((t - a0) / 1.2)
            ang = 8 * np.sin(t * 2.1)
            d = ImageDraw.Draw(pil)
            d.line([(px, -10), (px + np.sin(np.deg2rad(ang)) * 400, py - 150)], fill=(40, 36, 36, int(255 * fa)), width=4)
            px += np.sin(np.deg2rad(ang)) * 400
            rot = -ang
        elif act == 'sway':
            rot = 5 * sw
        else:
            py += 120 * (1 - app) - 80 * up
            rot = 3 * sw
        if shape == 'cloak':
            if 'pos' not in e:
                px, py = 800, 1260 + (py - 1050)
            paste_center(pil, self.cloak, px, py, alpha=fa * app, rot=rot, scale=0.75)
        elif shape == 'pouch':
            paste_center(pil, self.pouch, px, py, alpha=fa * app, rot=rot, scale=1.2)
            if e.get('text'):
                lab = char_img(e['text'], 'brush', 90, (200, 50, 36, 255))
                paste_center(pil, lab, px, py + 60, alpha=fa * app, rot=rot)
        elif shape == 'fire':
            if 'pos' not in e:
                px, py = 300, 1300
            lay = Image.new('RGBA', (500, 600))
            d = ImageDraw.Draw(lay)
            r = np.random.default_rng(int(t * 12))
            s = (0.6 + 0.4 * app) * (1 + 0.25 * beat)
            for col, sc in [((30, 28, 30), 1.0), ((200, 50, 36), 0.7), ((230, 120, 60), 0.4)]:
                pts = []
                for k in np.linspace(0, 2 * np.pi, 18):
                    rad = 150 * sc * s * (1 + 0.12 * r.normal())
                    y = np.sin(k) * rad * (0.9 if np.sin(k) > 0 else 2.0 + 0.4 * r.random())
                    pts.append((250 + np.cos(k) * rad * 0.8, 420 + y))
                d.polygon(pts, fill=col + (int(200 * fa),))
            paste_center(pil, lay.filter(ImageFilter.GaussianBlur(3)), px, py, alpha=app)
        elif act == 'swarm':
            hits = e['hits'] or list(np.linspace(a0, a1 - 0.5, 8))
            rs = np.random.default_rng(e['seed'])
            for k, tc in enumerate(hits):
                x, y, r0 = rs.uniform(420, 980), rs.uniform(650, 1450), rs.uniform(-20, 20)
                if t < tc:
                    continue
                p = eout((t - tc) / 0.25)
                g = char_img(e.get('text', '？')[0], 'brush', 130, (190, 40, 32, 255) if k % 3 == 2 else (22, 22, 26, 255))
                paste_center(pil, g, x, y, alpha=fa * p, scale=1.6 - 0.6 * p + 0.05 * np.sin(t * 14 + k), rot=r0)
        else:  # glyph emblem
            txt = e.get('text', '？')
            g = char_img(txt, 'brush', 380 if len(txt) == 1 else 260, (22, 22, 26, 255))
            n = int(len(self.enso) * eout((t - a0) / 1.2))
            lay = Image.new('RGBA', (520, 520))
            ld = ImageDraw.Draw(lay)
            for x, y, r_ in self.enso[:n]:
                x, y, r_ = 260 + x * 1.25, 260 + y * 1.25, r_ * 1.2
                ld.ellipse((x - r_, y - r_, x + r_, y + r_), fill=(34, 32, 34, 200))
            paste_center(pil, lay, px, py, alpha=fa)
            if app < 1:
                paste_center(pil, g.filter(ImageFilter.GaussianBlur(float(10 * (1 - app)))), px, py, alpha=fa * app * 0.6, scale=1.5 - 0.5 * app)
            paste_center(pil, g, px, py, alpha=fa * app, scale=1.1 - 0.1 * app + 0.03 * beat, rot=rot)

    def draw_clouds(self, pil, e, t):
        grow = window(t, e['start'], e['end'], 1.6, 1.6)
        if grow <= 0:
            return
        off = int(60 * (t - e['start'])) % 800
        n = self._clouds[:, off:off + W]
        ys = np.arange(1000)[:, None]
        front = 80 + 560 * grow + 40 * np.sin(np.arange(W)[None, :] / 90 + t)
        a = np.clip((n - 0.38) * 3.2, 0, 1) * np.clip((front - ys) / 180, 0, 1) * 0.92
        rgb = np.zeros((1000, W, 3), np.float32) + np.array([30, 30, 36], np.float32)
        pil.alpha_composite(Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8)))

    def draw_village(self, pil, e, t, beat):
        if not (e['start'] - 0.1 < t < e['end'] + 1.6):
            return
        vy = H - self.VH + 60 + 500 * (1 - eout((t - e['start']) / 1.8)) + 600 * ease((t - e['end']) / 1.5)
        pil.alpha_composite(self.village, (0, int(vy)))
        gl = Image.new('RGBA', (W, self.VH))
        gd = ImageDraw.Draw(gl)
        hits = e['hits'] or list(np.linspace(e['start'] + 0.6, e['start'] + 2.4, len(self.wins)))
        for k, (x, y) in enumerate(self.wins):
            tk = hits[min(k, len(hits) - 1)] if k < len(hits) else hits[-1] + 0.2 * (k - len(hits) + 1)
            if t < tk:
                continue
            a = eout((t - tk) / 0.3) * (0.8 + 0.2 * beat)
            gd.rectangle((x - 17, y - 22, x + 17, y + 22), fill=(220, 70, 40, int(255 * a)))
        pil.alpha_composite(gl.filter(ImageFilter.GaussianBlur(18)), (0, int(vy)))
        pil.alpha_composite(gl, (0, int(vy)))

    def draw_events(self, pil, t, beat):
        P = self.P
        d = ImageDraw.Draw(pil)
        for e in P.events:
            ty = e['type']
            if t < e['start'] - 0.1:
                continue
            if ty == 'prop':
                self.draw_prop(pil, e, t, beat)
            elif ty == 'clouds':
                self.draw_clouds(pil, e, t)
            elif ty == 'dim' and t < e['end'] + 1.5:
                prog = eout((t - e['start']) / 2.0)
                ea = 1 - ease((t - e['end']) / 1.5)
                lay = Image.new('RGBA', (W, 900))
                ld = ImageDraw.Draw(lay)
                sx, sy = self.sun
                for x, y, r_ in self.enso[:int(len(self.enso) * prog)]:
                    ld.ellipse((sx + x - r_, sy + y - r_, sx + x + r_, sy + y + r_), fill=(34, 32, 34, int(200 * ea)))
                pil.alpha_composite(lay)
            elif ty == 'village':
                self.draw_village(pil, e, t, beat)
            elif ty == 'thread' and t < e['end'] + 0.5:
                prog = eout((t - e['start']) / max(0.3, e.get('grow', e['start'] + 2.2) - e['start']))
                fa = 1 - ease((t - e['end']) / 0.4)
                pts = self.thread[:max(2, int(len(self.thread) * prog))]
                tl_ = Image.new('RGBA', (W, H))
                ImageDraw.Draw(tl_).line(pts, fill=(200, 40, 34, int(255 * fa)), width=9, joint='curve')
                pil.alpha_composite(tl_.filter(ImageFilter.GaussianBlur(10)))
                pil.alpha_composite(tl_)
                x, y = pts[-1]
                d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(200, 40, 34, int(255 * fa)))
            elif ty == 'burst':
                for k, tc in enumerate(e['hits']):
                    if not (tc <= t < max(e['end'], tc + 1.2)):
                        continue
                    r = np.random.default_rng(e['seed'] * 100 + k)
                    cx, cy = r.uniform(420, 980), r.uniform(700, 1250)
                    red = k >= len(e['hits']) - 2
                    p = eout((t - tc) / 0.25)
                    fa = 1 - ease((t - max(e['end'], tc + 1.2) + 1.0) / 1.0)
                    col = (200, 50, 36) if red else (26, 26, 30)
                    sp = 1.5 if red else 1
                    for _ in range(26):
                        dx, dy, r_ = r.normal(), r.normal(), r.uniform(4, 22) * p
                        x, y = cx + dx * 90 * p * sp, cy + dy * 90 * p * sp
                        d.ellipse((x - r_, y - r_, x + r_, y + r_), fill=col + (int(220 * fa),))
                    if red:
                        rr = 60 * p
                        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col + (int(230 * fa),))
            elif ty == 'thunder' and t < e['start'] + 1.2:
                r = np.random.default_rng(int((t - e['start']) * 15) + 3)
                a = 1 - ease((t - e['start'] - 0.3) / 0.9)
                x = e.get('pos', [620])[0]
                pts = [(x, -20)]
                for y in np.linspace(80, 1450, 14):
                    x += r.normal(0, 45)
                    pts.append((x, y))
                lay = Image.new('RGBA', (W, H))
                ld = ImageDraw.Draw(lay)
                ld.line(pts, fill=(20, 20, 24, int(255 * a)), width=16, joint='curve')
                for k in (4, 7, 10):
                    bx, by = pts[k]
                    bp = [(bx, by)]
                    for _ in range(4):
                        bx += r.normal(60 * (1 if k % 2 else -1), 25)
                        by += 70
                        bp.append((bx, by))
                    ld.line(bp, fill=(20, 20, 24, int(220 * a)), width=7)
                pil.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
                pil.alpha_composite(lay)
            elif ty == 'scatter' and t < e['start'] + 3:
                k = t - e['start']
                r = np.random.default_rng(e['seed'])
                for _ in range(36):
                    vx, vy, sp, ph = r.uniform(-1, 1), r.uniform(-1, 0.2), r.uniform(500, 1100), r.uniform(0, 6)
                    x = 620 + vx * sp * k
                    y = 1000 + vy * sp * k - 60 * k
                    f = np.sin(t * 16 + ph) * 12
                    s = 1 + 0.4 * k
                    d.line([(x - 22 * s, y - f * s), (x - 8 * s, y - 2), (x, y + 3), (x + 8 * s, y - 2), (x + 22 * s, y - f * s)], fill=(30, 30, 34, 220), width=4)
            elif ty == 'fireworks':
                for k, tc in enumerate(e['hits']):
                    kk = t - tc
                    if not 0 <= kk < 2.0:
                        continue
                    r = np.random.default_rng(e['seed'] * 100 + k)
                    x, y = r.uniform(250, 900), r.uniform(450, 1000)
                    R = 40 + 200 * eout(kk / 0.5)
                    fa = 1 - ease((kk - 1.2) / 0.8)
                    col = (200, 50, 36) if k % 2 else (30, 28, 30)
                    for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                        for q in (0.55, 0.8, 1.0):
                            rr = 5 + 7 * q
                            xx_, yy_ = x + np.cos(a) * R * q, y + np.sin(a) * R * q + 25 * kk * kk
                            d.ellipse((xx_ - rr, yy_ - rr, xx_ + rr, yy_ + rr), fill=col + (int(210 * fa),))
            elif ty == 'lanterns' and t < e['end'] + 1.5:
                gl = Image.new('RGBA', (W, H))
                gd = ImageDraw.Draw(gl)
                r = np.random.default_rng(e['seed'])
                fa = 1 - ease((t - e['end']) / 1.5)
                for _ in range(16):
                    x, dl, sp, ph = r.uniform(420, 1000), r.uniform(0, 1.6), r.uniform(0.7, 1.2), r.uniform(0, 6)
                    k = t - e['start'] - dl
                    if k < 0:
                        continue
                    y = H - 250 - k * 260 * sp
                    x_ = x - 200 + 25 * np.sin(k * 1.5 + ph)
                    s = 42 * max(0.4, 1.2 - 0.25 * k / 3)
                    gd.rounded_rectangle((x_ - s * 0.7, y - s, x_ + s * 0.7, y + s), 10, fill=(214, 64, 40, int(240 * fa)))
                    gd.rectangle((x_ - s * 0.45, y + s * 0.6, x_ + s * 0.45, y + s * 0.9), fill=(255, 190, 90, int(230 * fa)))
                pil.alpha_composite(gl.filter(ImageFilter.GaussianBlur(20)))
                pil.alpha_composite(gl)
            elif ty == 'stamp' and t < e['end'] + 0.5:
                p = eout((t - e['start'] + 0.05) / 0.2)
                fa = 1 - ease((t - e['end']) / 0.5)
                txt = e.get('text', P.seal or P.title[:4])
                px, py = e.get('pos', [660, 700])
                if len(txt) == 4:
                    paste_center(pil, self._seal(txt), px, py, alpha=p * fa, scale=2.4 - 0.8 * p, rot=-6)
                else:
                    g = char_img(txt, 'brush', 220 if len(txt) <= 2 else 150, (190, 40, 32, 255))
                    paste_center(pil, g, px, py, alpha=p * fa, scale=2.0 - 1.0 * p, rot=-6)
            elif ty == 'weather' and t < e['end'] + 1:
                self.draw_weather(d, e, t)

    def draw_weather(self, d, e, t):
        fa = window(t, e['start'], e['end'], 1.0, 1.0)
        kind = e.get('kind', 'rain')
        for x, y, v, s in self.weather:
            k = t - e['start']
            if kind == 'rain':
                yy_ = (y * H + k * (1400 + 500 * v)) % H
                xx_ = (x * W - k * 200) % W
                d.line([(xx_, yy_), (xx_ - 14, yy_ + 60 + 30 * v)], fill=(40, 40, 50, int(150 * fa)), width=2)
            elif kind == 'embers':
                yy_ = (y * H - k * (120 + 160 * v)) % H
                xx_ = (x * W + 30 * np.sin(k + s * 6)) % W
                r = 3 + 4 * s
                d.ellipse((xx_ - r, yy_ - r, xx_ + r, yy_ + r), fill=(210, 60, 36, int(200 * fa)))
            else:
                yy_ = (y * H + k * (60 + 90 * v)) % H
                xx_ = (x * W + 40 * np.sin(k * 0.8 + s * 6)) % W
                r = 3 + 5 * s
                col = (200, 60, 50) if kind == 'petals' else (150, 150, 158)
                d.ellipse((xx_ - r * 1.4, yy_ - r, xx_ + r * 1.4, yy_ + r), fill=col + (int(190 * fa),))

    # ------------------------------------------------------------ frame
    def frame(self, t):
        P = self.P
        beat = P.beat(t)
        mood = P.mood_at(t, MOODS)
        tint, scol = mood[:3], mood[3:]
        img = self.paper * tint
        paper_t = img.copy()
        zoom = sum(e.get('amount', 0.3) * window(t, e['start'], e['end'], 1.6, 1.2) for e in P.ev('zoom'))
        cam = 1 + 0.04 * ease(t / 8) + (0.012 * beat if t > P.drop else 0) + 0.2 * zoom
        # sun / moon
        sleep = max([window(t, e['start'], e['end'], 1.5, 1.2) for e in P.ev('dim')] + [0])
        sx = 250
        sy = 360 + 15 * min(t, 8) + 40 * sleep
        self.sun = (sx, sy)
        sr = 110 * (1 + 0.08 * beat * (t > P.drop))
        dsun = np.sqrt((self.xx[:900] - sx) ** 2 + (self.yy[:900] - sy) ** 2)
        sa = np.clip((sr - dsun) / 4, 0, 1) * 0.75 * ease(t / 2) * (1 - 0.5 * sleep)
        sc = scol * (1 - sleep) + np.array([150, 140, 135], np.float32) * sleep
        img[:900] = img[:900] * (1 - sa[..., None]) + sc * sa[..., None]
        for li, (a, sp) in enumerate(self.layers):
            off = pingpong(150 + sp * t * 1.3, self.WL - W)
            al = a[:, off:off + W]
            if cam != 1:
                s = 1 + (cam - 1) * (li + 1) / 2
                al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((int(W * s), int(H * s)), Image.BILINEAR), np.float32)[
                    int(H * (s - 1) * 0.6):int(H * (s - 1) * 0.6) + H, int(W * (s - 1) / 2):int(W * (s - 1) / 2) + W] / 255
            al = al * ease((t - li * 0.25) / 1.6)
            img = img * (1 - al[..., None]) + INK * al[..., None]
            mo = pingpong(100 + (li + 1) * 30 * t, 600)
            m = self.mist[:, mo:mo + W] * np.exp(-((self.yy - (1150 + li * 180)) / 170) ** 2) * 0.85
            img = img * (1 - m[..., None]) + paper_t * m[..., None]
        # ripples on strong beats in instrumental parts
        for g in P.F['strong']:
            dt = t - g
            if dt < 0 or dt > 2.2 or g < P.drop - 0.1 or not P.vocal_gap(g):
                continue
            R = 40 + dt * 330
            dd = np.abs(np.sqrt((self.xx[1500:] - 540) ** 2 + ((self.yy[1500:] - 1780) * 3.2) ** 2) - R)
            ra = np.clip(1 - dd / 5, 0, 1) * 0.5 * (1 - dt / 2.2)
            img[1500:] = img[1500:] * (1 - ra[..., None]) + INK * ra[..., None]
        pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
        dr = ImageDraw.Draw(pil)
        for bx, by, sp, ph in self.birds:
            x = (bx + sp * t * 2.2) % (W + 400) - 200
            y = by - 12 * (t % 30) + 8 * np.sin(t + ph)
            f = np.sin(t * 7 + ph) * 12 * (1 + beat * 0.5)
            dr.line([(x - 22, y - f), (x - 8, y - 2), (x, y + 3), (x + 8, y - 2), (x + 22, y - f)], fill=(30, 30, 34, 200), width=4, joint='curve')
        self.draw_intro(pil, t)
        self.draw_events(pil, t, beat)
        self.draw_scene_wipe(pil, t)
        self.draw_lyrics(pil, t)
        out = np.asarray(pil.convert('RGB'), np.float32)
        fi_ = ease(t / 0.8) * (1 - ease((t - P.dur + 1.6) / 1.5))
        out = out * fi_ + 245 * (1 - fi_)
        return self.post(out, t)

    def draw_intro(self, pil, t):
        P = self.P
        tfa = 1 - ease((t - P.title_out) / 1.0)
        if tfa <= 0:
            return
        th = self.tarr.shape[0]
        prog = eout((t - 0.8) / 2.6) * (th + 80) - 40
        m = np.clip((prog + self.wipe_noise[None, :] - np.arange(th)[:, None]) / 30, 0, 1)
        ta = self.tarr.copy()
        ta[..., 3] = (ta[..., 3] * m * tfa).astype(np.uint8)
        tlay = Image.fromarray(ta)
        tx, ty = 820, 380 + th // 2
        sh = tlay.filter(ImageFilter.GaussianBlur(10))
        sh.putalpha(sh.getchannel('A').point(lambda v: int(v * 0.35)))
        paste_center(pil, sh, tx + 4, ty + 6)
        paste_center(pil, tlay, tx, ty - 60 * (1 - tfa))
        yb = ty + th // 2
        if self.seal is not None and t > 3.6:
            paste_center(pil, self.seal, tx - 10, yb + 120, alpha=eout((t - 3.6) / 0.25) * tfa, scale=1.4 - 0.4 * eout((t - 3.6) / 0.25))
            yb += 220
        if self.credits is not None and t > 2.5:
            paste_center(pil, self.credits, tx + 170, 380 + self.credits.height / 2, alpha=eout((t - 2.5) / 1) * tfa)
        tf = font('brush', 92)
        k = 0
        for col, line in enumerate(self.tag):
            for ci, ch in enumerate(line):
                if k >= len(self.grid_after_drop) or t < self.grid_after_drop[k]:
                    return
                p = eout((t - self.grid_after_drop[k]) / 0.35) * tfa
                k += 1
                cx_, cy_ = 300 - col * 125, 640 + ci * 112
                paste_center(pil, self.halo, cx_, cy_, alpha=p, scale=0.9)
                paste_center(pil, text_layer(ch, tf, (25, 25, 28, 255)), cx_, cy_, alpha=p * 0.92, scale=1.25 - 0.25 * p)

    def draw_scene_wipe(self, pil, t):
        for s in self.P.scenes[1:]:
            k = (t - s['start'] + 0.35) / 0.9
            if not 0 <= k <= 1:
                continue
            lay = Image.new('RGBA', (W, H))
            d = ImageDraw.Draw(lay)
            r = np.random.default_rng(int(s['start'] * 10))
            x = W + 300 - (W + 900) * eout(k)
            for j in range(26):
                y = 200 + j * 62 + r.normal(0, 10)
                ln = 500 + 300 * r.random()
                d.line([(x + r.normal(0, 30), y), (x + ln, y + r.normal(0, 8))], fill=(30, 30, 34, int(200 * np.sin(np.pi * k) * r.uniform(0.3, 1))), width=int(r.uniform(18, 50)))
            pil.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4)))

    def draw_lyrics(self, pil, t):
        P = self.P
        for li_, j, ch, p, la, dt in P.lyric_state(t):
            if p <= 0:
                continue
            n = len(P.lyr[li_][0])
            per = n if n <= 7 else (n + 1) // 2 if n <= 14 else (n + 2) // 3
            col, row = divmod(j, per)
            cx_, cy_ = 300 - col * 135, 700 + row * 125
            cl = char_img(ch, 'brush', 110, (22, 22, 26, 255))
            pe = eout(p)
            paste_center(pil, self.halo, cx_, cy_, alpha=pe * la)
            if pe < 1:
                paste_center(pil, cl.filter(ImageFilter.GaussianBlur(float(8 * (1 - pe)))), cx_, cy_, alpha=pe * la * 0.6, scale=1.5 - 0.5 * pe)
            paste_center(pil, cl, cx_, cy_, alpha=pe * la, scale=1.15 - 0.15 * pe)

    def post(self, out, t):
        for e in self.P.ev('thunder'):
            k = t - e['start']
            if 0 <= k < 0.5:
                inv = 255 - out
                m = 1.0 if k < 0.08 or 0.16 < k < 0.22 else max(0, 1 - (k - 0.22) / 0.2) * 0.4
                out = out * (1 - m) + inv * m
                out = shake(out, e['start'], t, 0.5, 22)
        for e in self.P.ev('stamp'):
            out = shake(out, e['start'], t, 0.3, 16, 9)
        return out
