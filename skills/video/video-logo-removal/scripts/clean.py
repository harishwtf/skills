#!/usr/bin/env python
"""Remove the tracked logos from every frame of the configured shots.

usage: clean.py PROJECT [shot ...] [--in STAGE] [--out STAGE]
  --in  STAGE  start from an earlier stage's frames (e.g. 'stab') instead of the original video; use this to
               add a second pass (another logo) on top of approved work without redoing it
  --out STAGE  output folder name (default 'clean'); writes PROJECT/STAGE/shotNN.yuv (raw yuv420p frames)
"""
import os, sys, argparse, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode, planes, caption_mask, fix_region, fabric_for, leftovers, dil
from holes import logo_hole, unblend

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('shots', nargs='*', type=int)
ap.add_argument('--in', dest='src', default=None)
ap.add_argument('--out', default='clean')
ap.add_argument('--objects', default=None, help='comma-separated object ids to process (default: all logo objects)')
args = ap.parse_args()
P = Project(args.project)
only_objs = {int(x) for x in args.objects.split(',')} if args.objects else None
os.makedirs(P.p(args.out), exist_ok=True)
fab_cache = {}

for sid in (args.shots or sorted(P.shots)):
    a, b = P.shots[sid]
    n = b - a + 1
    logos = [o for o in P.objs_with_role(sid, 'logo') if not only_objs or o in only_objs]
    protects = P.objs_with_role(sid, 'protect')
    if args.src:
        src = open(P.yuv(args.src, sid), 'rb')
        frames = (src.read(P.FS) for _ in range(n))
    else:
        frames = decode(P.video, a, b)
    out = open(P.yuv(args.out, sid), 'wb')
    stats = {'frames': 0, 'fills': 0, 'dropped': 0, 'cleanup': 0}
    for j, buf in enumerate(frames):
        fr, Y, U, V = planes(buf, P.W, P.H)
        masks = {o: P.mask(sid, o, j) for o in logos}
        masks = {o: m for o, m in masks.items() if m is not None}
        if masks:
            cap = caption_mask(P, Y, U, V)
            prot_all = np.zeros((P.H, P.W), bool)
            for o in protects:
                m = P.mask(sid, o, j)
                if m is not None:
                    prot_all |= m
            for oid, obj in masks.items():
                sp = P.spec(sid, oid, j)
                mode = sp.get('mode', 'flat')
                fab = fabric_for(P, sid, oid, Y, U, V, obj, fab_cache)
                if fab is None:
                    print(f'shot {sid} obj {oid}: could not estimate the fabric colour; set "fabric": [u, v] in config',
                          file=sys.stderr)
                    continue
                prot = prot_all
                if sp.get('protect') is not None:
                    prot = np.zeros((P.H, P.W), bool)
                    for o in sp['protect']:
                        m = P.mask(sid, int(o), j)
                        if m is not None:
                            prot |= m
                if mode == 'unblend':
                    forbid = dil(cap, P.px(12)) | dil(prot, P.px(8))
                    core = unblend(P, Y, U, V, obj & ~forbid, fab, forbid=forbid)
                    if core.sum() > 50:
                        fix_region(P, Y, U, V, dil(core, P.px(5)) & ~prot, cap)
                    stats['fills'] += 1
                    continue
                surf = None
                if isinstance(sp.get('surface'), int):
                    surf = P.mask(sid, sp['surface'], j, respect_valid=False)
                res = logo_hole(P, Y, U, V, obj, fab, mode=mode, surface=surf, protect=prot, spec=sp)
                if res is None:
                    stats['dropped'] += 1
                    continue
                hole, clip = res
                fix_region(P, Y, U, V, hole, cap, clip=clip, bg=sp.get('bg', 'lama'),
                           max_side=1024 if clip is None else 1600)
                stats['fills'] += 1
            # cleanup: letter fragments that survived (light blobs enclosed by fabric near a tracked logo)
            hw = (P.W // 2, P.H // 2)
            for oid, obj in masks.items():
                if P.spec(sid, oid, j).get('cleanup', True) is False or (sid, oid) not in fab_cache or fab_cache[(sid, oid)] is None:
                    continue
                zone = dil(cv2.resize(obj.astype(np.uint8), hw, interpolation=cv2.INTER_NEAREST) > 0, P.px(30))
                res = leftovers(P, Y, U, V, zone, fab_cache[(sid, oid)])
                if res.sum() >= 6:
                    full = cv2.resize(res.astype(np.uint8), (P.W, P.H), interpolation=cv2.INTER_NEAREST) > 0
                    fix_region(P, Y, U, V, dil(full, P.px(10)) & ~dil(prot_all, P.px(6)), cap)
                    stats['cleanup'] += 1
        out.write(fr.tobytes())
        stats['frames'] += 1
    out.close()
    if stats['frames'] != n:
        sys.exit(f'shot {sid}: expected {n} frames, got {stats["frames"]}')
    print(f'shot {sid}: {stats["frames"]} frames, {stats["fills"]} object fills, {stats["cleanup"]} cleanup passes, '
          f'{stats["dropped"]} masks dropped (track drifted off the fabric)', flush=True)
