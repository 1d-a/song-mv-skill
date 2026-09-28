"""Storyboard = scenes (mood / page changes) + timed visual events, shared by all three styles.

Time references accepted anywhere a time is expected:
  12.5          absolute seconds
  "L3"          start of lyric line 3 (1-based)       "L3.end"  end of line 3
  "L3.2"        time of 2nd sung char of line 3      "T0" first vocal, "drop", "end"
  any of the above + offset, e.g. "L3.2+0.4", "L7-0.3"
hits (list of instants) accept a list of refs or one of:
  "chars:L5"  every char of line 5      "beats:L9~L10.end" / "strong:30~40" beat grid in a range
"""
import json
import os
import re
import sys

import numpy as np

TYPES = {
    'prop': 'object on screen. shape=sword|pouch|cloak|fire|glyph; text=label/glyph chars; action=rise|sway|drop; lift=time the object stands up/raises',
    'clouds': 'dark clouds press in over the sky',
    'dim': 'sun/moon falls asleep (wanes to crescent / grey), comes back after end',
    'village': 'houses appear; windows light up on hits',
    'thread': 'a red thread grows across the frame',
    'burst': 'explosion / ink splash / sparks at each hit',
    'thunder': 'lightning strike + flash + camera shake at start',
    'scatter': 'birds / torches / creatures flee away from start',
    'fireworks': 'fireworks at each hit',
    'lanterns': 'sky lanterns rise from start',
    'stamp': 'big word slams onto screen (text=...)',
    'weather': 'kind=rain|snow|petals|embers particles',
    'zoom': 'camera pushes in (amount, default 0.3) and back out at end',
    'lyricfx': 'climax lyric treatment for lines starting in [start, end): tone=bold|fragile|tragic|rise|final',
}
SHAPES = ('sword', 'pouch', 'cloak', 'fire', 'glyph')
MOODS = ('default', 'day', 'dusk', 'night', 'storm', 'dawn')
DEFAULT_LEN = dict(thunder=1.4, burst=1.2, scatter=3.0, stamp=1.5, fireworks=2.5)


class Refs:
    def __init__(self, P):
        self.P = P

    def t(self, r):
        if isinstance(r, (int, float)):
            return float(r)
        s = str(r).strip()
        m = re.fullmatch(r'(.+?)([+-]\d+(?:\.\d+)?)', s)
        if m and not re.fullmatch(r'-?\d+(\.\d+)?', s):
            return self.t(m.group(1)) + float(m.group(2))
        if re.fullmatch(r'-?\d+(\.\d+)?', s):
            return float(s)
        if s == 'T0':
            return self.P.t0
        if s == 'drop':
            return self.P.drop
        if s == 'end':
            return self.P.dur
        m = re.fullmatch(r'L(\d+)(?:\.(\d+|end))?', s)
        if not m:
            raise ValueError(f'bad time ref {r!r}')
        li = int(m.group(1)) - 1
        if not 0 <= li < len(self.P.lyr):
            raise ValueError(f'line out of range in {r!r} (song has {len(self.P.lyr)} lines)')
        txt, ts, end = self.P.lyr[li]
        if m.group(2) is None:
            return ts[0]
        if m.group(2) == 'end':
            return end
        return ts[min(int(m.group(2)), len(ts)) - 1]

    def hits(self, h):
        if h is None:
            return []
        if isinstance(h, str):
            kind, _, rng = h.partition(':')
            if kind == 'chars':
                li = int(rng.strip()[1:]) - 1
                return list(self.P.lyr[li][1])
            if kind in ('beats', 'strong'):
                a, b = rng.split('~')
                a, b = self.t(a), self.t(b)
                g = self.P.F['grid' if kind == 'beats' else 'strong']
                return [float(x) for x in g if a <= x <= b]
            return [self.t(h)]
        return [self.t(x) for x in h]


def auto_scenes(P):
    """one scene per two lyric lines, plus the intro and instrumental gaps."""
    sc = [dict(start=0.0, mood='default')]
    for i in range(0, len(P.lyr), 2):
        st = P.lyr[i][1][0] - 0.25
        if st - sc[-1]['start'] > 3:
            sc.append(dict(start=round(st, 2), mood='default'))
    return sc


