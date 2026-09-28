"""Shared engine: project loading, audio features, drawing helpers, lyric timing."""
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = {k: os.path.join(ROOT, 'fonts', v) for k, v in dict(
    brush='mashan.ttf', wild='liujian.ttf', zhimang='zhimang.ttf', hand='zcoolxw.ttf',
    serif='serif.otf', sans='sans.otf', kai='wenkai.ttf').items()}
_font_cache = {}


def font(name, size):
    k = (name, int(size))
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONT[name], int(size))
    return _font_cache[k]


# ---------------------------------------------------------------- math / noise
def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def eout(x):
    x = np.clip(x, 0, 1)
    return 1 - (1 - x) ** 3


def window(t, a, b, fin=0.4, fout=0.4):
    """1 inside [a, b] with eased edges."""
    return float(eout((t - a) / max(fin, 1e-3)) * (1 - ease((t - b) / max(fout, 1e-3))))


def fbm1d(n, octaves=6, seed=0, rough=0.5):
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    amp = 1
    for o in range(octaves):
        k = 2 ** o * 3
        pts = rng.standard_normal(k + 3)
        y += amp * np.interp(np.linspace(0, k, n), np.arange(k + 3), pts)
        amp *= rough
    return y


def value_noise2d(h, w, scale, seed=0):
    rng = np.random.default_rng(seed)
    gh, gw = int(h / scale) + 3, int(w / scale) + 3
    g = rng.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((int(gw * scale), int(gh * scale)), Image.BICUBIC)
    return np.asarray(img, np.float32)[:h, :w] / 255


def fbm2d(h, w, scale=400, octaves=5, seed=0):
    out = np.zeros((h, w), np.float32)
    amp = 1
    tot = 0
    for o in range(octaves):
        out += amp * value_noise2d(h, w, max(scale / 2 ** o, 2), seed + o)
        tot += amp
        amp *= 0.5
    return out / tot


def pingpong(x, span):
    """map a monotonically growing offset into [0, span] bouncing back and forth."""
    if span <= 0:
        return 0
    p = x % (2 * span)
    return int(p if p <= span else 2 * span - p)


