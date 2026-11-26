#!/usr/bin/env python
"""Assemble the final video: original frames everywhere, processed frames for the configured shots, encoded
at high quality with the source's frame rate and colour tags, original audio copied untouched. Then measure
how close untouched frames are to the source (they should be visually identical).

usage: render.py PROJECT [--out OUT.mp4] [--stages stab,clean] [--range A B] [--crf 12] [--no-check]
  --stages  per shot, the first stage folder that has a complete file is used (default stab, then clean)
  --range   render only global frames A..B (quick preview clip; audio trimmed to match)
"""
import os, sys, argparse, subprocess, re, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('--out', default=None)
ap.add_argument('--stages', default='stab,clean')
ap.add_argument('--range', nargs=2, type=int, default=None)
ap.add_argument('--crf', type=int, default=12)
ap.add_argument('--preset', default='slow')
ap.add_argument('--no-check', action='store_true')
A = ap.parse_args()
P = Project(A.project)
info = P.info
out = A.out or P.cfg.get('output') or os.path.splitext(P.video)[0] + '_clean.mp4'
if os.path.abspath(out) == os.path.abspath(P.video):
    sys.exit('refusing to overwrite the source video')

sub = {}
for sid, (a, b) in P.shots.items():
    n = b - a + 1
    for st in A.stages.split(','):
        path = P.yuv(st, sid)
        if os.path.exists(path) and os.path.getsize(path) == n * P.FS:
            sub[sid] = path
            break
print('using:', {s: os.path.basename(os.path.dirname(p)) for s, p in sorted(sub.items())})

fr = info['r_frame_rate']
pts = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time', '-of',
                      'csv=p=0', P.video], capture_output=True, text=True).stdout.split()
pts = sorted(float(x) for x in pts if x and x != 'N/A')
first, last = (A.range if A.range else (0, len(pts) - 1))

tags = []
for key, opt in (('color_primaries', '-color_primaries'), ('color_transfer', '-color_trc'), ('color_space', '-colorspace'),
                 ('color_range', '-color_range')):
    val = info.get(key)
    if val and val not in ('unknown', 'reserved'):
        tags += [opt, val]
bsf = []
if info.get('color_primaries') == 'bt709' or info.get('color_space') == 'bt709':
    # write the tags into the H.264 bitstream too (some players ignore container-only tags)
    bsf = ['-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag='
           + ('1' if info.get('color_range') == 'pc' else '0')]

tmp = out + '.part.mp4'
enc = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{P.W}x{P.H}', '-framerate', fr, '-i', '-']
if info.get('has_audio'):
    if A.range:
        fps_val = int(fr.split('/')[0]) / int(fr.split('/')[1])
        enc += ['-ss', f'{pts[first]:.6f}', '-t', f'{pts[last] - pts[first] + 1 / fps_val:.6f}']
    enc += ['-i', P.video, '-map', '0:v', '-map', '1:a', '-c:a', 'copy']
enc += ['-c:v', 'libx264', '-preset', A.preset, '-crf', str(A.crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p'] + tags + bsf
enc += ['-tag:v', 'avc1', '-movflags', '+faststart', '-shortest', tmp]
p = subprocess.Popen(enc, stdin=subprocess.PIPE)
files = {}
written = 0
for n, buf in enumerate(decode(P.video, first, last) if A.range else decode(P.video)):
    n += first
    so = P.shot_of(n)
    if so and so[0] in sub:
        sid, j = so
        f = files.setdefault(sid, open(sub[sid], 'rb'))
        f.seek(j * P.FS)
        buf = f.read(P.FS)
    p.stdin.write(buf)
    written += 1
p.stdin.close()
if p.wait() != 0:
    sys.exit('encode failed')
os.replace(tmp, out)
print(f'wrote {written} frames -> {out}')

if not A.no_check and not A.range:
    res = subprocess.run(['ffmpeg', '-v', 'info', '-i', out, '-i', P.video, '-lavfi',
                          '[0:v]setpts=N,split[a1][a2];[1:v]setpts=N,split[b1][b2];'
                          '[a1][b1]ssim=stats_file=-:[a2][b2]psnr=stats_file=' + P.p('review', 'psnr.log'),
                          '-f', 'null', '-'], capture_output=True, text=True)
    os.makedirs(P.p('review'), exist_ok=True)
    ss = [float(m) for m in re.findall(r'All:([0-9.]+)', res.stdout)]
    ps = [float(m) for m in re.findall(r'psnr_avg:([0-9.inf]+)', open(P.p('review', 'psnr.log')).read())] if os.path.exists(P.p('review', 'psnr.log')) else []
    changed = {a_ + j for s_, (a_, b_) in P.shots.items() if s_ in sub for j in range(b_ - a_ + 1)}
    for name, sel in (('untouched frames', lambda i: i not in changed), ('processed shots', lambda i: i in changed)):
        p_ = [x for i, x in enumerate(ps) if sel(i) and x != float('inf')]
        s_ = [x for i, x in enumerate(ss) if sel(i)]
        if p_ and s_:
            print(f'{name}: {len(s_)} frames  PSNR avg {np.mean(p_):.1f} dB  SSIM avg {np.mean(s_):.4f} min {min(s_):.4f}')
    print('(untouched frames should be ~45 dB / 0.995+, i.e. visually identical; frame count and audio are copied 1:1)')
    o = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,nb_frames,width,height,r_frame_rate',
                        '-of', 'compact=p=0', out], capture_output=True, text=True).stdout
    print(o.strip())