def load_storyboard(P):
    path = os.path.join(P.dir, 'storyboard.json')
    raw = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    R = Refs(P)
    scenes = [dict(s, start=R.t(s['start'])) for s in raw.get('scenes', [])] or auto_scenes(P)
    scenes.sort(key=lambda s: s['start'])
    if scenes[0]['start'] > 0:
        scenes.insert(0, dict(start=0.0, mood=scenes[0].get('mood', 'default')))
    events = []
    for k, e in enumerate(raw.get('events', [])):
        e = dict(e)
        e['start'] = R.t(e['start'])
        e['end'] = R.t(e['end']) if 'end' in e else e['start'] + DEFAULT_LEN.get(e['type'], 4.0)
        for key in ('lift', 'grow'):
            if key in e:
                e[key] = R.t(e[key])
        e['hits'] = R.hits(e.get('hits'))
        e['seed'] = k
        events.append(e)
    events.sort(key=lambda e: e['start'])
    shots = load_shots(raw.get('shots', []), R)
    if shots and not raw.get('scenes'):
        scenes = [dict(start=s['start'], mood=SHOT_MOOD.get(s.get('bg', 'day'), 'default')) for s in shots]
        if scenes[0]['start'] > 0:
            scenes.insert(0, dict(start=0.0, mood=scenes[0]['mood']))
    return dict(scenes=scenes, events=events, shots=shots)


SHOT_MOOD = dict(day='day', dawn='dawn', dusk='dusk', night='night', storm='storm', dark='night', fire='dusk', indoor='default', paper='default')


def load_shots(raw, R):
    """shots: [{start, bg, cam, items:[{k, x, y, s, in, out, move, ...}], fx:[{k, at, end, hits, ...}]}]"""
    shots = []
    for si, sh in enumerate(raw):
        sh = dict(sh)
        sh['start'] = R.t(sh['start'])
        items = []
        for ii, it in enumerate(sh.get('items', [])):
            it = dict(it)
            it['in'] = R.t(it['in']) if 'in' in it else sh['start'] + 0.15 + 0.3 * ii
            for key in ('out',):
                if key in it:
                    it[key] = R.t(it[key])
            if 'move' in it:
                it['move'] = [R.t(x) for x in it['move']]
            items.append(it)
        sh['items'] = items
        fxs = []
        for fi, f in enumerate(sh.get('fx', [])):
            f = dict(f)
            f['at'] = R.t(f['at']) if 'at' in f else sh['start']
            if 'end' in f:
                f['end'] = R.t(f['end'])
            if 'flee' in f:
                f['flee'] = R.t(f['flee'])
            f['hits'] = R.hits(f.get('hits'))
            f['seed'] = si * 10 + fi
            fxs.append(f)
        sh['fx'] = fxs
        shots.append(sh)
    shots.sort(key=lambda s: s['start'])
    return shots


# keyword -> event template used by --draft
KEYWORDS = [
    ('雷|电|霆', dict(type='thunder', at='char')),
    ('烟花|庆|喊|欢', dict(type='fireworks', hits='chars')),
    ('火药|爆|炸|点燃', dict(type='burst', hits='chars_tail')),
    ('灯|祈|愿', dict(type='lanterns')),
    ('剑', dict(type='prop', shape='sword', action='rise')),
    ('衫|衣|袍', dict(type='prop', shape='cloak', action='sway')),
    ('火|焰|烛|光', dict(type='prop', shape='fire', action='sway')),
    ('袋|包|囊', dict(type='prop', shape='pouch', action='drop')),
    ('线|丝|绳', dict(type='thread')),
    ('村|家|人间|屋|庭院|炊烟', dict(type='village', hits='chars')),
    ('云|挡|压|黑天|风', dict(type='clouds')),
    ('醒|睡|眠|夜|月|梦', dict(type='dim')),
    ('跑|逃|散|飞|远', dict(type='scatter', at='char')),
    ('雨|泪', dict(type='weather', kind='rain')),
    ('雪|霜|寒', dict(type='weather', kind='snow')),
    ('花|春', dict(type='weather', kind='petals')),
]
STOP = set('我你他她它们的了着在是有也不一这那把就都说来去得地要会还又与和')


