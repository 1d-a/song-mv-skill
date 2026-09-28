"""蜡笔童画 shot renderer: every shot is a self-contained illustrated page (bg + items + fx) that replaces the last one."""
import numpy as np
from PIL import Image, ImageDraw

from mvkit.core import H, W, ease, eout
from mvkit.styles import crayon_art as A

BOX = (50, 70, 1030, 1610)
BG = dict(
    day=[((190, 220, 245), 0, 0.55, 120), ((225, 238, 248), 0.55, 1, 90)],
    dawn=[((250, 200, 185), 0, 0.45, 120), ((252, 228, 170), 0.45, 1, 110)],
    dusk=[((240, 150, 100), 0, 0.35, 140), ((248, 190, 130), 0.35, 0.7, 120), ((250, 215, 160), 0.7, 1, 100)],
    night=[((30, 40, 90), 0, 0.6, 225), ((50, 60, 115), 0.6, 1, 215)],
    storm=[((80, 82, 105), 0, 0.5, 210), ((120, 120, 140), 0.5, 1, 180)],
    dark=[((22, 22, 40), 0, 1, 235)],
    indoor=[((238, 205, 160), 0, 0.72, 150), ((200, 150, 100), 0.72, 1, 190)],
    fire=[((90, 25, 25), 0, 0.45, 225), ((180, 60, 30), 0.45, 1, 200)],
    paper=[],
)


def box_mask(seed=0):
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = BOX
    pts = []
    for x in np.linspace(x0, x1, 30):
        pts.append((x, y0 + r.normal() * 3))
    for y in np.linspace(y0, y1, 50):
        pts.append((x1 + r.normal() * 3, y))
    for x in np.linspace(x1, x0, 30):
        pts.append((x, y1 + 8 * np.sin(x / 45) + r.normal() * 3))
    for y in np.linspace(y1, y0, 50):
        pts.append((x0 + r.normal() * 3, y))
    m = Image.new('L', (W, H))
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m, pts


def bg_layer(kind, r):
    lay = Image.new('RGBA', (W, H))
    x0, y0, x1, y1 = BOX
    stops = BG[kind]
    if stops:
        ys = np.linspace(0, 1, H)[:, None]
        mids = [(a + b) / 2 for _, a, b, _ in stops]
        g = np.zeros((H, 1, 4), np.float32)
        for ch in range(3):
            g[..., ch] = np.interp(ys, mids, [c[ch] for c, _, _, _ in stops])
        g[..., 3] = np.interp(ys, mids, [bb for _, _, _, bb in stops])
        lay = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), 'RGBA')
    for k, (col, a, b, base) in enumerate(stops):
        ya, yb = y0 + (y1 - y0) * a - 140, y0 + (y1 - y0) * b + 140
        dk = tuple(int(v * 0.86) for v in col)
        A.hatch(lay, A.rect(x0 - 20, ya, x1 + 20, yb), dk, r, 11, 0.55 + 0.35 * k, 4, amin=35, amax=85)
    if kind == 'indoor':
        yb = y0 + (y1 - y0) * 0.72
        for y in np.linspace(yb + 40, y1, 5):
            A.stroke(lay, [(x0, y), (x1, y + 6)], A.WOODD, r, 3, 1.5, 1)
        A.stroke(lay, [(x0, yb), (x1, yb + 4)], A.WOODD, r, 6, 1.5, 2)
    return lay


def pline(pts, u):
    """point at fraction u along polyline + partial polyline"""
    pts = np.asarray(pts, np.float32)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = seg.sum() * float(np.clip(u, 0, 1))
    out = [tuple(pts[0])]
    for k, s in enumerate(seg):
        if L <= s:
            p = pts[k] + (pts[k + 1] - pts[k]) * (L / max(s, 1e-6))
            out.append(tuple(p))
            return out
        L -= s
        out.append(tuple(pts[k + 1]))
    return out


