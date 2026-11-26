#!/usr/bin/env python
"""Track every configured object (logos, surfaces, protected things like hands) through its shot with
SAM 2.1, propagating forward and backward from all prompted frames.

usage: track.py PROJECT [shot ...] [--objects 1,2]
Prompts (config.json, half-res coords): [frame, [x0,y0,x1,y1]] or [frame, [x0,y0,x1,y1], [[x,y,1|0], ...]]
(1 = point on the object, 0 = point that is NOT the object). Prompt the same object on several frames
(start, middle, end, and wherever it changes shape) - this is what keeps tracks from drifting.
Masks: PROJECT/masks/shotNN/objK/FFFFF.png (half-res, 0-255 probability).
"""
import os, sys, glob, argparse, shutil, numpy as np, cv2
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, MODELS, device
import torch
from sam2.build_sam import build_sam2_video_predictor

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('shots', nargs='*', type=int)
ap.add_argument('--objects', default=None)
args = ap.parse_args()
P = Project(args.project)
only = {int(x) for x in args.objects.split(',')} if args.objects else None
pred = build_sam2_video_predictor('configs/sam2.1/sam2.1_hiera_b+.yaml', os.path.join(MODELS, 'sam2.1_hiera_base_plus.pt'),
                                  device=device())
for sid in (args.shots or sorted(P.objects)):
    objs = {o: sp for o, sp in P.objects.get(sid, {}).items() if sp.get('prompts') and (not only or o in only)}
    if not objs:
        continue
    fdir = P.frames_dir(sid)
    n = len(glob.glob(os.path.join(fdir, '*.jpg')))
    if n == 0:
        sys.exit(f'shot {sid}: no frames; run extract_frames.py first')
    with torch.inference_mode():
        st = pred.init_state(video_path=fdir, offload_video_to_cpu=True)
        for oid, sp in objs.items():
            for ent in sp['prompts']:
                f, box = ent[0], ent[1]
                kw = {}
                if len(ent) > 2 and ent[2]:
                    kw['points'] = np.array([[x, y] for x, y, _ in ent[2]], np.float32)
                    kw['labels'] = np.array([l for _, _, l in ent[2]], np.int32)
                pred.add_new_points_or_box(inference_state=st, frame_idx=int(f), obj_id=int(oid),
                                           box=np.array(box, np.float32) if box else None, **kw)
        acc = {}
        for rev in (False, True):
            for fi, oids, logits in pred.propagate_in_video(st, reverse=rev):
                lg = logits[:, 0].float().cpu().numpy()
                for k, oid in enumerate(oids):
                    key = (fi, int(oid))
                    acc[key] = lg[k] if key not in acc else np.maximum(acc[key], lg[k])
        pred.reset_state(st)
    for oid in objs:
        d = P.p('masks', f'shot{sid:02d}', f'obj{oid}')
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    for (fi, oid), lg in acc.items():
        p = (1 / (1 + np.exp(-np.clip(lg, -20, 20))) * 255).astype(np.uint8)
        cv2.imwrite(P.p('masks', f'shot{sid:02d}', f'obj{oid}', f'{fi:05d}.png'), p)
    print(f'shot {sid}: tracked objects {sorted(objs)} over {n} frames', flush=True)