def draft(P):
    """naive keyword storyboard; the agent is expected to rewrite it by hand."""
    events, scenes = [], auto_scenes(P)
    sec_mood = {'dark': 'storm', 'urgent': 'storm', 'heavy': 'storm', 'wounded': 'night', 'despair': 'night',
                'quiet': 'dusk', 'hesitant': 'dusk', 'outro': 'dawn', 'gentle': 'dawn', 'warm': 'dusk'}
    for s in scenes[1:]:
        li = next(i for i, (_, ts, _) in enumerate(P.lyr) if ts[0] - 0.25 >= s['start'] - 0.01)
        sec = (P.lines[li].get('section') or '').lower()
        s['mood'] = next((v for k, v in sec_mood.items() if k in sec), 'default')
    for i, (txt, ts, end) in enumerate(P.lyr):
        L = f'L{i + 1}'
        got = None
        for pat, tpl in KEYWORDS:
            m = re.search(pat, txt)
            if not m:
                continue
            e = {k: v for k, v in tpl.items() if k not in ('at', 'hits')}
            j = m.start() + 1
            e['start'] = f'{L}.{j}' if tpl.get('at') == 'char' else L
            e['end'] = f'{L}.end+1'
            if tpl.get('hits') == 'chars':
                e['hits'] = f'chars:{L}'
            elif tpl.get('hits') == 'chars_tail':
                e['hits'] = [f'{L}.{k}' for k in range(max(1, len(txt) - 1), len(txt) + 1)]
            got = e
            break
        if got is None:  # fall back to the most "noun-like" char as a glyph emblem
            cand = [c for c in txt if c not in STOP] or list(txt)
            got = dict(type='prop', shape='glyph', text=cand[-1], action='rise', start=L, end=f'{L}.end+0.8')
        got['_line'] = txt
        events.append(got)
    return dict(scenes=[dict(start=round(s['start'], 2), mood=s['mood']) for s in scenes], events=events)


def lint(P, verbose=True):
    """print the timeline and flag stretches of singing with no new visual change."""
    marks = [(s['start'], f"SCENE mood={s.get('mood', 'default')}") for s in P.scenes]
    probs = []
    for e in P.events:
        if e['type'] not in TYPES:
            probs.append(f"unknown type {e['type']}")
        if e['type'] == 'prop' and e.get('shape') not in SHAPES:
            probs.append(f"unknown prop shape {e.get('shape')}")
        if e['start'] > P.dur or e['end'] < e['start']:
            probs.append(f"bad time range {e['type']} {e['start']:.2f}-{e['end']:.2f}")
        desc = e['type'] + (f"/{e.get('shape')}" if e['type'] == 'prop' else '') + (f" '{e.get('text', '')}'" if e.get('text') else '')
        marks.append((e['start'], desc))
        marks.extend((h, f'  · hit {e["type"]}') for h in e['hits'][:1])
    for sh in P.sb.get('shots', []):
        marks.append((sh['start'], f"SHOT bg={sh.get('bg', 'day')} " + ' '.join(it['k'] for it in sh['items'])))
        marks.extend((it['in'], f"  + {it['k']}") for it in sh['items'] if it['in'] > sh['start'] + 0.2)
        marks.extend((f['at'], f"  ~ {f['k']}") for f in sh['fx'] if f['at'] > sh['start'] + 0.2)
    marks.sort()
    starts = sorted(m[0] for m in marks)
    for txt, ts, end in P.lyr:
        a, b = ts[0], end
        inside = [s for s in starts if a - 1.0 <= s <= b]
        if not inside:
            probs.append(f'no visual change during line "{txt}" ({a:.1f}-{b:.1f}s)')
    for x, y in zip(starts, starts[1:] + [P.dur]):
        if y - x > 8 and sum(not P.vocal_gap(u) for u in np.arange(x, y, 1.0)) > 8:
            probs.append(f'{y - x:.1f}s without any new visual change ({x:.1f}-{y:.1f}s)')
    if verbose:
        li = 0
        for t, d in marks:
            while li < len(P.lyr) and P.lyr[li][1][0] <= t:
                print(f'{P.lyr[li][1][0]:7.2f}  ♪ L{li + 1} {P.lyr[li][0]}')
                li += 1
            print(f'{t:7.2f}  {d}')
        print('\nPROBLEMS:' if probs else '\nno problems found')
        for p in probs:
            print('  -', p)
    return probs


if __name__ == '__main__':
    import argparse
    from mvkit.core import Project
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--draft', action='store_true', help='write storyboard.draft.json from keywords')
    a = ap.parse_args()
    P = Project(a.project)
    if a.draft:
        out = os.path.join(P.dir, 'storyboard.draft.json')
        json.dump(draft(P), open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('wrote', out)
    else:
        sys.exit(1 if lint(P) else 0)
