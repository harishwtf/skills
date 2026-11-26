#!/usr/bin/env python
"""Temporal stabilization of the filled areas: removes the shimmer you see on playback when each frame's
fill was invented independently. For every frame, the fills of the neighbouring frames are warped onto it
with optical flow computed on the ORIGINAL footage (so they follow the real cloth motion) and combined
with a robust weighted median-anchored average. Only pixels that differ from the reference are touched;
grain lost by averaging is added back.

usage: stabilize.py PROJECT [shot ...] [--in clean] [--out stab] [--ref STAGE]
  --ref STAGE  only re-stabilize pixels that differ from STAGE (e.g. a second logo pass on top of approved
               'stab' frames) instead of everything that differs from the original video
Config: "stabilize_skip": {"14": [43, 75]}  local frame ranges to leave as-is (fast whip pans / heavy motion
blur, where flow is unreliable and averaging makes blotches).
"""
import os, sys, argparse, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode, ell

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('shots', nargs='*', type=int)
ap.add_argument('--in', dest='src', default='clean')
ap.add_argument('--out', default='stab')
ap.add_argument('--ref', default=None)
ap.add_argument('--k', type=int, default=4, help='half window in frames')
ap.add_argument('--sigma', type=float, default=2.0)
ap.add_argument('--robust', type=float, default=14.0)
A = ap.parse_args()
P = Project(A.project)
W, H, FS = P.W, P.H, P.FS
SKIP = {int(k): v for k, v in P.cfg.get('stabilize_skip', {}).items()}
Q = 4
qw, qh = W // Q, H // Q
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
GXQ, GYQ = np.meshgrid(np.arange(qw, dtype=np.float32), np.arange(qh, dtype=np.float32))
os.makedirs(P.p(A.out), exist_ok=True)


