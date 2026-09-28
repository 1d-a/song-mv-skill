"""Lyric -> per-character singing times.

python -m mvkit.align PROJECT [--model small]
reads project.json (audio, lyrics_file), writes lyrics.json and prints lines with low confidence.
"""
import argparse
import json
import os
import re

import numpy as np
from pypinyin import lazy_pinyin

from mvkit.core import audio_duration, load_mono

KEEP = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')


def parse_lyrics(path):
    """-> list of dict(text, section). [Section] tags, blank lines and punctuation are dropped."""
    lines, section = [], ''
    for raw in open(path, encoding='utf-8-sig'):
        s = raw.strip()
        if not s:
            continue
        m = re.fullmatch(r'[\[【(（](.*?)[\]】)）]', s)
        if m:
            section = m.group(1)
            continue
        txt = ''.join(KEEP.findall(s))
        if txt:
            lines.append(dict(text=txt, section=section))
    return lines


def transcribe(model, audio, prompt, offset=0.0, dur=None):
    """-> list of (char, t_start, t_end) from whisper word timestamps."""
    sr = 16000
    a = load_mono(audio, sr)
    a = a[int(offset * sr): int((offset + dur) * sr) if dur else None]
    segs, _ = model.transcribe(a, language='zh', word_timestamps=True, initial_prompt=prompt[:180],
                               condition_on_previous_text=False, vad_filter=False, beam_size=5)
    out = []
    for s in segs:
        for w in s.words or []:
            cs = KEEP.findall(w.word)
            if not cs:
                continue
            d = (w.end - w.start) / len(cs)
            out.extend((c, offset + w.start + k * d, offset + w.start + (k + 1) * d) for k, c in enumerate(cs))
    return out


def _py(c):
    p = lazy_pinyin(c)[0]
    return p.rstrip('12345')