# ---------------------------------------------------------------- drawing
def text_layer(txt, fnt, fill=(255, 255, 255, 255), vertical=False, spacing=0, stroke=0, stroke_fill=None):
    """render text to a tight RGBA image"""
    if vertical:
        ims = [text_layer(c, fnt, fill, False, 0, stroke, stroke_fill) for c in txt]
        w = max(i.width for i in ims)
        h = sum(i.height for i in ims) + spacing * (len(ims) - 1)
        out = Image.new('RGBA', (w, h))
        y = 0
        for i in ims:
            out.alpha_composite(i, ((w - i.width) // 2, y))
            y += i.height + spacing
        return out
    size = fnt.size
    tmp = Image.new('RGBA', (int(size * (len(txt) + 1) * 1.3) + abs(spacing) * len(txt), int(size * 2)))
    d = ImageDraw.Draw(tmp)
    x = size // 4
    for c in txt:
        d.text((x, size // 3), c, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += d.textlength(c, font=fnt) + spacing
    bb = tmp.getbbox()
    return tmp.crop(bb) if bb else Image.new('RGBA', (1, 1))


def fit_font(name, txt, max_w, max_size, vertical=False, max_h=None):
    size = max_size
    while size > 20:
        im = text_layer(txt, font(name, size), vertical=vertical)
        if im.width <= max_w and (max_h is None or im.height <= max_h):
            return size
        size = int(size * 0.92)
    return size


def with_alpha(layer, alpha):
    if alpha >= 1:
        return layer
    layer = layer.copy()
    layer.putalpha(layer.getchannel('A').point(lambda v: int(v * max(0.0, alpha))))
    return layer


def paste_center(base, layer, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.003:
        return
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    if rot:
        layer = layer.rotate(rot, Image.BICUBIC, expand=True)
    layer = with_alpha(layer, alpha)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


_char_cache = {}


def char_img(c, fname, size, fill, stroke=0, stroke_fill=None):
    k = (c, fname, int(size), fill, stroke, stroke_fill)
    if k not in _char_cache:
        _char_cache[k] = text_layer(c, font(fname, size), fill, stroke=stroke, stroke_fill=stroke_fill)
    return _char_cache[k]


def star_pts(cx, cy, r1, r2, n=5, rot=-np.pi / 2):
    return [(cx + np.cos(rot + k * np.pi / n) * (r1 if k % 2 == 0 else r2),
             cy + np.sin(rot + k * np.pi / n) * (r1 if k % 2 == 0 else r2)) for k in range(2 * n)]


def shake(out, t0, t, dur=0.45, amp=20, seed=0):
    k = t - t0
    if 0 <= k < dur:
        dx, dy = np.random.default_rng(int(k * 100) + seed).normal(0, amp * (1 - k / dur), 2).astype(int)
        out = np.roll(out, (dy, dx), (0, 1))
    return out


# ---------------------------------------------------------------- audio
def audio_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def load_mono(path, sr=22050):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def _smooth(x, up=0.6, down=0.12):
    y = np.zeros_like(x)
    v = 0
    for i, xi in enumerate(x):
        v += (xi - v) * (up if xi > v else down)
        y[i] = v
    return y


def estimate_beats(a, sr, dur):
    """tempo + beat grid from spectral-flux autocorrelation."""
    hop = 512
    n = 2048
    fr = np.lib.stride_tricks.sliding_window_view(np.pad(a, (n // 2, n)), n)[::hop] * np.hanning(n)
    S = np.log1p(np.abs(np.fft.rfft(fr, axis=1)) * 10)
    flux = np.r_[0, np.maximum(0, np.diff(S, axis=0)).sum(1)]
    flux = flux - np.convolve(flux, np.ones(16) / 16, 'same')
    flux = np.maximum(flux, 0)
    fps = sr / hop
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    lags = np.arange(len(ac)) / fps
    bpm_range = (lags > 60 / 190) & (lags < 60 / 70)
    w = np.exp(-0.5 * (np.log2(60 / np.maximum(lags, 1e-3) / 120)) ** 2 / 0.9 ** 2)
    score = np.where(bpm_range, ac * w, 0)
    period = lags[np.argmax(score)]
    # refine period and phase
    best = (-1, period, 0)
    for p in np.linspace(period * 0.985, period * 1.015, 31):
        for ph in np.linspace(0, p, 40, endpoint=False):
            idx = ((ph + np.arange(0, dur - ph, p)) * fps).astype(int)
            idx = idx[idx < len(flux)]
            s = flux[idx].mean()
            if s > best[0]:
                best = (s, p, ph)
    _, period, phase = best
    grid = phase + np.arange(0, (dur - phase) / period) * period
    # downbeats: parity with stronger onsets
    idx = np.minimum((grid * fps).astype(int), len(flux) - 1)
    strong = grid[0::2] if flux[idx[0::2]].sum() >= flux[idx[1::2]].sum() else grid[1::2]
    return 60 / period, grid, strong


def compute_features(audio, dur):
    sr = 22050
    a = load_mono(audio, sr)
    n = 2048
    hop = sr // FPS
    nf = int(dur * FPS) + 10
    ap = np.pad(a, (n // 2, n + nf * hop))
    idx = np.arange(nf) * hop
    rms = np.zeros(nf)
    bass = np.zeros(nf)
    bands = np.zeros((nf, 32), np.float32)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    edges = np.searchsorted(freqs, np.geomspace(40, 10000, 33))
    win = np.hanning(n)
    for s in range(0, nf, 600):
        fr = np.stack([ap[i:i + n] for i in idx[s:s + 600]]) * win
        S = np.abs(np.fft.rfft(fr, axis=1))
        rms[s:s + 600] = np.sqrt((fr ** 2).mean(1))
        bass[s:s + 600] = S[:, (freqs > 30) & (freqs < 160)].mean(1)
        bands[s:s + 600] = np.stack([S[:, edges[i]:max(edges[i + 1], edges[i] + 1)].mean(1) for i in range(32)], 1)
    rms /= rms.max() + 1e-9
    bass /= np.percentile(bass, 99) + 1e-9
    bands = np.log1p(bands * 4)
    bands /= np.percentile(bands, 99) + 1e-9
    tempo, grid, strong = estimate_beats(a, sr, dur)
    t = np.arange(nf) / FPS
    loud = _smooth(rms, 0.05, 0.01)
    loud = np.clip(loud / (np.percentile(loud, 90) + 1e-9), 0.3, 1)
    beat = np.zeros(nf)
    for g in grid:
        m = t >= g
        beat[m] = np.maximum(beat[m], np.exp(-(t[m] - g) * 7) * 0.5)
    for g in strong:
        m = t >= g
        beat[m] = np.maximum(beat[m], np.exp(-(t[m] - g) * 6))
    beat *= loud
    # "drop": first beat after 2s where loudness reaches 60% of song's typical level
    lv = _smooth(rms, 0.2, 0.05)
    ref = np.percentile(lv, 70)
    cand = [g for g in strong if g > 2 and lv[min(int(g * FPS) + 3, nf - 1)] > 0.6 * ref]
    drop = float(cand[0]) if cand else float(strong[min(4, len(strong) - 1)])
    return dict(rms=_smooth(rms), bass=_smooth(np.clip(bass, 0, 1.5)), bands=np.clip(bands, 0, 1.2), beat=beat,
                grid=grid, strong=strong, tempo=np.array(tempo), drop=np.array(drop), dur=np.array(dur))


# ---------------------------------------------------------------- project
class Project:
    """project dir layout: project.json, lyrics.json (from align), storyboard.json, features.npz"""

    def __init__(self, pdir):
        self.dir = os.path.abspath(pdir)
        cfg = json.load(open(os.path.join(self.dir, 'project.json'), encoding='utf-8'))
        self.cfg = cfg
        self.audio = os.path.join(self.dir, cfg['audio'])
        self.title = cfg['title']
        self.subtitle = cfg.get('subtitle', '')
        self.credits = cfg.get('credits', '')
        self.seal = cfg.get('seal', '')
        self.dur = float(cfg.get('duration') or audio_duration(self.audio))
        fp = os.path.join(self.dir, 'features.npz')
        if not os.path.exists(fp):
            np.savez(fp, **compute_features(self.audio, self.dur))
        self.F = {k: v for k, v in np.load(fp).items()}
        self.drop = float(cfg.get('drop', self.F['drop']))
        lp = os.path.join(self.dir, 'lyrics.json')
        self.lines = json.load(open(lp, encoding='utf-8'))['lines'] if os.path.exists(lp) else []
        self.lyr = [(ln['text'], ln['times'], ln['end']) for ln in self.lines]
        self.t0 = self.lyr[0][1][0] if self.lyr else self.dur
        from mvkit.storyboard import load_storyboard
        self.sb = load_storyboard(self)
        self.scenes = self.sb['scenes']
        self.events = self.sb['events']
        self.title_out = float(cfg.get('title_out', max(3.5, self.t0 - 1.1)))

    def beat(self, t):
        return float(self.F['beat'][min(int(t * FPS), len(self.F['beat']) - 1)])

    def rms(self, t):
        return float(self.F['rms'][min(int(t * FPS), len(self.F['rms']) - 1)])

    def ev(self, kind):
        return [e for e in self.events if e['type'] == kind]

    def scene_at(self, t):
        i = 0
        for k, s in enumerate(self.scenes):
            if t >= s['start']:
                i = k
        return i

    def mood_at(self, t, moods):
        """blend of per-mood value dicts/arrays across scene boundaries (1.5 s crossfade)."""
        i = self.scene_at(t)
        cur = np.asarray(moods[self.scenes[i].get('mood', 'default')], np.float32)
        if i > 0:
            k = ease((t - self.scenes[i]['start']) / 1.5)
            if k < 1:
                prev = np.asarray(moods[self.scenes[i - 1].get('mood', 'default')], np.float32)
                cur = prev * (1 - k) + cur * k
        return cur

    def lyric_state(self, t, fade=0.35, pop=0.3):
        """(line, idx, char, p, line_alpha, dt) for visible line(s); p=0 -> not yet sung"""
        out = []
        for i, (txt, ts, end) in enumerate(self.lyr):
            nxt = self.lyr[i + 1][1][0] if i + 1 < len(self.lyr) else end + 2.0
            hide = min(nxt, end + 2.5)
            if t < ts[0] - 0.15 or t > hide + fade:
                continue
            la = 1 - float(np.clip((t - hide) / fade, 0, 1))
            for j, (c, tc) in enumerate(zip(txt, ts)):
                out.append((i, j, c, float(np.clip((t - tc) / pop, 0, 1)), la, t - tc))
        return out

    def vocal_gap(self, t):
        """True if no lyric line is active around t (instrumental section)."""
        for txt, ts, end in self.lyr:
            if ts[0] - 1.0 <= t <= end + 1.5:
                return False
        return True
