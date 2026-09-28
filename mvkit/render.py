"""Render a song video (or a time range / still frames) in one style.

python -m mvkit.render PROJECT --style ink|crayon|paper [--start S --dur D] [--jobs N] [--out FILE]
python -m mvkit.render PROJECT --style ink --stills 12.5,20,31 --sheet out.png     (quick look, no video)
Chunks are cached in PROJECT/build/<style>/ so an interrupted render resumes.
"""
import argparse
import glob
import hashlib
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from mvkit.core import FPS, Project
from mvkit.styles import STYLES, load_style, out_frame

CHUNK = 300  # frames


def ffprobe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'default=nw=1', path],
                       capture_output=True, text=True)
    info = {}
    for line in r.stdout.splitlines():
        k, _, v = line.partition('=')
        info.setdefault(k, []).append(v)
    return info


def chunk_ok(path, nframes):
    if not os.path.exists(path):
        return False
    d = ffprobe(path).get('duration', ['0'])
    try:
        return abs(float(d[-1]) - nframes / FPS) < 0.2
    except ValueError:
        return False


def encode(frames_iter, path, size):
    tmp = path + '.part.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for fr in frames_iter:
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit(f'ffmpeg failed for {path}')
    os.replace(tmp, path)


def build_dir(P, style):
    h = hashlib.sha1()
    root = os.path.dirname(os.path.abspath(__file__))
    for f in ['project.json', 'lyrics.json', 'storyboard.json', 'features.npz']:
        fp = os.path.join(P.dir, f)
        if os.path.exists(fp):
            h.update(open(fp, 'rb').read())
    for f in sorted(glob.glob(os.path.join(root, '*.py')) + glob.glob(os.path.join(root, 'styles', '*.py'))):
        h.update(open(f, 'rb').read())
    return os.path.join(P.dir, 'build', style, h.hexdigest()[:10])


def worker(pdir, style, chunks, f0, f1):
    P = Project(pdir)
    S = load_style(style, P)
    bdir = build_dir(P, style)
    for c in chunks:
        a, b = max(f0, c * CHUNK), min(f1, (c + 1) * CHUNK)
        path = os.path.join(bdir, f'chunk_{c:04d}_{a}_{b}.mp4')
        if chunk_ok(path, b - a):
            continue
        t0 = time.time()
        encode((out_frame(S, fi / FPS) for fi in range(a, b)), path, (P.OW, P.OH))
        print(f'[{style}] chunk {c} frames {a}-{b} done in {time.time() - t0:.0f}s', flush=True)


def auto_jobs(mem_per_job=1.5, reserve=1.0, cap=8):
    """parallel workers that fit this machine: usable CPUs (affinity + cgroup quota), one core kept free on 4+,
    and MemAvailable minus `reserve` GB divided by ~`mem_per_job` GB per worker (style ~0.9 GB + its x264 encoder)"""
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    try:
        q, per = open('/sys/fs/cgroup/cpu.max').read().split()
        if q != 'max':
            cpus = min(cpus, max(1, int(int(q) / int(per))))
    except (OSError, ValueError):
        pass
    mem = None
    try:
        mem = next(int(l.split()[1]) / 2 ** 20 for l in open('/proc/meminfo') if l.startswith('MemAvailable:'))
    except (OSError, StopIteration):
        pass
    by_cpu = cpus - 1 if cpus >= 4 else cpus
    by_mem = by_cpu if mem is None else int((mem - reserve) // mem_per_job)
    jobs = max(1, min(by_cpu, by_mem, cap))
    print(f'[render] {cpus} CPUs, ' + ('unknown' if mem is None else f'{mem:.1f} GB') + f' RAM available -> --jobs {jobs}')
    return jobs


def render(pdir, style, start=0.0, dur=None, jobs=None, out=None):
    P = Project(pdir)
    jobs = jobs or auto_jobs()
    dur = P.dur - start if dur is None else min(dur, P.dur - start)
    f0, f1 = int(round(start * FPS)), int(round((start + dur) * FPS))
    bdir = build_dir(P, style)
    os.makedirs(bdir, exist_ok=True)
    chunks = list(range(f0 // CHUNK, (f1 - 1) // CHUNK + 1))
    groups = [chunks[i::jobs] for i in range(jobs) if chunks[i::jobs]]
    procs = [subprocess.Popen([sys.executable, '-m', 'mvkit.render', pdir, '--style', style, '--worker', ','.join(map(str, g)), '--range', f'{f0},{f1}'],
                              cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) for g in groups]
    if any(p.wait() for p in procs):
        raise SystemExit('a render worker failed; rerun the same command to resume')
    files = [os.path.join(bdir, f'chunk_{c:04d}_{max(f0, c * CHUNK)}_{min(f1, (c + 1) * CHUNK)}.mp4') for c in chunks]
    lst = os.path.join(bdir, 'concat.txt')
    with open(lst, 'w') as f:
        f.writelines(f"file '{x}'\n" for x in files)
    name = STYLES[style][1]
    out = out or os.path.join(P.dir, 'out', f'{P.title}_{name}' + ('' if start == 0 and abs(dur - P.dur) < 0.1 else f'_{start:g}s+{dur:g}s') + '.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    afade = f'afade=t=in:st=0:d=0.3,afade=t=out:st={max(0, dur - 1.2):.2f}:d=1.2' if start > 0 or dur < P.dur - 0.1 else f'afade=t=out:st={max(0, dur - 0.6):.2f}:d=0.6'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', P.audio,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-af', afade, '-shortest', '-movflags', '+faststart', out], check=True)
    info = ffprobe(out)
    ok = 'video' in info.get('codec_type', []) and 'audio' in info.get('codec_type', []) and info.get('width') == [str(P.OW)] and info.get('height') == [str(P.OH)]
    print(f"{out}\n  duration={float(info['duration'][-1]):.2f}s  size={P.OW}x{P.OH}  streams={info.get('codec_type')}  {'OK' if ok else 'CHECK FAILED'}")
    if not ok:
        raise SystemExit(1)
    return out


def stills(pdir, style, times, sheet=None, cols=4, S=None, P=None, label=True):
    P = P or Project(pdir)
    S = S or load_style(style, P)
    ims = [Image.fromarray(np.clip(out_frame(S, t), 0, 255).astype(np.uint8)) for t in times]
    if sheet:
        tw, th = 360, 360 * P.OH // P.OW
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new('RGB', (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (24, 24, 28))
        for k, im in enumerate(ims):
            sh.paste(im.resize((tw, th), Image.LANCZOS), (12 + (k % cols) * (tw + 12), 12 + (k // cols) * (th + 12)))
        os.makedirs(os.path.dirname(os.path.abspath(sheet)), exist_ok=True)
        sh.save(sheet)
        print('wrote', sheet)
    return ims


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--style', required=True, choices=list(STYLES))
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--dur', type=float)
    ap.add_argument('--jobs', type=int, help='parallel workers (default: auto from CPUs and free RAM)')
    ap.add_argument('--out')
    ap.add_argument('--stills', help='comma separated seconds')
    ap.add_argument('--sheet', help='contact sheet png for --stills')
    ap.add_argument('--worker', help=argparse.SUPPRESS)
    ap.add_argument('--range', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.worker:
        f0, f1 = map(int, a.range.split(','))
        worker(a.project, a.style, [int(x) for x in a.worker.split(',')], f0, f1)
    elif a.stills:
        stills(a.project, a.style, [float(x) for x in a.stills.split(',')], a.sheet or os.path.join(a.project, 'out', f'stills_{a.style}.png'))
    else:
        render(a.project, a.style, a.start, a.dur, a.jobs, a.out)