def split(buf):
    a = np.frombuffer(buf, np.uint8)
    return [a[:W * H].reshape(H, W), a[W * H:W * H * 5 // 4].reshape(H // 2, W // 2), a[W * H * 5 // 4:].reshape(H // 2, W // 2)]


def warpq(img, flow):
    return cv2.remap(img, GXQ + flow[..., 0], GYQ + flow[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def read_stage(stage, sid, n):
    with open(P.yuv(stage, sid), 'rb') as f:
        return [split(f.read(FS)) for _ in range(n)]


for sid in (A.shots or sorted(P.shots)):
    a, b = P.shots[sid]
    n = b - a + 1
    orig = [split(bytes(x)) for x in decode(P.video, a, b)]
    outs = read_stage(A.src, sid, n)
    ref = read_stage(A.ref, sid, n) if A.ref else orig
    oq = [cv2.resize(o[0], (qw, qh), interpolation=cv2.INTER_AREA) for o in orig]
    chg = []
    for o, c in zip(ref, outs):
        d = np.abs(c[0].astype(np.int16) - o[0].astype(np.int16)) > 1
        du = (np.abs(c[1].astype(np.int16) - o[1].astype(np.int16)) > 1) | (np.abs(c[2].astype(np.int16) - o[2].astype(np.int16)) > 1)
        d |= cv2.resize(du.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
        chg.append(cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_CLOSE, ell(P.px(4))) > 0)
    skip = SKIP.get(sid)
    res = []
    K = A.k
    for t in range(n):
        Yt, Ut, Vt = [x.copy() for x in outs[t]]
        if chg[t].sum() < 200 or (skip and skip[0] <= t <= skip[1]):
            res.append((Yt, Ut, Vt)); continue
        ys, xs = np.nonzero(chg[t])
        y0, y1 = max(0, ys.min() - 24) & ~3, min(H, (ys.max() + 28) & ~3)
        x0, x1 = max(0, xs.min() - 24) & ~3, min(W, (xs.max() + 28) & ~3)
        rh, rw = y1 - y0, x1 - x0
        gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
        gxu, gyu = np.meshgrid(np.arange(x0 // 2, x1 // 2, dtype=np.float32), np.arange(y0 // 2, y1 // 2, dtype=np.float32))
        sy, su, sv, sw = [], [], [], []
        for s in range(max(0, t - K), min(n, t + K + 1)):
            wt = np.exp(-((s - t) ** 2) / (2 * A.sigma ** 2))
            if s == t:
                sy.append(Yt[y0:y1, x0:x1].astype(np.float32)); su.append(Ut[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32))
                sv.append(Vt[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32)); sw.append(np.full((rh, rw), wt, np.float32))
                continue
            f_ts = dis.calc(oq[t], oq[s], None)
            f_st = dis.calc(oq[s], oq[t], None)
            ok = np.linalg.norm(f_ts + warpq(f_st, f_ts), axis=2) < 0.75          # forward-backward consistency
            fq = f_ts[y0 // Q:y1 // Q, x0 // Q:x1 // Q]
            fx = cv2.resize(fq[..., 0], (rw, rh), interpolation=cv2.INTER_LINEAR) * Q
            fy = cv2.resize(fq[..., 1], (rw, rh), interpolation=cv2.INTER_LINEAR) * Q
            valid = cv2.resize(ok[y0 // Q:y1 // Q, x0 // Q:x1 // Q].astype(np.uint8), (rw, rh), interpolation=cv2.INTER_NEAREST) > 0
            mx, my = gx + fx, gy + fy
            valid &= (mx >= 0) & (mx <= W - 1) & (my >= 0) & (my <= H - 1)
            Ys, Us, Vs = outs[s]
            sy.append(cv2.remap(Ys, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32))
            fxu = cv2.resize(fx, (rw // 2, rh // 2), interpolation=cv2.INTER_AREA) / 2
            fyu = cv2.resize(fy, (rw // 2, rh // 2), interpolation=cv2.INTER_AREA) / 2
            su.append(cv2.remap(Us, gxu + fxu, gyu + fyu, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32))
            sv.append(cv2.remap(Vs, gxu + fxu, gyu + fyu, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32))
            sw.append(valid.astype(np.float32) * wt)
        SY, SW = np.stack(sy), np.stack(sw)
        ci = t - max(0, t - K)
        with np.errstate(all='ignore'):
            m0 = np.nanmedian(np.where(SW > 0, SY, np.nan), axis=0)
        m0 = np.where(np.isnan(m0), SY[ci], m0)
        R = SW * np.exp(-((SY - m0) / A.robust) ** 2)
        R[ci] = np.maximum(R[ci], 1e-3)
        Ystab = (SY * R).sum(0) / np.maximum(R.sum(0), 1e-6)
        RU = cv2.resize(R.transpose(1, 2, 0), (rw // 2, rh // 2), interpolation=cv2.INTER_AREA).reshape(rh // 2, rw // 2, -1).transpose(2, 0, 1)
        Ustab = (np.stack(su) * RU).sum(0) / np.maximum(RU.sum(0), 1e-6)
        Vstab = (np.stack(sv) * RU).sum(0) / np.maximum(RU.sum(0), 1e-6)
        c = chg[t][y0:y1, x0:x1].astype(np.uint8)
        m = cv2.GaussianBlur((cv2.erode(c, ell(4)) > 0).astype(np.float32), (0, 0), 3) * (c > 0)
        cur = Yt[y0:y1, x0:x1].astype(np.float32)
        newY = cur + m * (Ystab - cur)
        core = cv2.erode(c, ell(8)) > 0
        if core.sum() > 400:
            hp_c = cur - cv2.GaussianBlur(cur, (0, 0), 1.2)
            hp_n = newY - cv2.GaussianBlur(newY, (0, 0), 1.2)
            add = max(0.0, float(hp_c[core].std()) ** 2 - float(hp_n[core].std()) ** 2) ** 0.5
            if add > 0.2:
                g = cv2.GaussianBlur(np.random.default_rng().standard_normal((rh, rw)).astype(np.float32), (0, 0), 0.6)
                newY += m * g * (add / max(g.std(), 1e-6))
        Yt[y0:y1, x0:x1] = np.clip(newY + 0.5, 0, 255).astype(np.uint8)
        mu = cv2.resize(m, (rw // 2, rh // 2), interpolation=cv2.INTER_AREA)
        for Pl, St in ((Ut, Ustab), (Vt, Vstab)):
            cu = Pl[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32)
            Pl[y0 // 2:y1 // 2, x0 // 2:x1 // 2] = np.clip(cu + mu * (St - cu) + 0.5, 0, 255).astype(np.uint8)
        res.append((Yt, Ut, Vt))
    with open(P.yuv(A.out, sid), 'wb') as f:
        for Yt, Ut, Vt in res:
            f.write(Yt.tobytes()); f.write(Ut.tobytes()); f.write(Vt.tobytes())
    print(f'shot {sid}: stabilized {n} frames -> {P.yuv(A.out, sid)}', flush=True)
