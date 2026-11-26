#!/usr/bin/env python
"""Automated checks. Every flag still needs a look by eye (review.py) - the detectors are deliberately
over-sensitive, and some real problems (smudges, wrong colours) are only visible to a human.

  scan   PROJECT [shots] [--stage stab]   leftover letter fragments near each tracked logo, per frame;
                                          saves crops of the worst frames to PROJECT/review/scan_sNN.png
  wobble PROJECT [shots] [--stage stab]   motion-compensated flicker of the filled areas vs. the real fabric
                                          (ratio ~1 = moves like fabric; >1.5 = visibly shimmers on playback)
  sweep  PROJECT --video OUT.mp4 [--color U,V ...]
                                          whole-video sweep for light marks on the uniform/bag colours, INCLUDING
                                          shots you did not process (this is how missed shots are found);
                                          saves one review sheet per 8 flagged runs to PROJECT/review/sweep_*.png
"""
import os, sys, argparse, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode, planes, Fabric, estimate_fabric, leftovers, dil, to_bgr

ap = argparse.ArgumentParser()
ap.add_argument('cmd', choices=['scan', 'wobble', 'sweep'])
ap.add_argument('project')
ap.add_argument('shots', nargs='*', type=int)
ap.add_argument('--stage', default='stab')
ap.add_argument('--video', default=None)
ap.add_argument('--color', action='append', default=[])
A = ap.parse_args()
P = Project(A.project)
os.makedirs(P.p('review'), exist_ok=True)
hw = (P.W // 2, P.H // 2)


def object_fabrics():
    """fabric colour per (shot, logo object): from config, or estimated on the original frame"""
    out = {}
    for sid in sorted(P.objects):
        a, b = P.shots[sid]
        for oid in P.objs_with_role(sid, 'logo'):
            f = P.spec(sid, oid).get('fabric', 'auto')
            if isinstance(f, (list, tuple)):
                out[(sid, oid)] = Fabric(f); continue
            for j in range(b - a + 1):
                m = P.mask(sid, oid, j)
                if m is None:
                    continue
                buf = next(decode(P.video, a + j, a + j))
                _, Y, U, V = planes(buf, P.W, P.H)
                out[(sid, oid)] = estimate_fabric(Y, U, V, m, P.k)
                break
    return {k: v for k, v in out.items() if v is not None}


if A.cmd == 'scan':
    fabs = object_fabrics()
    for sid in (A.shots or sorted(P.objects)):
        a, b = P.shots[sid]
        n = b - a + 1
        logos = [o for o in P.objs_with_role(sid, 'logo') if (sid, o) in fabs]
        res = []
        with open(P.yuv(A.stage, sid), 'rb') as f:
            for j in range(n):
                buf = f.read(P.FS)
                _, Y, U, V = planes(buf, P.W, P.H, copy=False)
                tot = np.zeros((P.H // 2, P.W // 2), bool)
                for oid in logos:
                    m = P.mask(sid, oid, j, full=False)
                    if m is None:
                        continue
                    tot |= leftovers(P, Y, U, V, dil(m, P.px(30)), fabs[(sid, oid)])
                res.append((j, int(tot.sum()), tot if tot.any() else None, buf if tot.sum() >= 25 else None))
        flagged = [r for r in res if r[1] >= 25]
        worst = sorted(res, key=lambda r: -r[1])[:6]
        print(f'shot {sid}: {n} frames, {len(flagged)} flagged (>=25 px at half-res), worst ' +
              ', '.join(f'f{j}:{c}' for j, c, _, _ in worst if c))
        tiles = []
        for j, c, d, buf in sorted(flagged, key=lambda r: -r[1])[:8]:
            ys, xs = np.nonzero(d); cy, cx = int(ys.mean()) * 2, int(xs.mean()) * 2
            img = to_bgr(buf, P.W, P.H)
            s = P.px(400)
            y0, x0 = min(max(0, cy - s // 2), P.H - s), min(max(0, cx - s // 2), P.W - s)
            crop = img[y0:y0 + s, x0:x0 + s].copy()
            dd = cv2.resize(d.astype(np.uint8), (P.W, P.H), interpolation=cv2.INTER_NEAREST)[y0:y0 + s, x0:x0 + s] > 0
            mark = crop.copy(); mark[dd] = (0, 0, 255)
            t = cv2.resize(np.hstack([crop, mark]), (600, 300), interpolation=cv2.INTER_AREA)
            cv2.putText(t, f'shot {sid} f{j} {c}px', (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            tiles.append(t)
        if tiles:
            while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
            out = P.p('review', f'scan_s{sid:02d}.png')
            cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)]))
            print('  ->', out)

elif A.cmd == 'wobble':
    q = 4; fw, fh = P.W // q, P.H // q
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    gx, gy = np.meshgrid(np.arange(fw, dtype=np.float32), np.arange(fh, dtype=np.float32))
    warp = lambda img, fl: cv2.remap(img, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    yq = lambda buf: cv2.resize(np.frombuffer(buf, np.uint8)[:P.W * P.H].reshape(P.H, P.W), (fw, fh), interpolation=cv2.INTER_AREA)
    for sid in (A.shots or sorted(P.objects)):
        a, b = P.shots[sid]
        rows, prev = [], None
        with open(P.yuv(A.stage, sid), 'rb') as f:
            for j, ob in enumerate(decode(P.video, a, b)):
                o = yq(ob).astype(np.float32); c = yq(f.read(P.FS)).astype(np.float32)
                ch = cv2.morphologyEx((np.abs(c - o) > 2).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
                if prev is not None:
                    po, pc, pch = prev
                    fwd = dis.calc(o.astype(np.uint8), po.astype(np.uint8), None)
                    bwd = dis.calc(po.astype(np.uint8), o.astype(np.uint8), None)
                    ok = np.linalg.norm(fwd + warp(bwd, fwd), axis=2) < 1.0
                    reg = (cv2.erode((ch | pch).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ok
                    if reg.sum() > 150:
                        ec = float(np.abs(c - warp(pc, fwd))[reg].mean()); eo = float(np.abs(o - warp(po, fwd))[reg].mean())
                        rows.append((j, ec / max(eo, 0.7), ec, eo))
                prev = (o, c, ch)
        if not rows:
            print(f'shot {sid}: no filled frame pairs'); continue
        r = np.array([x[1] for x in rows])
        worst = sorted(rows, key=lambda x: -x[1])[:6]
        print(f'shot {sid}: pairs={len(rows)} wobble median={np.median(r):.2f} p90={np.percentile(r, 90):.2f} '
              f'pairs>1.5={int((r > 1.5).sum())} worst=' + ', '.join(f'f{j}:{q_:.2f}' for j, q_, _, _ in worst))

elif A.cmd == 'sweep':
    video = A.video or P.cfg.get('output')
    fabs = [Fabric([float(x) for x in c.split(',')]) for c in A.color]
    if not fabs:
        uniq = []
        for f in object_fabrics().values():
            if all(np.hypot(f.du * f.mag - g.du * g.mag, f.dv * f.mag - g.dv * g.mag) > 6 for g in uniq):
                uniq.append(f)
        fabs = uniq
    print('sweeping for light marks on:', fabs)
    zone = np.ones((P.H // 2, P.W // 2), bool)
    counts = []
    for n, buf in enumerate(decode(video)):
        _, Y, U, V = planes(buf, P.W, P.H, copy=False)
        d = np.zeros_like(zone)
        for f in fabs:
            d |= leftovers(P, Y, U, V, zone, f, min_area=12, enclose=0.45)
        counts.append((n, int(d.sum())))
    runs, cur = [], None
    for n, c in counts:
        if c >= 20:
            if cur and n - cur[1] <= 3:
                cur[1] = n; cur[2] = max(cur[2], c)
            else:
                if cur: runs.append(cur)
                cur = [n, n, c]
    if cur: runs.append(cur)
    print(f'{len(counts)} frames, {sum(1 for _, c in counts if c >= 20)} flagged frames, {len(runs)} runs')
    cnt = dict(counts)
    targets = {max(range(a, b + 1), key=lambda i: cnt[i]): (a, b) for a, b, _ in runs}
    tiles = []
    for n, buf in enumerate(decode(video)):
        if n not in targets:
            continue
        _, Y, U, V = planes(buf, P.W, P.H, copy=False)
        d = np.zeros_like(zone)
        for f in fabs:
            d |= leftovers(P, Y, U, V, zone, f, min_area=12, enclose=0.45)
        img = to_bgr(buf, P.W, P.H)
        k_, lab, st, cen = cv2.connectedComponentsWithStats(d.astype(np.uint8), 8)
        th = cv2.resize(img, (180, int(180 * P.H / P.W)), interpolation=cv2.INTER_AREA)
        sx, sy = 180 / (P.W // 2), th.shape[0] / (P.H // 2)
        for i in range(1, k_):
            x, y, w, h, _ = st[i]
            cv2.rectangle(th, (int(x * sx), int(y * sy)), (int((x + w) * sx) + 1, int((y + h) * sy) + 1), (0, 0, 255), 1)
        bi = 1 + int(np.argmax(st[1:, 4])) if k_ > 1 else None
        cx, cy = (int(cen[bi][0] * 2), int(cen[bi][1] * 2)) if bi else (P.W // 2, P.H // 2)
        s = P.px(500)
        x0, y0 = min(max(0, cx - s // 2), P.W - s), min(max(0, cy - s // 2), P.H - s)
        z = cv2.resize(img[y0:y0 + s, x0:x0 + s], (th.shape[0], th.shape[0]), interpolation=cv2.INTER_AREA)
        a, b = targets[n]
        t = np.hstack([th, z])
        cv2.putText(t, f'run {a}-{b} f{n}', (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(t)
        num, den = (int(x) for x in P.info['r_frame_rate'].split('/'))
        print(f'run frames {a}-{b} ({a * den / num:.1f}s) worst frame {n}: {cnt[n]} px')
    for s_ in range(0, len(tiles), 8):
        ch_ = tiles[s_:s_ + 8]
        while len(ch_) % 2: ch_.append(np.zeros_like(ch_[0]))
        out = P.p('review', f'sweep_{s_ // 8}.png')
        cv2.imwrite(out, np.vstack([np.hstack(ch_[i:i + 2]) for i in range(0, len(ch_), 2)]))
        print('  ->', out)