class Book:
    def __init__(self, S, shots):
        self.S, self.P = S, S.P
        self.shots = shots
        self.starts = [s['start'] for s in shots]
        self.mask, self.box_pts = box_mask(3)
        self.mask_np = np.asarray(self.mask, np.float32) / 255
        self.bgs = {}
        self.cache = {}
        self.impacts = []
        for s in shots:
            for f in s.get('fx', []):
                if f['k'] in ('bolt', 'boom', 'flash', 'shake'):
                    for h in [f['at']] + f.get('hits', []):
                        self.impacts.append((h, f['k'], f.get('amp', 1.0)))

    def shot_at(self, t):
        return max(0, int(np.searchsorted(self.starts, t, 'right')) - 1)

    def bg(self, kind, vi):
        if kind not in self.bgs:
            self.bgs[kind] = [bg_layer(kind, np.random.default_rng(100 + i)) for i in range(3)]
        return self.bgs[kind][vi]

    def item_layers(self, si, ii):
        key = (si, ii)
        if key not in self.cache:
            if len(self.cache) > 90:
                for k in [k for k in self.cache if abs(k[0] - si) > 2]:
                    del self.cache[k]
            it = self.shots[si]['items'][ii]
            w, h = A.SIZE[it['k']]
            out = []
            for v in range(3):
                lay = Image.new('RGBA', (w, h))
                A.FN[it['k']](lay, np.random.default_rng(si * 131 + ii * 7 + v), it)
                s = it.get('s', 1.0)
                if s != 1.0:
                    lay = lay.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
                if it.get('flip'):
                    lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
                out.append(lay)
            self.cache[key] = out
        return self.cache[key]

    # ------------------------------------------------------------ items
    def draw_item(self, c, si, ii, it, t, vi, beat, r):
        t_in = it['in']
        if t < t_in:
            return
        dur = it.get('dur', 0.8)
        p = float(np.clip((t - t_in) / dur, 0, 1))
        alpha = it.get('a', 1.0)
        if 'out' in it:
            alpha *= 1 - ease((t - it['out']) / it.get('odur', 0.5))
            if alpha <= 0.01:
                return
        lay = self.item_layers(si, ii)[vi]
        x, y = it.get('x', 540), it.get('y', 900)
        rot = it.get('rot', 0.0)
        scale = 1.0
        if 'to' in it:
            m0, m1 = it.get('move', [t_in, t_in + 2.0])
            q = ease((t - m0) / max(m1 - m0, 1e-3)) if it.get('ease', True) else float(np.clip((t - m0) / max(m1 - m0, 1e-3), 0, 1))
            x += (it['to'][0] - x) * q
            y += (it['to'][1] - y) * q
            if 'rot_to' in it:
                rot += (it['rot_to'] - rot) * q
        how = it.get('how', 'draw')
        ph = (si * 1.7 + ii * 2.3)
        amp = it.get('amp', 1.0)
        for an in it.get('anim', '').split():
            if an == 'sway':
                rot += 4 * amp * np.sin(t * 1.6 + ph)
            elif an == 'bob':
                y += 12 * amp * np.sin(t * 2.2 + ph)
            elif an == 'laugh':
                y += 10 * amp * abs(np.sin(t * 9 + ph))
                rot += 5 * amp * np.sin(t * 9 + ph)
            elif an == 'shake':
                x += r.normal() * 3 * amp
                y += r.normal() * 3 * amp
            elif an == 'tremble':
                x += 4 * amp * np.sin(t * 23 + ph)
            elif an == 'pulse':
                scale *= 1 + 0.035 * amp * beat
            elif an == 'breathe':
                scale *= 1 + 0.02 * amp * np.sin(t * 1.5 + ph)
            elif an == 'spin':
                rot += (t - t_in) * 140 * amp
            elif an == 'flicker':
                alpha *= 0.72 + 0.28 * np.sin(t * 7 + ph) * np.sin(t * 3.1)
            elif an == 'drift':
                x += (t - t_in) * 14 * amp
            elif an == 'saw':
                x += 70 * amp * np.sin(t * 5)
            elif an == 'swing':
                rot += 12 * amp * np.sin(t * 2.4 + ph)
        if how == 'draw' and p < 1:
            lay = self.wipe(lay, p, 'x')
        elif how == 'grow' and p < 1:
            lay = self.wipe(lay, p, 'y')
        elif how == 'drop':
            q = min(1.0, (t - t_in) / 0.45)
            y -= (1 - q * q) * 900
            if 0.45 <= t - t_in < 0.7:
                y -= 30 * np.sin((t - t_in - 0.45) / 0.25 * np.pi)
        elif how == 'pop':
            k = t - t_in
            scale *= max(0.05, 1 - np.exp(-k * 7) * np.cos(k * 14)) if k < 1.2 else 1
        elif how == 'fade':
            alpha *= eout(p)
        elif how in ('slide_l', 'slide_r'):
            x += (1 - eout(p)) * (-900 if how == 'slide_l' else 900)
        elif how == 'rise':
            y += (1 - eout(p)) * 500
            alpha *= eout(p * 2)
        elif how == 'fall':
            y -= (1 - eout(p)) * 500
            alpha *= eout(p * 2)
        if lay is None:
            return
        if abs(scale - 1) > 0.004:
            lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
        if abs(rot) > 0.05:
            lay = lay.rotate(-rot, Image.BICUBIC, expand=True)
        if alpha < 0.995:
            a = np.asarray(lay.getchannel('A'), np.float32) * max(0.0, alpha)
            lay = lay.copy()
            lay.putalpha(Image.fromarray(a.astype(np.uint8)))
        c.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2))) if self.inside(lay, x, y) else self.paste_clip(c, lay, x, y)

    @staticmethod
    def inside(lay, x, y):
        x0, y0 = int(x - lay.width / 2), int(y - lay.height / 2)
        return x0 >= 0 and y0 >= 0 and x0 + lay.width <= W and y0 + lay.height <= H

    @staticmethod
    def paste_clip(c, lay, x, y):
        x0, y0 = int(x - lay.width / 2), int(y - lay.height / 2)
        cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x0 + lay.width), min(H, y0 + lay.height)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        c.alpha_composite(lay.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0)), (cx0, cy0))

    @staticmethod
    def wipe(lay, p, axis):
        if p <= 0:
            return None
        w, h = lay.size
        if axis == 'x':
            g = (np.arange(w, dtype=np.float32) / w)[None, :] * 0.85 + (np.arange(h, dtype=np.float32) / h)[:, None] * 0.15
        else:
            g = 1 - (np.arange(h, dtype=np.float32) / h)[:, None] * np.ones((1, w), np.float32)
        soft = 0.08
        a = np.asarray(lay.getchannel('A'), np.float32) * np.clip((p * (1 + soft) - g) / soft, 0, 1)
        l2 = lay.copy()
        l2.putalpha(Image.fromarray(a.astype(np.uint8)))
        return l2

    # ------------------------------------------------------------ fx
    def draw_fx(self, base, si, f, t, vi, beat, r):
        t0, t1 = f['at'], f.get('end', 1e9)
        if t < t0 - 0.01 or t > t1 + 0.6:
            return
        c = Image.new('RGBA', (W, H))
        self._fx(c, si, f, t, vi, beat, r, t0, t1)
        base.alpha_composite(c)

    def _fx(self, c, si, f, t, vi, beat, r, t0, t1):
        k = f['k']
        fa = 1 - ease((t - t1) / 0.6)
        tt = t - t0
        d = ImageDraw.Draw(c, 'RGBA')
        rs = np.random.default_rng(f.get('seed', 0) * 13 + si)
        x, y = f.get('x', 540), f.get('y', 900)
        s = f.get('s', 1.0)
        n = f.get('n', 0)
        if k == 'rain':
            for m in range(n or 90):
                px = (rs.uniform(0, W) + tt * 120) % W
                py = (rs.uniform(0, H) + tt * rs.uniform(900, 1300)) % 1640
                d.line([(px, py), (px - 10, py + 38)], fill=(110, 135, 190, int(170 * fa)), width=3)
        elif k in ('snow', 'frostfall'):
            for m in range(n or 70):
                sp = rs.uniform(60, 140)
                px = (rs.uniform(0, W) + 30 * np.sin(tt * 0.8 + m)) % W
                py = (rs.uniform(0, 1640) + tt * sp) % 1640
                rr = rs.uniform(5, 11)
                d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(250, 252, 255, int(230 * fa)), outline=(160, 180, 220, int(200 * fa)), width=2)
        elif k == 'embers':
            for m in range(n or 40):
                u = (tt * rs.uniform(0.15, 0.35) + rs.uniform()) % 1
                px = f.get('x', 540) + rs.uniform(-1, 1) * f.get('w', 500) + 30 * np.sin(tt * 2 + m)
                py = f.get('y', 1500) - u * f.get('h', 1200)
                rr = rs.uniform(3, 8) * (1 - u)
                d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(250, 150 + int(80 * rs.uniform()), 40, int(230 * (1 - u) * fa)))
        elif k in ('leaves', 'petals'):
            cols = [(90, 160, 80), (230, 140, 50), (210, 90, 60)] if k == 'leaves' else [(245, 160, 180), (250, 200, 210)]
            for m in range(n or 18):
                u = (tt * rs.uniform(0.12, 0.25) + rs.uniform()) % 1
                px = -100 + u * (W + 200)
                py = rs.uniform(150, 1500) + 80 * np.sin(u * 8 + m)
                a = u * 12 + m
                pts = [(px + 18 * np.cos(a + q) * (1 if j % 2 else 0.4), py + 18 * np.sin(a + q) * (1 if j % 2 else 0.4)) for j, q in enumerate(np.linspace(0, 2 * np.pi, 4, endpoint=False))]
                d.polygon(pts, fill=cols[m % len(cols)] + (int(220 * fa),))
        elif k == 'wind':
            for m in range(n or 7):
                u = (tt * rs.uniform(0.35, 0.6) + rs.uniform()) % 1
                py = rs.uniform(200, 1500)
                px = -300 + u * (W + 600)
                pts = [(px - 240 + q * 240, py + 14 * np.sin(q * 6 + m)) for q in np.linspace(0, 1, 12)]
                if m % 3 == 0:
                    pts += [(px + 30 * np.cos(a), py - 30 + 30 * np.sin(a)) for a in np.linspace(np.pi / 2, 2.4 * np.pi, 10)]
                A.jline(d, pts, (130, 150, 185), 4, r, 1.5, 1)
        elif k in ('steam', 'smoke'):
            col = tuple(f.get('col', (170, 170, 180) if k == 'smoke' else (235, 235, 240)))
            for m in range(n or (3 if k == 'steam' else 6)):
                if k == 'steam':
                    ox = (m - (n or 3) / 2 + 0.5) * 40 * s
                    u0 = (tt * 0.5 + m * 0.33) % 1
                    pts = [(x + ox + 16 * s * np.sin(q * 7 + tt * 3 + m), y - q * 220 * s) for q in np.linspace(u0 * 0.3, 0.3 + u0 * 0.7, 10)]
                    A.jline(d, pts, (200, 200, 210), 5, r, 1, 1)
                else:
                    u = (tt * 0.25 + m / (n or 6)) % 1
                    rr = (30 + 110 * u) * s
                    px = x + 60 * s * np.sin(u * 5 + m) + u * f.get('dx', 60)
                    py = y - u * f.get('h', 700)
                    d.ellipse([px - rr, py - rr * 0.8, px + rr, py + rr * 0.8], fill=col + (int(120 * (1 - u) * fa),))
                    d.ellipse([px - rr, py - rr * 0.8, px + rr, py + rr * 0.8], outline=(110, 110, 120, int(120 * (1 - u) * fa)), width=3)
        elif k == 'sparks':
            for m in range(n or 14):
                a = rs.uniform(0, 2 * np.pi)
                u = (tt * 2.2 + rs.uniform()) % 1
                rr = (20 + 110 * u) * s
                px, py = x + rr * np.cos(a), y + rr * np.sin(a) - 40 * u
                L = 16 * s * (1 - u)
                d.line([(px, py), (px + L * np.cos(a), py + L * np.sin(a))], fill=(255, 210, 60, int(255 * (1 - u) * fa)), width=4)
        elif k == 'fire':
            for m, (col, sc) in enumerate([((230, 60, 40), 1.0), ((245, 140, 40), 0.72), ((252, 215, 80), 0.42)]):
                g = min(1.0, tt / 0.6)
                pts = []
                for a in np.linspace(0, 2 * np.pi, 26, endpoint=False):
                    rr = 1 + 0.18 * np.sin(5 * a + t * 9 + m) + 0.1 * np.sin(3 * a - t * 7)
                    top = 1.0 + 0.9 * max(0.0, -np.sin(a)) * (1 + 0.25 * np.sin(t * 6 + m))
                    pts.append((x + 90 * s * sc * g * rr * np.cos(a), y - 30 * s * sc + 90 * s * sc * g * rr * np.sin(a) * top))
                d.polygon(pts, fill=col + (int(225 * fa),))
        elif k == 'glow':
            rad, col = f.get('r', 200) * (1 + 0.05 * beat), tuple(f.get('col', (255, 220, 120)))
            g = eout(tt / 0.8) * fa * (0.8 + 0.2 * np.sin(t * 5)) * f.get('a', 1.0)
            R = int(rad)
            yy, xx = np.mgrid[-R:R, -R:R].astype(np.float32)
            a = np.clip(1 - np.sqrt(xx * xx + yy * yy) / rad, 0, 1) ** 1.6 * 170 * g
            gl = Image.new('RGBA', (2 * R, 2 * R), col + (0,))
            gl.putalpha(Image.fromarray(a.astype(np.uint8)))
            self.paste_clip(c, gl, x, y)
        elif k == 'rays':
            col = tuple(f.get('col', (250, 200, 70)))
            g = eout(tt / 0.6) * fa
            r0, r1 = f.get('r0', 120) * s, f.get('r1', 420) * s
            for m, a in enumerate(np.linspace(0, 2 * np.pi, f.get('n', 18), endpoint=False) + t * 0.25):
                e = r1 * (0.8 + 0.2 * np.sin(t * 3 + m)) * g
                d.line([(x + r0 * np.cos(a), y + r0 * np.sin(a)), (x + (r0 + e) * np.cos(a), y + (r0 + e) * np.sin(a))], fill=col + (int(200 * g),), width=7)
        elif k == 'bolt':
            for h in [t0] + f.get('hits', []):
                q = t - h
                if 0 <= q < 0.55 and (q < 0.12 or 0.2 < q < 0.35):
                    lay = self.bolt_layers[vi]
                    sc = f.get('s', 1.0)
                    if sc != 1:
                        lay = lay.resize((int(lay.width * sc), int(lay.height * sc)))
                    c.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
        elif k == 'boom':
            for h in [t0] + f.get('hits', []):
                q = t - h
                if 0 <= q < 0.9:
                    lay = self.boom_layers[vi]
                    sc = s * (0.4 + 0.8 * eout(q / 0.25)) * (1 + 0.1 * q)
                    lay = lay.resize((int(lay.width * sc), int(lay.height * sc)))
                    a = np.asarray(lay.getchannel('A'), np.float32) * (1 - ease((q - 0.45) / 0.45))
                    lay.putalpha(Image.fromarray(a.astype(np.uint8)))
                    self.paste_clip(c, lay.rotate(q * 30, Image.BILINEAR), x, y)
        elif k == 'fireworks':
            cols = [(235, 70, 60), (250, 200, 60), (60, 130, 220), (80, 180, 90), (180, 100, 200)]
            for j, h in enumerate([t0] + f.get('hits', [])):
                q = t - h
                if not 0 <= q < 1.4:
                    continue
                rj = np.random.default_rng(j + 7 * si)
                px, py = rj.uniform(200, 880), rj.uniform(220, 750)
                col = cols[j % 5]
                g = eout(q / 0.7)
                for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                    r0, r1 = 150 * g * 0.5, 150 * g + 10
                    d.line([(px + r0 * np.cos(a), py + r0 * np.sin(a) + 30 * q * q), (px + r1 * np.cos(a), py + r1 * np.sin(a) + 30 * q * q)],
                           fill=col + (int(240 * (1 - q / 1.4) * fa),), width=6)
        elif k == 'lanterns':
            lay = self.sky_lantern[vi]
            for m in range(n or 8):
                st = t0 + m * f.get('gap', 0.5)
                if t < st:
                    continue
                u = (t - st) / f.get('rise', 6.0)
                px = rs.uniform(150, 930) + 30 * np.sin(t + m)
                py = f.get('y', 1500) - u * 1300
                sc = rs.uniform(0.6, 1.0) * (1 - 0.4 * u)
                if py > 60:
                    l2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))))
                    d.ellipse([px - 60 * sc, py - 40 * sc, px + 60 * sc, py + 100 * sc], fill=(255, 210, 90, int(50 * fa)))
                    self.paste_clip(c, l2, px, py)
        elif k == 'footprints':
            path = f['path']
            steps = n or 10
            big = f.get('kind', 'shoe')
            for m in range(steps):
                ts = t0 + (t1 - t0 if t1 < 1e8 else 2.0) * m / steps
                if t < ts:
                    continue
                pts = pline(path, (m + 0.5) / steps)
                px, py = pts[-1]
                q = pline(path, min(1, (m + 1) / steps))[-1]
                ang = np.arctan2(q[1] - py, q[0] - px)
                side = 1 if m % 2 else -1
                px += -np.sin(ang) * 18 * side * s
                py += np.cos(ang) * 18 * side * s
                ai = int(200 * fa * f.get('a', 1.0) * min(1, (t - ts) / 0.2))
                col = tuple(f.get('col', (90, 70, 60)))
                if big == 'claw':
                    rr = 26 * s
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col + (ai,))
                    for j in (-1, 0, 1):
                        a = ang + j * 0.5
                        cx, cy = px + np.cos(a) * rr * 1.5, py + np.sin(a) * rr * 1.5
                        d.ellipse([cx - rr * 0.35, cy - rr * 0.35, cx + rr * 0.35, cy + rr * 0.35], fill=col + (ai,))
                else:
                    pts2 = A.ell(px, py, 12 * s, 22 * s, 16)
                    ca, sa = np.cos(ang - np.pi / 2), np.sin(ang - np.pi / 2)
                    pts2 = [(px + (u - px) * ca - (v - py) * sa, py + (u - px) * sa + (v - py) * ca) for u, v in pts2]
                    d.polygon(pts2, fill=col + (ai,))
        elif k == 'thread':
            g = float(np.clip(tt / max(0.2, f.get('grow', 1.5)), 0, 1))
            pts = pline(f['path'], g)
            if len(pts) > 1:
                A.jline(d, pts, tuple(f.get('col', (215, 40, 45))), f.get('w', 7), r, 1.2, 2)
        elif k == 'bubbles':
            for m in range(n or 4):
                u = (tt * 0.35 + m / (n or 4)) % 1
                px, py = x + 60 * u + 12 * np.sin(u * 9), y - 220 * u
                rr = 10 + 26 * u
                d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(170, 190, 235, int(230 * (1 - u) * fa)), width=4)
        elif k == 'birds':
            for m in range(n or 6):
                q = max(0.0, tt - m * 0.15)
                if q <= 0:
                    continue
                a = rs.uniform(-2.6, -0.5)
                sp = rs.uniform(250, 420)
                px, py = x + np.cos(a) * sp * q, y + np.sin(a) * sp * q
                wf = 14 * np.sin(t * 12 + m)
                A.jline(d, [(px - 26, py - wf), (px, py + 6), (px + 26, py - wf)], (60, 60, 70), 5, r, 1, 1)
        elif k == 'eyes':
            lay = self.eye_layers[vi]
            flee = f.get('flee')
            for m in range(n or 6):
                st = t0 + m * f.get('gap', 0.35)
                if t < st:
                    continue
                px = f.get('x0', 150) + rs.uniform() * (f.get('x1', 930) - f.get('x0', 150))
                py = f.get('y0', 300) + rs.uniform() * (f.get('y1', 1300) - f.get('y0', 300))
                sc = rs.uniform(0.6, 1.2) * s
                blink = abs(np.sin(t * 0.9 + m * 1.7)) > 0.08
                a = min(1, (t - st) / 0.3) * fa
                if flee is not None and t > flee:
                    q = (t - flee) / 1.0
                    a *= max(0.0, 1 - q)
                    py -= 0
                    sc *= max(0.1, 1 - 0.5 * q)
                if a <= 0.02 or not blink:
                    continue
                l2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))))
                if a < 1:
                    l2.putalpha(Image.fromarray((np.asarray(l2.getchannel('A'), np.float32) * a).astype(np.uint8)))
                self.paste_clip(c, l2, px, py)
        elif k == 'pages':
            lay = self.page_layers[vi]
            for m in range(n or 6):
                q = tt - m * 0.4
                if q <= 0:
                    continue
                u = (q * 0.35) % 1.4
                px = x + u * 800 + 40 * np.sin(q * 3)
                py = y - u * 700 + 60 * np.sin(q * 2 + m)
                l2 = lay.rotate(q * 200 + m * 40, Image.BILINEAR, expand=True).resize((int(lay.width * 0.7), int(lay.height * 0.7)))
                self.paste_clip(c, l2, px, py)
        elif k == 'tears':
            for m in range(n or 3):
                u = (tt * 0.6 + m / (n or 3)) % 1
                px, py = x + (m - 1) * 30, y + u * 200
                d.ellipse([px - 8, py - 12, px + 8, py + 12], fill=(110, 160, 225, int(220 * (1 - u) * fa)))
        elif k == 'fireflies':
            for m in range(n or 8):
                px = f.get('x0', 150) + rs.uniform() * (f.get('x1', 930) - f.get('x0', 150)) + 20 * np.sin(t * 0.7 + m)
                py = f.get('y0', 300) + rs.uniform() * (f.get('y1', 1400) - f.get('y0', 300)) + 20 * np.cos(t * 0.9 + m)
                g = max(0.0, np.sin(t * rs.uniform(1.5, 3.5) + m * 2)) * fa
                for rr, al in ((46, 70), (24, 140), (9, 255)):
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(255, 220, 110, int(al * g)))
        elif k == 'crack':
            g = float(np.clip(tt / 0.3, 0, 1))
            pts = pline(f['path'], g)
            if len(pts) > 1:
                A.jline(d, pts, (30, 25, 30), 7, r, 2, 2)

    # ------------------------------------------------------------ page
    def page(self, si, t, vi, r, beat):
        sh = self.shots[si]
        c = Image.new('RGBA', (W, H))
        c.alpha_composite(self.bg(sh.get('bg', 'day'), vi))
        fx = sh.get('fx', [])
        for f in fx:
            if f.get('z') == 'back':
                self.draw_fx(c, si, f, t, vi, beat, r)
        for ii, it in enumerate(sh['items']):
            self.draw_item(c, si, ii, it, t, vi, beat, r)
            for f in fx:
                if f.get('z') == ii:
                    self.draw_fx(c, si, f, t, vi, beat, r)
        for f in fx:
            if f.get('z') is None:
                self.draw_fx(c, si, f, t, vi, beat, r)
        end = self.starts[si + 1] if si + 1 < len(self.starts) else self.P.dur
        u = float(np.clip((t - sh['start']) / max(1.0, end - sh['start']), 0, 1))
        cam = sh.get('cam', {})
        z0, z1 = cam.get('z', [1.0, 1.05])
        px0, px1 = cam.get('x', [0, 0])
        py0, py1 = cam.get('y', [0, 0])
        z = z0 + (z1 - z0) * u
        cx, cy = 540 + px0 + (px1 - px0) * u, 840 + py0 + (py1 - py0) * u
        if abs(z - 1) > 0.002 or cx != 540 or cy != 840:
            ww, hh = W / z, H / z
            x0, y0 = cx - ww * 540 / W, cy - hh * 840 / H
            c = c.transform((W, H), Image.EXTENT, (x0, y0, x0 + ww, y0 + hh), Image.BILINEAR)
        a = np.asarray(c.getchannel('A'), np.float32) * self.mask_np
        c.putalpha(Image.fromarray(a.astype(np.uint8)))
        return c

    def prepare(self):
        self.bolt_layers = [self.elem('bolt', v) for v in range(3)]
        self.boom_layers = [self.elem('boom', v) for v in range(3)]
        self.sky_lantern = [self.elem('sky_lantern', v) for v in range(3)]
        self.eye_layers = [self.elem('eyes', v) for v in range(3)]
        self.page_layers = [self.elem('page', v) for v in range(3)]

    @staticmethod
    def elem(name, v, **p):
        w, h = A.SIZE[name]
        lay = Image.new('RGBA', (w, h))
        A.FN[name](lay, np.random.default_rng(900 + v), p)
        return lay

    def frame_line(self, d, r):
        A.jline(d, self.box_pts + [self.box_pts[0]], (60, 55, 60), 6, r, 1.5, 2)