def align(lyr_chars, rec):
    """global alignment; returns index into rec for each lyric char (or -1)."""
    n, m = len(lyr_chars), len(rec)
    lp = [_py(c) for c in lyr_chars]
    rp = [_py(c) for c, _, _ in rec]
    GL, GR = 1.0, 0.55  # skipping a lyric char / skipping a recognised (hallucinated) char
    D = np.zeros((n + 1, m + 1), np.float32)
    D[1:, 0] = np.arange(1, n + 1) * GL
    D[0, 1:] = np.arange(1, m + 1) * GR
    B = np.zeros((n + 1, m + 1), np.int8)
    for i in range(1, n + 1):
        li, pi = lyr_chars[i - 1], lp[i - 1]
        sub = np.array([0.0 if li == rc[0] else (0.25 if pi == rp[j] else 1.2) for j, rc in enumerate(rec)], np.float32)
        diag = D[i - 1, :-1] + sub
        up = D[i - 1, 1:] + GL
        row = np.minimum(diag, up)
        br = np.where(diag <= up, 0, 1)
        # left moves (skip rec) need a sequential scan
        Di = D[i]
        Bi = B[i]
        Di[0] = D[i - 1, 0] + GL
        Bi[0] = 1
        for j in range(1, m + 1):
            v = row[j - 1]
            b = br[j - 1]
            lv = Di[j - 1] + GR
            if lv < v:
                v, b = lv, 2
            Di[j] = v
            Bi[j] = b
    res = [-1] * n
    i, j = n, m
    while i > 0 and j > 0:
        b = B[i, j]
        if b == 0:
            if lyr_chars[i - 1] == rec[j - 1][0] or lp[i - 1] == rp[j - 1]:
                res[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif b == 1:
            i -= 1
        else:
            j -= 1
    return res


def assign_times(chars, rec, idx, dur):
    t = np.full(len(chars), np.nan)
    e = np.full(len(chars), np.nan)
    for k, j in enumerate(idx):
        if j >= 0:
            t[k], e[k] = rec[j][1], rec[j][2]
    known = np.where(~np.isnan(t))[0]
    if len(known) == 0:
        raise SystemExit('whisper recognised nothing usable; check the audio / lyrics file')
    t = np.interp(np.arange(len(chars)), known, t[known])
    e = np.where(np.isnan(e), t + 0.3, e)
    for k in range(1, len(t)):  # monotonic, >=60ms apart
        t[k] = max(t[k], t[k - 1] + 0.06)
    return np.minimum(t, dur - 0.1), e


def run(pdir, model_name='small'):
    from faster_whisper import WhisperModel
    cfg = json.load(open(os.path.join(pdir, 'project.json'), encoding='utf-8'))
    audio = os.path.join(pdir, cfg['audio'])
    dur = audio_duration(audio)
    lines = parse_lyrics(os.path.join(pdir, cfg['lyrics_file']))
    chars = [c for ln in lines for c in ln['text']]
    owner = [i for i, ln in enumerate(lines) for _ in ln['text']]
    model = WhisperModel(model_name, device='cpu', compute_type='int8')
    print('transcribing whole song ...', flush=True)
    rec = transcribe(model, audio, '以下是普通话歌曲的歌词。')
    idx = align(chars, rec)
    t, e = assign_times(chars, rec, idx, dur)
    matched = np.array([j >= 0 for j in idx])
    # refine: re-transcribe windows around lines with poor matches
    for li, ln in enumerate(lines):
        ks = [k for k, o in enumerate(owner) if o == li]
        if matched[ks].mean() >= 0.5:
            continue
        a = max(0.0, t[ks[0]] - 2.5)
        b = min(dur, t[ks[-1]] + 3.0)
        prev_k = [k for k in range(ks[0]) if matched[k]]
        next_k = [k for k in range(ks[-1] + 1, len(chars)) if matched[k]]
        if prev_k:
            a = max(a, t[prev_k[-1]] - 0.2)
        if next_k:
            b = min(max(b, a + 4), t[next_k[0]] + 0.2)
        sub = transcribe(model, audio, ln['text'], a, b - a)
        if not sub:
            continue
        sidx = align([chars[k] for k in ks], sub)
        if sum(j >= 0 for j in sidx) <= matched[ks].sum():
            continue
        st, se = assign_times([chars[k] for k in ks], sub, sidx, dur)
        for q, k in enumerate(ks):
            t[k], e[k] = st[q], se[q]
            matched[k] = sidx[q] >= 0
        print(f'  refined line {li + 1} {ln["text"]} in {a:.1f}-{b:.1f}s', flush=True)
    for k in range(1, len(t)):
        t[k] = max(t[k], t[k - 1] + 0.06)
    for li, ln in enumerate(lines):  # whisper stretches a line's first char back into the preceding silence
        ks = [k for k, o in enumerate(owner) if o == li]
        if len(ks) > 2:
            med = float(np.median(np.diff(t[ks[1:]])))
            t[ks[0]] = max(t[ks[0]], t[ks[1]] - 1.2 * med)
    out = []
    for li, ln in enumerate(lines):
        ks = [k for k, o in enumerate(owner) if o == li]
        times = [round(float(t[k]), 2) for k in ks]
        nxt = t[ks[-1] + 1] if ks[-1] + 1 < len(t) else dur
        end = float(min(max(e[ks[-1]], times[-1] + 0.3), nxt - 0.05, times[-1] + 1.5))
        out.append(dict(text=ln['text'], section=ln['section'], times=times, end=round(end, 2),
                        conf=round(float(matched[ks].mean()), 2)))
    json.dump(dict(lines=out), open(os.path.join(pdir, 'lyrics.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for i, ln in enumerate(out):
        flag = '  <-- CHECK' if ln['conf'] < 0.5 else ''
        print(f"L{i + 1:<3} {ln['times'][0]:7.2f}-{ln['end']:7.2f} conf={ln['conf']:.2f} {ln['text']}{flag}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--model', default='small')
    a = ap.parse_args()
    run(a.project, a.model)
