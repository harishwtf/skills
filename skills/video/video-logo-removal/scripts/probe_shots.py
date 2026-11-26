#!/usr/bin/env python
"""Split a video into shots and make a labelled contact sheet (one frame per shot) so you can see which
shots show the branding. Writes PROJECT/shots_detected.json and PROJECT/review/shots.jpg.

usage: probe_shots.py PROJECT [--threshold 0.25] [--color U,V]
  --color U,V  also report, per shot, how much of the frame has this chroma (e.g. the uniform colour);
               shots with a lot of it are candidates for logos. U,V are centred chroma values (-128..127).
"""
import os, sys, json, argparse, subprocess, re, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode, Fabric

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('--threshold', type=float, default=0.25)
ap.add_argument('--color', default=None)
args = ap.parse_args()
P = Project(args.project)
info = P.info
num, den = map(int, info['r_frame_rate'].split('/'))
fps = num / den

# frame count + timestamps (packet pts are reliable for VFR-ish phone footage too)
pts = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time',
                      '-of', 'csv=p=0', P.video], capture_output=True, text=True).stdout.split()
pts = sorted(float(x) for x in pts if x and x != 'N/A')
N = len(pts)
# scene cuts on a small proxy
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', P.video, '-an', '-vf',
                      f"scale=270:-2,select='gt(scene,{args.threshold})',metadata=print:file=-", '-f', 'null', '-'],
                     capture_output=True, text=True).stdout
cut_t = [float(m) for m in re.findall(r'pts_time:([0-9.]+)', log)]
cuts = sorted({int(np.argmin([abs(p - t) for p in pts])) for t in cut_t} - {0})
bounds = [0] + cuts + [N]
shots = {i: [bounds[i], bounds[i + 1] - 1] for i in range(len(bounds) - 1)}

fab = None
if args.color:
    fab = Fabric([float(x) for x in args.color.split(',')])
pres = {}
if fab is not None:
    w, h = 136, 240
    for n_, buf in enumerate(decode(P.video, scale=(w, h))):
        a = np.frombuffer(buf, np.uint8)
        y = a[:w * h].reshape(h, w).astype(np.float32)
        u = cv2.resize(a[w * h:w * h * 5 // 4].reshape(h // 2, w // 2), (w, h)).astype(np.float32) - 128
        v = cv2.resize(a[w * h * 5 // 4:].reshape(h // 2, w // 2), (w, h)).astype(np.float32) - 128
        sid = next(s for s, (a_, b_) in shots.items() if a_ <= n_ <= b_)
        pres.setdefault(sid, []).append(float(fab.is_fabric(y, u, v, 0.5).mean()))

tiles = []
for sid, (a, b) in shots.items():
    mid = (a + b) // 2
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{pts[mid]:.4f}', '-i', P.video, '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], capture_output=True).stdout[:P.FS]
    img = cv2.cvtColor(np.frombuffer(raw, np.uint8).reshape(P.H * 3 // 2, P.W), cv2.COLOR_YUV2BGR_I420)
    tw = 300
    t = cv2.resize(img, (tw, int(tw * P.H / P.W)), interpolation=cv2.INTER_AREA)
    lab = f'#{sid} f{a}-{b} {a / fps:.1f}s'
    if sid in pres:
        lab += f' {100 * max(pres[sid]):.0f}%'
    cv2.rectangle(t, (0, 0), (tw, 22), (0, 0, 0), -1)
    cv2.putText(t, lab, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    tiles.append(t)
cols = 7
while len(tiles) % cols:
    tiles.append(np.zeros_like(tiles[0]))
os.makedirs(P.p('review'), exist_ok=True)
cv2.imwrite(P.p('review', 'shots.jpg'), np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]),
            [cv2.IMWRITE_JPEG_QUALITY, 90])
json.dump({str(k): v for k, v in shots.items()}, open(P.p('shots_detected.json'), 'w'), indent=1)
print(f'{N} frames, {fps:.3f} fps, {P.W}x{P.H}, {len(shots)} shots')
for sid, (a, b) in shots.items():
    extra = f'  colour max {100 * max(pres[sid]):.1f}% mean {100 * np.mean(pres[sid]):.1f}%' if sid in pres else ''
    print(f'shot {sid:2d}: frames {a}-{b} ({a / fps:.2f}-{(b + 1) / fps:.2f}s){extra}')
print('contact sheet:', P.p('review', 'shots.jpg'))
