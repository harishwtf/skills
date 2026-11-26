#!/usr/bin/env python
"""Visual review tools. All write a PNG you then look at (Read the image).

  grid     PROJECT --shot S --frames 0,40 [--crop x0,y0,x1,y1] [--step 50] [--width 1000] [-o out.png]
           half-res frames with a labelled coordinate grid -> pick prompt boxes/points (half-res coords)
  overlay  PROJECT --shot S --frames 0,10,20 [--crop x0,y0,x1,y1] [--objects 1,2] [--width 300]
           tracked masks drawn on the half-res frames (crop in half-res coords) -> check tracking
  compare  PROJECT --shot S --frames 0,5,10 --crop x0,y0,x1,y1 [--stages clean,stab] [--width 300]
           original vs processed stages at FULL resolution (crop in full-res coords) -> check fills.
           --frames a:b:step gives consecutive frames (look for flicker / pops between neighbours)
  videos   --a ORIG.mp4 --b OUT.mp4 --frames 1104,1110 --crop x0,y0,x1,y1 [--width 300]
           two videos at the same global frame numbers (full-res crop) -> check the final render
"""
import os, sys, argparse, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

COLORS = [(0, 0, 255), (255, 0, 255), (255, 128, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255), (0, 128, 255),
          (255, 255, 0), (128, 255, 0), (255, 0, 128)]


def frames_arg(s):
    if ':' in s:
        a, b, *st = [int(x) for x in s.split(':')]
        return list(range(a, b + 1, st[0] if st else 1))
    return [int(x) for x in s.split(',')]


def label(img, text):
    cv2.rectangle(img, (0, 0), (min(img.shape[1], 12 + 9 * len(text)), 20), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    return img


def tile(rows_of_imgs, out):
    rows = []
    for r in rows_of_imgs:
        h = max(i.shape[0] for i in r)
        rows.append(np.hstack([cv2.copyMakeBorder(i, 0, h - i.shape[0] + 3, 0, 3, cv2.BORDER_CONSTANT, value=(255, 0, 255))
                               for i in r]))
    w = max(r.shape[1] for r in rows)
    img = np.vstack([cv2.copyMakeBorder(r, 0, 0, 0, w - r.shape[1], cv2.BORDER_CONSTANT) for r in rows])
    cv2.imwrite(out, img)
    print(out)


def resize_w(img, w):
    return cv2.resize(img, (w, max(1, int(img.shape[0] * w / img.shape[1]))), interpolation=cv2.INTER_AREA)


def grab(video, frames, W, H):
    a, b = min(frames), max(frames)
    from vlr import decode
    out = {}
    for n, buf in zip(range(a, b + 1), decode(video, a, b)):
        if n in frames:
            out[n] = buf
    return out


ap = argparse.ArgumentParser()
ap.add_argument('cmd', choices=['grid', 'overlay', 'compare', 'videos'])
ap.add_argument('project', nargs='?')
ap.add_argument('--shot', type=int)
ap.add_argument('--frames', required=True)
ap.add_argument('--crop', default=None)
ap.add_argument('--step', type=int, default=50)
ap.add_argument('--objects', default=None)
ap.add_argument('--stages', default='clean')
ap.add_argument('--width', type=int, default=None)
ap.add_argument('--a'); ap.add_argument('--b')
ap.add_argument('-o', '--out', default=None)
A = ap.parse_args()
frames = frames_arg(A.frames)
crop = [int(x) for x in A.crop.split(',')] if A.crop else None

if A.cmd == 'videos':
    from vlr import probe, to_bgr
    info = probe(A.a); W, H = int(info['width']), int(info['height'])
    rows = []
    for name, vid in (('orig', A.a), ('out', A.b)):
        bufs = grab(vid, frames, W, H)
        row = []
        for n in frames:
            img = to_bgr(bufs[n], W, H)
            if crop: img = img[crop[1]:crop[3], crop[0]:crop[2]]
            row.append(label(resize_w(img, A.width or 300), f'{name} {n}'))
        rows.append(row)
    tile(rows, A.out or 'compare_videos.png')
    sys.exit()

from vlr import Project, to_bgr
P = Project(A.project)
sid = A.shot
rdir = P.p('review'); os.makedirs(rdir, exist_ok=True)

if A.cmd == 'grid':
    row = []
    for j in frames:
        img = cv2.imread(os.path.join(P.frames_dir(sid), f'{j:05d}.jpg'))
        x0, y0, x1, y1 = crop or (0, 0, img.shape[1], img.shape[0])
        img = img[y0:y1, x0:x1].copy()
        sc = (A.width or min(1000, (x1 - x0) * 2)) / (x1 - x0)
        img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
        st = A.step
        for gx in range((x0 // st + 1) * st, x1, st):
            X = int((gx - x0) * sc); cv2.line(img, (X, 0), (X, img.shape[0]), (0, 255, 255), 1)
            cv2.putText(img, str(gx), (X + 2, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        for gy in range((y0 // st + 1) * st, y1, st):
            Yy = int((gy - y0) * sc); cv2.line(img, (0, Yy), (img.shape[1], Yy), (0, 255, 255), 1)
            cv2.putText(img, str(gy), (2, Yy - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        row.append(label(img, f'shot {sid} frame {j}'))
    tile([row], A.out or os.path.join(rdir, f'grid_s{sid}.png'))

elif A.cmd == 'overlay':
    objs = [int(x) for x in A.objects.split(',')] if A.objects else sorted(P.objects.get(sid, {}))
    row = []
    for j in frames:
        img = cv2.imread(os.path.join(P.frames_dir(sid), f'{j:05d}.jpg'))
        for i, oid in enumerate(objs):
            m = P.mask(sid, oid, j, full=False)
            if m is None: continue
            c = COLORS[i % len(COLORS)]
            ov = img.copy(); ov[m] = c
            img = cv2.addWeighted(img, 0.6, ov, 0.4, 0)
            cn, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(img, cn, -1, c, 2)
        if crop: img = img[crop[1]:crop[3], crop[0]:crop[2]]
        row.append(label(resize_w(img, A.width or 300), f'{j}'))
    legend = ' '.join(f'obj{o}={["red","magenta","blue","yellow","green","white","orange","cyan"][i % 8]}' for i, o in enumerate(objs))
    print(legend)
    rows = [row[i:i + 8] for i in range(0, len(row), 8)]
    tile(rows, A.out or os.path.join(rdir, f'overlay_s{sid}.png'))

elif A.cmd == 'compare':
    a, b = P.shots[sid]
    stages = [s for s in A.stages.split(',') if s]
    bufs = grab(P.video, [a + j for j in frames], P.W, P.H)
    cols = []
    for j in frames:
        ims = [('orig', to_bgr(bufs[a + j], P.W, P.H))]
        for s in stages:
            with open(P.yuv(s, sid), 'rb') as f:
                f.seek(j * P.FS); ims.append((s, to_bgr(f.read(P.FS), P.W, P.H)))
        col = []
        for name, img in ims:
            if crop: img = img[crop[1]:crop[3], crop[0]:crop[2]]
            col.append(label(resize_w(img, A.width or 300), f'{name} {j}'))
        cols.append(col)
    rows = [[c[i] for c in cols] for i in range(len(cols[0]))]
    tile(rows, A.out or os.path.join(rdir, f'compare_s{sid}.png'))
