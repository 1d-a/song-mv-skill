"""方案 剪纸月夜: layered paper-cut moonlit valley with cliffs, rope bridge, village and red paper lyric tiles."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from mvkit.core import H, W, FPS, char_img, ease, eout, fbm1d, fbm2d, fit_font, font, paste_center, shake, text_layer, value_noise2d, window

HH = H + 240
# mood -> sky top rgb, sky bottom rgb
MOODS = dict(default=[18, 24, 62, 58, 40, 88], night=[14, 18, 50, 48, 34, 80], dusk=[60, 36, 90, 214, 120, 90],
             dawn=[70, 90, 150, 236, 170, 160], day=[80, 130, 200, 190, 210, 230], storm=[20, 22, 30, 60, 60, 74])


class Style:
    name = '剪纸月夜'

    def __init__(self, P):
        self.P = P
        self.view_y = 0 if P.OH == H else 240
        rng = np.random.default_rng(5)
        yy, _ = np.mgrid[0:HH, 0:W].astype(np.float32)
        self.u = (yy / HH)[..., None]
        self.tex = fbm2d(HH, W, 60, 4, 9)
        self.fiber = value_noise2d(HH, W, 2, 3)
        self.skytex = (0.93 + 0.1 * self.tex[..., None])
        moon = Image.new('L', (W, HH))
        ImageDraw.Draw(moon).ellipse((260, 420, 820, 980), fill=255)
        self.moonL = self.lfm(moon, (246, 226, 180), 30)
        mg = Image.new('RGBA', (W, HH))
        ImageDraw.Draw(mg).ellipse((160, 320, 920, 1080), fill=(255, 220, 160, 90))
        self.mglow = mg.filter(ImageFilter.GaussianBlur(80))
        self.cloudA = self.lfm(self.cloud_mask(300, 900, 1.3, 1), (205, 196, 220), 14)
        self.cloudB = self.lfm(self.cloud_mask(820, 620, 1.0, 2), (180, 176, 210), 14)
        self.far = self.lfm(self.ridge_mask(1250, 320, 3, 4), (60, 62, 110), 20)
        self.mid = self.lfm(self.ridge_mask(1400, 260, 4, 3), (44, 44, 86), 20)
        cl = Image.new('L', (W, HH))
        d = ImageDraw.Draw(cl)
        d.polygon(list(zip([0, 250, 330, 345, 310, 330, 290, 300, 250, 0], [1180, 1175, 1190, 1350, 1500, 1650, 1800, 2000, HH, HH])), fill=255)
        d.polygon(list(zip([W, 800, 760, 740, 780, 750, 790, 770, W], [1110, 1115, 1130, 1300, 1450, 1650, 1850, HH, HH])), fill=255)
        self.houses = [(830, 1115, 110, 80), (960, 1112, 100, 95)]
        for x, y, w, h in self.houses:
            d.rectangle((x, y - h, x + w, y), fill=255)
            d.polygon([(x - 28, y - h + 6), (x - 10, y - h - 8), (x + w / 2, y - h - 58), (x + w + 10, y - h - 8), (x + w + 28, y - h + 6), (x + w / 2, y - h - 22)], fill=255)
            d.rectangle((x + w * 0.7, y - h - 60, x + w * 0.7 + 16, y - h - 20), fill=255)
        for px, py in [(90, 1180), (170, 1178)]:
            for j in range(4):
                wd = 70 - j * 14
                d.polygon([(px - wd, py - j * 45), (px + wd, py - j * 45), (px, py - j * 45 - 80)], fill=255)
        self.cliffs = self.lfm(cl, (22, 22, 44), 22)
        self.windows = [(x + w * 0.3, y - h * 0.55) for x, y, w, h in self.houses]
        self.chimney = [(x + w * 0.7 + 8, y - h - 60) for x, y, w, h in self.houses]
        self.B0, self.B1 = np.array([330., 1190.]), np.array([760., 1130.])
        self.deck = self.bridge_pts(18, 90)
        self.rope = self.bridge_pts(40, 60) - np.array([0, 70])
        size = fit_font('serif', P.title, 400, 150, vertical=True, max_h=900)
        title = text_layer(P.title, font('serif', size), (245, 230, 205, 255), vertical=True, spacing=10)
        ban = Image.new('RGBA', (title.width + 90, title.height + 110))
        bd = ImageDraw.Draw(ban)
        bd.rectangle((0, 0, ban.width - 1, ban.height - 1), fill=(168, 32, 30, 240))
        bd.rectangle((12, 12, ban.width - 13, ban.height - 13), outline=(245, 210, 170, 255), width=3)
        ban.alpha_composite(title, (45, 55))
        self.ban = ban
        self.tag = text_layer(P.subtitle, font('kai', fit_font('kai', P.subtitle, 900, 60)), (245, 230, 205, 255), spacing=6) if P.subtitle else None
        self.credits = text_layer(P.credits, font('kai', 40), (245, 230, 205, 220), spacing=4) if P.credits else None
        NS = 140
        self.fs = dict(x=rng.uniform(0, W, NS), y=rng.uniform(0, H, NS), v=rng.uniform(40, 110, NS), s=rng.uniform(2, 5, NS), p=rng.uniform(0, 6, NS))
        self.lbeats = [g for g in P.F['grid'] if g > P.drop - 0.05][:4]
        # pieces
        sm_ = Image.new('L', (220, 1000))
        sd = ImageDraw.Draw(sm_)
        cx = 110
        sd.polygon([(cx - 40, 640), (cx + 40, 640), (cx + 36, 90), (cx, 0), (cx - 36, 90)], fill=255)
        sd.rectangle((cx - 105, 640, cx + 105, 690), fill=255)
        sd.rectangle((cx - 24, 690, cx + 24, 900), fill=255)
        sd.ellipse((cx - 34, 890, cx + 34, 960), fill=255)
        self.SWORD = self.piece(sm_, (186, 128, 72))
        swd = ImageDraw.Draw(self.SWORD)
        for y in range(760, 950, 26):
            swd.line([(60 + cx - 24, 60 + y), (60 + cx + 24, 60 + y + 14)], fill=(120, 30, 26, 255), width=7)
        swd.line([(60 + cx, 210), (60 + cx, 660)], fill=(150, 100, 55, 255), width=4)
        tm = Image.new('L', (120, 260))
        ImageDraw.Draw(tm).polygon([(60, 0), (100, 60), (85, 250), (60, 200), (35, 250), (20, 60)], fill=255)
        self.TASSEL = self.piece(tm, (190, 36, 32), 8)
        self.DC1 = self.lfm(self.cloud_mask(540, 560, 2.0, 7), (40, 42, 72), 18)
        self.DC2 = self.lfm(self.cloud_mask(540, 780, 1.7, 8), (40, 42, 72), 18)
        em = Image.new('L', (W, HH))
        ImageDraw.Draw(em).ellipse((260, 400, 820, 960), fill=255)
        self.ECL = self.lfm(em, (26, 32, 70), 16)
        pm = Image.new('L', (300, 340))
        pd = ImageDraw.Draw(pm)
        pd.ellipse((20, 80, 280, 330), fill=255)
        pd.polygon([(100, 110), (60, 20), (120, 55), (150, 0), (180, 55), (240, 20), (200, 110)], fill=255)
        self.POUCH = self.piece(pm, (176, 36, 32))
        ImageDraw.Draw(self.POUCH).rectangle((155, 160, 265, 178), fill=(240, 200, 90, 255))
        cm = Image.new('L', (420, 760))
        ImageDraw.Draw(cm).polygon([(150, 40), (270, 40), (330, 160), (350, 420), (390, 720), (330, 690), (290, 740), (250, 690), (210, 740),
                                    (170, 690), (130, 740), (90, 690), (40, 720), (80, 420), (100, 160)], fill=255)
        self.CLOAK = self.piece(cm, (70, 96, 150))
        bm = Image.new('L', (420, 1000))
        ImageDraw.Draw(bm).polygon([(250, 0), (60, 470), (200, 450), (40, 1000), (380, 380), (230, 400), (400, 0)], fill=255)
        self.BOLT = self.piece(bm, (250, 214, 90))
        self.FLAME = []
        for k, col in enumerate([(200, 40, 30), (240, 120, 40), (250, 210, 90)]):
            fm = Image.new('L', (300, 420))
            s = 1 - k * 0.28
            ImageDraw.Draw(fm).polygon([(150 + 130 * s * np.cos(a) * (1 - 0.3 * np.sin(a * 3)), 300 + (np.sin(a) * 110 * s if np.sin(a) > 0 else np.sin(a) * 290 * s))
                                        for a in np.linspace(0, 2 * np.pi, 40)], fill=255)
            self.FLAME.append(self.piece(fm, col, 10))
        rr5 = np.random.default_rng(21)
        self.TORCH = [(rr5.uniform(40, 300), rr5.uniform(900, 930), rr5.uniform(0, 6)) for _ in range(7)]
        tile = Image.new('RGBA', (112, 112))
        td = ImageDraw.Draw(tile)
        td.rectangle((0, 0, 111, 111), fill=(170, 34, 30, 255))
        td.rectangle((7, 7, 104, 104), outline=(245, 210, 170, 255), width=2)
        self.tile = tile
        sh = Image.new('RGBA', (140, 140))
        ImageDraw.Draw(sh).rectangle((14, 14, 126, 126), fill=(0, 0, 0, 150))
        self.tile_sh = sh.filter(ImageFilter.GaussianBlur(8))
        self._tiles = {}

    # ------------------------------------------------------------ builders
    def lfm(self, mask, color, shadow=18):
        m = np.asarray(mask, np.float32) / 255
        col = np.array(color, np.float32) * (0.9 + 0.14 * self.tex[..., None] + 0.05 * self.fiber[..., None])
        er = np.asarray(mask.filter(ImageFilter.MinFilter(7)), np.float32) / 255
        col = col * (1 + 0.12 * (m - er)[..., None])
        lay = Image.fromarray(np.dstack([np.clip(col, 0, 255), m * 255]).astype(np.uint8))
        sh = Image.new('RGBA', (W, HH))
        sh.putalpha(mask.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: int(v * 0.55)))
        out = Image.new('RGBA', (W, HH))
        out.alpha_composite(sh, (8, 14))
        out.alpha_composite(lay)
        return out

    def piece(self, mask_img, color, shadow=14):
        m = np.asarray(mask_img, np.float32) / 255
        h, w_ = m.shape
        t_ = fbm2d(h, w_, 40, 3, 17)
        col = np.array(color, np.float32) * (0.9 + 0.16 * t_[..., None])
        er = np.asarray(mask_img.filter(ImageFilter.MinFilter(7)), np.float32) / 255
        col = col * (1 + 0.15 * (m - er)[..., None])
        lay = Image.fromarray(np.dstack([np.clip(col, 0, 255), m * 255]).astype(np.uint8))
        pad = 60
        out = Image.new('RGBA', (w_ + pad * 2, h + pad * 2))
        sh = Image.new('RGBA', out.size)
        sm = Image.new('L', out.size)
        sm.paste(mask_img, (pad + 10, pad + 16))
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: int(v * 0.6)))
        out.alpha_composite(sh)
        out.alpha_composite(lay, (pad, pad))
        return out

    def cloud_mask(self, cx, cy, s, seed):
        m = Image.new('L', (W, HH))
        d = ImageDraw.Draw(m)
        for k in range(5):
            x = cx + (k - 2) * 60 * s
            rr_ = (45 + 25 * np.sin(k * 1.7 + seed)) * s
            d.ellipse((x - rr_, cy - rr_ * 0.9 - (k % 2) * 20 * s, x + rr_, cy + rr_ * 0.6), fill=255)
        d.rectangle((cx - 170 * s, cy, cx + 170 * s, cy + 22 * s), fill=255)
        return m

    def ridge_mask(self, base, amp, seed, peaks):
        x = np.arange(W)
        r = fbm1d(W, 6, seed, 0.5) * amp * 0.25 + base
        rr = np.random.default_rng(seed)
        for _ in range(peaks):
            c = rr.uniform(0, W)
            wd = rr.uniform(90, 220)
            r -= rr.uniform(0.5, 1) * amp * np.exp(-((x - c) / wd) ** 2)
        m = Image.new('L', (W, HH))
        ImageDraw.Draw(m).polygon([(0, HH)] + list(zip(x.tolist(), r.tolist())) + [(W, HH)], fill=255)
        return m

    def bridge_pts(self, n, sag):
        u = np.linspace(0, 1, n)
        p = self.B0[None] + (self.B1 - self.B0)[None] * u[:, None]
        p[:, 1] += sag * 4 * u * (1 - u)
        return p

    def char_tile(self, ch, size=112):
        k = (ch, size)
        if k not in self._tiles:
            t = self.tile.copy()
            c = char_img(ch, 'serif', 76, (248, 232, 205, 255))
            t.alpha_composite(c, ((112 - c.width) // 2, (112 - c.height) // 2))
            self._tiles[k] = t if size == 112 else t.resize((size, size), Image.LANCZOS)
        return self._tiles[k]

    # ------------------------------------------------------------ frame
    def active(self, t, kind, shape=None):
        return [e for e in self.P.events if e['type'] == kind and (shape is None or e.get('shape') == shape) and e['start'] - 0.1 <= t <= e['end'] + 1.0]

    def frame(self, t):
        P = self.P
        fi = int(round(t * FPS))
        beat = P.beat(t)
        pan_len = max(3.0, min(7.5, P.t0 - 0.5))
        pan = 240 * (1 - eout(min(t, pan_len) / pan_len))
        m = P.mood_at(t, MOODS)
        sky = (m[:3] * (1 - self.u) + m[3:] * self.u) * self.skytex
        so = int(pan * 0.2)
        frame = Image.fromarray(np.clip(sky[240 - so:240 - so + H], 0, 255).astype(np.uint8)).convert('RGBA')

        def comp(layer, par, dx=0, a=1.0):
            off = int(pan * par)
            crop = layer.crop((0, 240 - off, W, 240 - off + H))
            if a < 1:
                crop.putalpha(crop.getchannel('A').point(lambda v: int(v * max(0, a))))
            frame.alpha_composite(crop, (int(dx), 0))

        dims = [e for e in P.ev('dim') if e['start'] - 0.1 <= t <= e['end'] + 1.2]
        moon_dim = max([window(t, e['start'], e['end'], 1.5, 1.0) for e in dims] + [0])
        comp(self.mglow, 0.3, a=(0.7 + 0.3 * beat) * (1 - 0.8 * moon_dim))
        comp(self.moonL, 0.3)
        for e in dims:
            ex = 600 * (1 - eout((t - e['start']) / 2.0)) + 170 + 700 * ease((t - e['end']) / 1.0)
            comp(self.ECL, 0.3, dx=ex)
        drift = t % 60
        drift = drift if drift < 30 else 60 - drift
        comp(self.cloudB, 0.4, dx=-40 + 12 * drift)
        comp(self.far, 0.55)
        comp(self.cloudA, 0.6, dx=30 - 16 * drift)
        comp(self.mid, 0.75)
        cl_in = max([window(t, e['start'], e['end'], 1.6, 1.5) for e in P.ev('clouds')] +
                    [window(t, e['start'] - 1.5, e['start'] + 2.5, 0.5, 1.0) for e in P.ev('thunder')] + [0])
        if cl_in > 0:
            comp(self.DC1, 0.3, dx=-W * (1 - cl_in) - 60, a=min(1, cl_in * 1.5))
            comp(self.DC2, 0.3, dx=W * (1 - cl_in) + 80, a=min(1, cl_in * 1.5))
        oy = 240 - pan
        sm = Image.new('RGBA', (W, H))
        sd = ImageDraw.Draw(sm)
        for cx_, cy_ in self.chimney:
            for k in range(12):
                a = ((t * 0.6 + k / 12) % 1)
                y = cy_ - a * 380 + 240 - pan
                x = cx_ + np.sin(a * 6 + t) * 30 * a + a * 60
                r_ = 10 + a * 38
                sd.ellipse((x - r_, y - r_, x + r_, y + r_), fill=(210, 205, 225, int(120 * (1 - a))))
        frame.alpha_composite(sm.filter(ImageFilter.GaussianBlur(4)))
        bd2 = ImageDraw.Draw(frame)
        rp = [(x, y - oy) for x, y in self.rope]
        dk = [(x, y - oy) for x, y in self.bridge_pts(40, 90)]
        for x, y in self.deck:
            bd2.line([(x, y - oy - 70), (x, y - oy)], fill=(20, 20, 40, 255), width=3)
        bd2.line(rp, fill=(20, 20, 40, 255), width=5)
        bd2.line(dk, fill=(20, 20, 40, 255), width=12)
        for i in range(len(self.deck) - 1):
            x, y = self.deck[i]
            bd2.line([(x, y - oy - 10), (x, y - oy + 8)], fill=(40, 34, 60, 255), width=10)
        comp(self.cliffs, 1.0)
        gl = Image.new('RGBA', (W, H))
        gd = ImageDraw.Draw(gl)
        for e in P.ev('scatter'):
            if not (e['start'] - 2.0 < t < e['start'] + 2.5):
                continue
            ta = eout((t - e['start'] + 2.0) / 0.4)
            run = max(0, t - e['start'])
            for x, y, ph in self.TORCH:
                x_ = x + 20 * np.sin(t * 2 + ph) - run * run * 260 - run * 120
                fa = ta * (1 - ease(run / 1.4))
                if fa <= 0:
                    continue
                fl_ = 16 + 6 * np.sin(t * 20 + ph)
                gd.line([(x_, y - oy + 240), (x_ + 4, y - oy + 200)], fill=(40, 26, 20, int(255 * fa)), width=5)
                gd.ellipse((x_ - fl_ * 0.7, y - oy + 200 - fl_ * 1.5, x_ + fl_ * 0.7 + 4, y - oy + 200 + fl_ * 0.4), fill=(255, 150, 40, int(255 * fa)))
        wa = 0.35 + 0.65 * eout((t - P.drop) / 0.4)
        vhits = sorted(h for e in P.ev('village') for h in e['hits'] if h <= t)
        vact = self.active(t, 'village')
        for k, (x, y) in enumerate(self.windows):
            wb = wa * (1 + 0.5 * max([ease((t - h) / 0.3) * (1 - ease((t - h - 0.8) / 0.6)) for h in vhits[-3:]] + [0]) + 0.3 * bool(vact))
            gd.rectangle((x - 14, y - oy - 16, x + 14, y - oy + 16), fill=(255, 190, 90, int(min(255, 255 * wb))))
        lans = [(u, self.lbeats[k]) for k, u in enumerate([0.2, 0.4, 0.6, 0.8]) if k < len(self.lbeats)]
        for e in P.ev('village') + P.ev('thread'):
            hs = e['hits'] or [e['start'] + 0.3 * k for k in range(5)]
            lans += [(u, hs[min(k, len(hs) - 1)]) for k, u in enumerate([0.1, 0.3, 0.5, 0.7, 0.9])] if e['type'] == 'village' else []
            if e['type'] == 'thread':
                g1 = e.get('grow', e['start'] + 2.0)
                lans += [(u, g1 + 0.12 * k) for k, u in enumerate([0.1, 0.3, 0.5, 0.7, 0.9])]
        for u, tb in lans:
            if t < tb:
                continue
            p = eout((t - tb) / 0.3)
            x, y = rp[int(u * 39)]
            y += 40
            gd.line([(x, y - 40), (x, y - 18)], fill=(20, 20, 40, 255), width=2)
            s_ = 18 * p * (1 + 0.15 * beat)
            gd.ellipse((x - s_ * 0.8, y - s_, x + s_ * 0.8, y + s_), fill=(230, 60, 40, 255))
        glow = gl.filter(ImageFilter.GaussianBlur(22))
        frame.alpha_composite(glow)
        frame.alpha_composite(glow)
        frame.alpha_composite(gl)
        pouch_xy = self.draw_props(frame, t, beat, fi)
        self.draw_fx(frame, t, beat, fi, rp, pouch_xy)
        fl = Image.new('RGBA', (W, H))
        fd = ImageDraw.Draw(fl)
        fs = self.fs
        for x, y, v, s_, p in zip(fs['x'], fs['y'], fs['v'], fs['s'], fs['p']):
            yy_ = (y + v * t) % H
            xx_ = (x + 25 * np.sin(t + p)) % W
            fd.ellipse((xx_ - s_, yy_ - s_, xx_ + s_, yy_ + s_), fill=(240, 240, 255, 170))
        frame.alpha_composite(fl)
        z = 1 + sum(e.get('amount', 0.38) * window(t, e['start'], e['end'], 1.8, 0.9) for e in P.ev('zoom'))
        if z > 1.001:
            zc = (560, 930)
            ww, hh = W / z, H / z
            x0 = min(max(zc[0] - ww / 2, 0), W - ww)
            y0 = min(max(zc[1] - hh * 0.45, 0), H - hh)
            frame = frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + ww, y0 + hh))
        self.draw_text(frame, t)
        out = np.asarray(frame.convert('RGB'), np.float32) * ease(t / 0.8) * (1 - ease((t - P.dur + 1.6) / 1.5))
        for e in P.ev('thunder'):
            k = t - e['start']
            if 0 <= k < 0.45:
                fl_ = 0.6 * (1 - k / 0.45)
                out = out * (1 - fl_) + 250 * fl_
                out = shake(out, e['start'], t, 0.45, 20, fi)
        for e in P.ev('stamp'):
            out = shake(out, e['start'], t, 0.3, 14, 5)
        return out

    def draw_props(self, frame, t, beat, fi):
        pouch_xy = None
        for e in self.active(t, 'prop'):
            s0, s1 = e['start'], e['end']
            sh = e.get('shape')
            outp = ease((t - s1) / 1.0)
            if sh == 'sword':
                pin = eout((t - s0) / 1.2)
                lift = e.get('lift', s0 + min(3.6, (s1 - s0) * 0.5))
                up = ease((t - lift) / 1.0)
                rot = (1 - pin) * -120 + (-35) * (1 - up) + 3 * np.sin(t * 1.4)
                x = 560 + (1 - pin) * 700
                y = 660 - 40 * up + 1400 * outp ** 2 + 12 * np.sin(t * 1.9)
                sc = 0.9 + 0.12 * up + 0.05 * beat * up
                if up > 0:
                    hal = Image.new('RGBA', (700, 1300))
                    ImageDraw.Draw(hal).ellipse((150, 100, 550, 1200), fill=(255, 200, 120, int(90 * up)))
                    paste_center(frame, hal.filter(ImageFilter.GaussianBlur(60)), x, y, rot=rot)
                paste_center(frame, self.SWORD, x, y, rot=rot, scale=sc)
                a_ = np.deg2rad(rot)
                paste_center(frame, self.TASSEL, x + np.sin(a_) * 440 * sc, y + np.cos(a_) * 440 * sc + 90, rot=rot * 0.3 + 8 * np.sin(t * 3), scale=sc)
            elif sh == 'pouch':
                dn = eout((t - s0) / 1.2)
                sw_ = 8 * np.sin(t * 2.1) * (1 - 0.5 * dn)
                px, py = 420 + np.sin(np.deg2rad(sw_)) * 500, -250 + 950 * dn - 1100 * outp
                ImageDraw.Draw(frame).line([(420, -10), (px, py - 150)], fill=(200, 60, 50, 255), width=4)
                paste_center(frame, self.POUCH, px, py, rot=-sw_)
                if e.get('text'):
                    lab = text_layer(e['text'], font('serif', 70 if len(e['text']) <= 2 else 50), (248, 225, 170, 255), spacing=4)
                    paste_center(frame, lab, px, py + 40, rot=-sw_)
                pouch_xy = (px, py)
            elif sh == 'cloak':
                dn = eout((t - s0) / 1.2)
                x, y = e.get('pos', [860, 1380])
                paste_center(frame, self.CLOAK, x + 20 * np.sin(t * 1.1), y - 900 * (1 - dn) + 1300 * outp ** 2, rot=6 * np.sin(t * 1.3), scale=0.6)
            elif sh == 'fire':
                x, y = e.get('pos', [540, 1020])
                gr = eout((t - s0) / 0.6) * (1 - outp)
                for k, fl in enumerate(self.FLAME):
                    s = gr * (0.8 + 0.12 * np.sin(t * (9 + k * 3) + k) + 0.2 * beat)
                    if s > 0.02:
                        paste_center(frame, fl, x + 6 * np.sin(t * 7 + k), y - 40 * k * s, scale=s, rot=4 * np.sin(t * 5 + k))
            else:
                self.draw_glyph(frame, e, t, beat, outp)
        return pouch_xy

    def draw_glyph(self, frame, e, t, beat, outp):
        txt = e.get('text', '？')
        if e.get('action') == 'swarm':
            hits = e['hits'] or list(np.linspace(e['start'], e['end'] - 0.5, 8))
            rs = np.random.default_rng(e['seed'])
            for k, tc in enumerate(hits):
                x, y, rot = rs.uniform(180, 900), rs.uniform(500, 1400), rs.uniform(-25, 25)
                if t < tc:
                    continue
                p = eout((t - tc) / 0.3)
                paste_center(frame, self.char_tile(txt[0]), x, y - 1400 * outp ** 2, scale=1.3 - 0.3 * p, rot=rot * p + (1 - p) * 90, alpha=p)
            return
        x, y = e.get('pos', [540, 860])
        p = eout((t - e['start']) / 0.6)
        size = 360
        big = Image.new('RGBA', (size, size))
        d = ImageDraw.Draw(big)
        d.rectangle((0, 0, size - 1, size - 1), fill=(170, 34, 30, 250))
        d.rectangle((16, 16, size - 17, size - 17), outline=(245, 210, 170, 255), width=4)
        c = text_layer(txt, font('serif', int(size * 0.62 / max(1, len(txt) ** 0.8))), (248, 232, 205, 255))
        big.alpha_composite(c, ((size - c.width) // 2, (size - c.height) // 2))
        sq = abs(np.cos((1 - p) * np.pi / 2 * 3))
        big = big.resize((max(1, int(size * (0.2 + 0.8 * sq))), size), Image.LANCZOS)
        paste_center(frame, self.tile_sh.resize((size + 60, size + 60)), x + 10, y + 16 - 1400 * outp ** 2, alpha=p)
        paste_center(frame, big, x, y - 1400 * outp ** 2, rot=4 * np.sin(t * 1.5), scale=1 + 0.04 * beat)

    def draw_fx(self, frame, t, beat, fi, rp, pouch_xy):
        P = self.P
        lay = Image.new('RGBA', (W, H))
        d = ImageDraw.Draw(lay)
        for e in P.ev('burst'):
            for k, tc in enumerate(e['hits']):
                if not tc <= t < max(e['end'], tc + 1.2):
                    continue
                rs = np.random.default_rng(e['seed'] * 50 + k)
                fx, fy = (pouch_xy[0], pouch_xy[1] + 185) if pouch_xy else (rs.uniform(250, 830), rs.uniform(500, 1100))
                r7 = np.random.default_rng(fi)
                kk = t - tc
                for _ in range(22):
                    a = r7.uniform(0, 2 * np.pi)
                    rr = r7.uniform(10, 110) * (1 + beat + kk)
                    x2, y2, s2 = fx + np.cos(a) * rr, fy + np.sin(a) * rr, r7.uniform(3, 8)
                    d.polygon([(x2, y2 - s2), (x2 + s2 * 0.5, y2), (x2, y2 + s2), (x2 - s2 * 0.5, y2)], fill=(255, 210, 90, int(255 * (1 - ease(kk / 1.2)))))
        for e in P.ev('thread'):
            if not e['start'] <= t <= e['end'] + 0.5:
                continue
            n = eout((t - e['start']) / max(0.3, e.get('grow', e['start'] + 2.0) - e['start']))
            px, py = (pouch_xy[0], pouch_xy[1]) if pouch_xy else (160, 900)
            tgt = rp[int(0.9 * 39)]
            path = [(px + (tgt[0] - px) * u + 60 * np.sin(u * 9), py + 180 + (tgt[1] - py - 180) * u - 120 * np.sin(u * np.pi)) for u in np.linspace(0, n, 60)]
            d.line(path, fill=(235, 50, 40, int(255 * (1 - ease((t - e['end']) / 0.5)))), width=6, joint='curve')
        for e in P.ev('lanterns'):
            if not e['start'] <= t <= e['end'] + 6:
                continue
            rs = np.random.default_rng(e['seed'])
            for _ in range(14):
                x, dl, sp_, ph = rs.uniform(620, 1040), rs.uniform(0, 1.8), rs.uniform(0.7, 1.2), rs.uniform(0, 6)
                k = t - e['start'] - dl
                if k < 0:
                    continue
                y = 900 - k * 240 * sp_
                x_ = x - 40 * k + 20 * np.sin(k * 1.5 + ph)
                s_ = 26
                d.polygon([(x_ - s_ * 0.8, y - s_), (x_ + s_ * 0.8, y - s_), (x_ + s_ * 0.6, y + s_), (x_ - s_ * 0.6, y + s_)], fill=(220, 70, 40, 240))
                d.rectangle((x_ - s_ * 0.4, y + s_ * 0.5, x_ + s_ * 0.4, y + s_ * 0.9), fill=(255, 210, 110, 255))
        cols = [(230, 70, 50), (250, 200, 90), (120, 180, 230), (240, 140, 170)]
        for e in P.ev('fireworks'):
            rs = np.random.default_rng(e['seed'])
            for k, tc in enumerate(e['hits']):
                x, y = rs.uniform(200, 880), rs.uniform(300, 800)
                kk = t - tc
                if kk < 0 or kk > 2.2:
                    continue
                R = 50 + 190 * eout(kk / 0.6)
                fa = 1 - ease((kk - 1.4) / 0.8)
                col = cols[k % 4]
                for j in range(16):
                    a = j * np.pi / 8 + tc
                    px_, py_ = x + np.cos(a) * R, y + np.sin(a) * R + 30 * kk * kk
                    ca, sa_ = np.cos(a), np.sin(a)
                    d.polygon([(px_ + ca * 16, py_ + sa_ * 16), (px_ - sa_ * 5, py_ + ca * 5), (px_ - ca * 16, py_ - sa_ * 16), (px_ + sa_ * 5, py_ - ca * 5)], fill=col + (int(255 * fa),))
        for e in P.ev('weather'):
            wa = window(t, e['start'], e['end'], 1.0, 1.0)
            if wa <= 0:
                continue
            kind = e.get('kind', 'rain')
            rs = np.random.default_rng(e['seed'])
            for _ in range(120):
                x, y, v = rs.random() * W, rs.random() * H, rs.random()
                k = t - e['start']
                if kind == 'rain':
                    yy_ = (y + k * (1300 + 500 * v)) % H
                    d.line([(x - 0.15 * yy_ % W, yy_), (x - 0.15 * yy_ % W - 8, yy_ + 50)], fill=(200, 210, 240, int(160 * wa)), width=2)
                else:
                    col = {'snow': (250, 250, 255), 'petals': (250, 170, 190), 'embers': (255, 150, 60)}.get(kind, (250, 250, 255))
                    yy_ = (y + k * (80 + 80 * v) * (-1 if kind == 'embers' else 1)) % H
                    xx_ = (x + 30 * np.sin(k + v * 6)) % W
                    s = 4 + 5 * v
                    d.ellipse((xx_ - s, yy_ - s * 0.7, xx_ + s, yy_ + s * 0.7), fill=col + (int(220 * wa),))
        g_ = lay.filter(ImageFilter.GaussianBlur(14))
        frame.alpha_composite(g_)
        frame.alpha_composite(lay)
        for e in P.ev('thunder'):
            if e['start'] - 0.05 < t < e['start'] + 1.1:
                p = eout((t - e['start'] + 0.05) / 0.15)
                paste_center(frame, self.BOLT, e.get('pos', [300])[0], -600 + 1050 * p, alpha=1 - ease((t - e['start'] - 0.6) / 0.5), rot=-8)
        for e in P.ev('stamp'):
            if e['start'] <= t <= e['end'] + 0.5:
                p = eout((t - e['start']) / 0.25)
                txt = e.get('text', P.title[:4])
                size = 150 if len(txt) <= 4 else int(600 / len(txt))
                tl = text_layer(txt, font('serif', size), (248, 232, 205, 255), vertical=True, spacing=8)
                ban = Image.new('RGBA', (tl.width + 70, tl.height + 80))
                bd = ImageDraw.Draw(ban)
                bd.rectangle((0, 0, ban.width - 1, ban.height - 1), fill=(168, 32, 30, 245))
                bd.rectangle((10, 10, ban.width - 11, ban.height - 11), outline=(245, 210, 170, 255), width=3)
                ban.alpha_composite(tl, (35, 40))
                paste_center(frame, ban, *e.get('pos', [540, 760]), alpha=p * (1 - ease((t - e['end']) / 0.5)), scale=1.8 - 0.8 * p, rot=-4)

    def draw_text(self, frame, t):
        P = self.P
        to = P.title_out
        if 0.8 < t < to + 1.2:
            p = eout((t - 0.8) / 1.4) * (1 - ease((t - to + 0.1) / 1.0))
            hcrop = max(1, int(self.ban.height * p))
            frame.alpha_composite(self.ban.crop((0, 0, self.ban.width, hcrop)), (W - self.ban.width - 70, self.view_y + 110))
            if self.credits is not None:
                paste_center(frame, self.credits, W - 70 - self.ban.width / 2, self.view_y + 110 + self.ban.height + 60, alpha=p)
        for li_, j, ch, p, la, dt in P.lyric_state(t):
            if p <= 0:
                continue
            nn = len(P.lyr[li_][0])
            step = min(124, 1000 / nn)
            ts = int(min(112, step * 0.9))
            x = W / 2 + (j - (nn - 1) / 2) * step
            y = self.view_y + self.P.OH - 185
            pe = eout(p)
            rot = (1 - pe) * (25 if j % 2 else -25) + (2 if j % 2 else -2)
            paste_center(frame, self.tile_sh, x + 6, y + 10, alpha=pe * la, scale=(1.4 - 0.4 * pe) * ts / 112, rot=rot)
            paste_center(frame, self.char_tile(ch, ts), x, y - 30 * (1 - pe), alpha=pe * la, scale=1.4 - 0.4 * pe, rot=rot)
        ts, te = P.drop + 0.3, P.t0 - 0.3
        if te - ts <= 1.5:
            ts, te = 1.5, max(3.0, P.t0 - 0.2)
        if self.tag is not None and ts < t < te:
            p = eout((t - ts) / 0.8) * (1 - ease((t - te + 0.7) / 0.7))
            paste_center(frame, self.tag, W / 2, self.view_y + self.P.OH - 160 + 20 * (1 - p), alpha=p)
