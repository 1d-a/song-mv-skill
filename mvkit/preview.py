"""三种方案图: one poster-style preview sheet per style, built from the song's own storyboard.

python -m mvkit.preview PROJECT [--styles ink,crayon,paper] [--clip 8]
writes PROJECT/out/方案A_水墨江湖.png ... (8 key frames each, intro + the most varied storyboard moments)
--clip N additionally renders an N-second clip of the busiest stretch for each style.
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw

from mvkit.core import Project, font
from mvkit.render import render, stills
from mvkit.styles import STYLES, load_style

LETTERS = 'ABC'


def key_times(P, n=8):
    """intro title moment + storyboard events spread over the song, preferring new event types."""
    t_title = min(P.title_out - 0.5, max(4.0, P.drop + 1.5))
    cands = []
    for e in P.events:
        dt = {'thunder': 0.1, 'stamp': 0.25, 'burst': 0.3}.get(e['type'], 1.2)
        tt = (e['hits'][0] + 0.3) if e['hits'] and e['type'] in ('fireworks', 'burst') else e['start'] + dt
        if e['type'] == 'prop' and 'lift' in e:
            tt = e['lift'] + 1.0
        cands.append((tt, e['type'] + str(e.get('shape', ''))))
    cands.sort()
    chosen, seen = [t_title], set()
    edges = np.linspace(P.t0, P.dur - 2, n)
    for a, b in zip(edges[:-1], edges[1:]):
        pool = [(tt, kind) for tt, kind in cands if a <= tt < b]
        if not pool:
            chosen.append(float((a + b) / 2))
            continue
        fresh = [c for c in pool if c[1] not in seen] or pool
        tt, kind = fresh[len(fresh) // 2]
        chosen.append(tt)
        seen.add(kind)
    out = []
    for c in sorted(chosen)[:n]:
        for sc in P.scenes[1:]:
            if -0.6 < c - sc['start'] < 0.8:
                c = sc['start'] + 0.8
        out.append(c)
    return out


def busiest(P, win):
    best, bt = -1, P.t0
    for s in np.arange(P.t0 - 1, P.dur - win, 1.0):
        k = sum(1 for e in P.events if s <= e['start'] <= s + win) + sum(1 for sc in P.scenes if s <= sc['start'] <= s + win)
        if k > best:
            best, bt = k, s
    return float(bt)


def sheet(P, key, times, out):
    S = load_style(key, P)
    ims = stills(None, key, times, P=P, S=S)
    tw, th, pad, head = 405, 720, 16, 150
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw + (cols + 1) * pad, head + rows * (th + pad) + pad), (22, 22, 26))
    d = ImageDraw.Draw(sh)
    k = list(STYLES).index(key)
    d.text((pad + 4, 28), f'方案{LETTERS[k]}  {STYLES[key][1]}', font=font('serif', 64), fill=(245, 235, 220))
    d.text((pad + 8, 104), f'《{P.title}》  ' + '  '.join(f'{int(t // 60)}:{t % 60:04.1f}' for t in times), font=font('sans', 28), fill=(170, 170, 175))
    for i, im in enumerate(ims):
        sh.paste(im.resize((tw, th), Image.LANCZOS), (pad + (i % cols) * (tw + pad), head + (i // cols) * (th + pad)))
    sh.save(out, quality=92)
    print('wrote', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--styles', default=','.join(STYLES))
    ap.add_argument('--clip', type=float, default=0)
    a = ap.parse_args()
    P = Project(a.project)
    times = key_times(P)
    os.makedirs(os.path.join(P.dir, 'out'), exist_ok=True)
    for key in a.styles.split(','):
        k = list(STYLES).index(key)
        sheet(P, key, times, os.path.join(P.dir, 'out', f'方案{LETTERS[k]}_{STYLES[key][1]}.jpg'))
    if a.clip:
        s = busiest(P, a.clip)
        for key in a.styles.split(','):
            k = list(STYLES).index(key)
            render(a.project, key, s, a.clip, out=os.path.join(P.dir, 'out', f'方案{LETTERS[k]}_{STYLES[key][1]}_片段.mp4'))
