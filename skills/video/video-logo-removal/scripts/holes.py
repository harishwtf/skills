"""Turn a tracked logo blob into the exact set of pixels to replace, per removal mode.

Modes (set per object in config.json, can change per frame range via "overrides"):
  flat    - logo printed inside a surface (chest, back). Fill SAM's blob + any letter fragments it missed.
  edge    - logo that reaches the surface's silhouette (sleeves, a bag next to a door). Split fill: the surface
            side is inpainted from the surface only, the outside from the outside only, so wall/door/skin colour
            never smears into the fabric (and vice versa).
  tight   - SAM's blob also covers things that must survive (a cuff, folds, a hand): replace only the letter
            strokes found inside/near the blob.
  unblend - motion-blurred, semi-transparent letters: subtract the letters from the fabric (keeps the real
            folds and motion blur), inpaint only the near-opaque core.
"""
import numpy as np, cv2
from vlr import dil, ero, local_ref, drop_long, hysteresis, fill_enclosed, large_components, crop_yuv_full, box_around, nconv


def surface_mask(P, o, fabric, tracked=None):
    """outline of the garment / object the logo sits on (crop coords)"""
    if tracked is not None:
        s = cv2.morphologyEx(tracked.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (2 * P.px(25) + 1,) * 2)) > 0
    else:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * P.px(30) + 1,) * 2)
        s = cv2.morphologyEx(fabric.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
    s |= ero(o, P.px(10))
    return fill_enclosed(s, (P.px(150)) ** 2)


def logo_hole(P, Y, U, V, obj, fab, mode='flat', surface=None, protect=None, spec=None):
    """-> (hole, clip) full-res masks, or None when the track drifted off the fabric.
    clip is the surface mask for edge/tight split fills (None for flat)."""
    spec = spec or {}
    pad = P.px(220)
    y0, y1, x0, x1 = box_around(P, obj, pad)
    y, u, v = crop_yuv_full(P, Y, U, V, y0, y1, x0, x1)
    o = obj[y0:y1, x0:x1]
    s = fab.sat(u, v)
    fabric = fab.is_fabric(y, u, v)
    # drift guard: a real logo has fabric around it
    ring = dil(o, P.px(30)) & ~o
    if ring.sum() and (s[ring] > 0.3 * fab.mag).mean() < 0.005:
        return None
    yl, sl = local_ref([y, s], fabric)
    valid_ref = ~np.isnan(yl)
    yl = np.nan_to_num(yl, nan=255.0); sl = np.nan_to_num(sl, nan=-255.0)
    prot = np.zeros_like(o)
    if protect is not None:
        prot = dil(protect[y0:y1, x0:x1], P.px(8))
    # other solid colours (e.g. a sleeve next to a bag): large, saturated, off-hue regions are never logo
    chroma = np.hypot(u, v)
    other = large_components((chroma > 15) & (s < 0.2 * chroma) & ~o, P.px(55) ** 2)
    prot |= dil(other, P.px(3))
    surf = None
    if mode in ('edge', 'tight') and spec.get('surface', 'auto') is not None:
        tr = surface[y0:y1, x0:x1] if surface is not None else None
        surf = surface_mask(P, o, fabric, tr)
    reach = P.px(spec.get('reach', 60))
    near = dil(o, reach) & valid_ref & ~prot
    if surf is not None:
        near &= dil(surf, P.px(4))
    strong = ~fabric & (y > yl + 10) & (s < sl - 6) & near
    weak = (y > yl + 4) & (s < sl - 3) & near
    ink = drop_long(hysteresis(weak, strong), P.px(220))
    if mode == 'tight':
        hole = dil(ink, P.px(10)) & dil(o, P.px(24))
    else:
        hole = dil(o, P.px(spec.get('dilate', 9))) | dil(ink, P.px(8))
    if spec.get('extra'):
        hole = dil(hole, P.px(spec['extra']))
    hole &= ~prot
    clip = None
    if surf is not None:
        core = hole.copy()
        band = spec.get('edge_band', 0)
        if band:
            # redraw the logo's soft rim where it meets the outside world (door, wall)
            hole |= dil(hole, P.px(band)) & ~fabric & ~prot
        clip = (surf | core) & ~other
    H_, C_ = np.zeros((P.H, P.W), bool), None
    H_[y0:y1, x0:x1] = hole
    if clip is not None:
        C_ = np.zeros((P.H, P.W), bool)
        C_[y0:y1, x0:x1] = clip
    return H_, C_


def unblend(P, Y, U, V, obj, fab, forbid=None, core_thr=0.5, amax=0.8,
            Rs=(1.2, 1.35, 1.5, 1.65, 1.8, 2.0, 2.2, 2.45, 2.7, 3.0)):
    """Subtract semi-transparent light letters from the fabric, in place. Model per pixel:
    pixel = (1-a)*fabric + a*letter, letters neutral, letter luma = R * fabric luma (R self-calibrated).
    Solved at chroma resolution so luma/chroma edges align; luma correction applied as a smooth delta so
    the original fine detail and grain survive. Returns the near-opaque core that still needs inpainting."""
    H, W = Y.shape
    reg_full = ero(obj, 2)
    if not reg_full.any():
        return np.zeros((H, W), bool)
    pad = P.px(120)
    ys, xs = np.nonzero(reg_full)
    y0, y1 = max(0, ys.min() - pad) & ~3, min(H, (ys.max() + pad + 4) & ~3)
    x0, x1 = max(0, xs.min() - pad) & ~3, min(W, (xs.max() + pad + 4) & ~3)
    hh, ww = (y1 - y0) // 2, (x1 - x0) // 2
    yfull = Y[y0:y1, x0:x1].astype(np.float32)
    y = cv2.resize(yfull, (ww, hh), interpolation=cv2.INTER_AREA)
    u = U[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32) - 128
    v = V[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32) - 128
    s, pp = fab.sat(u, v), fab.perp(u, v)
    reg = cv2.resize(reg_full[y0:y1, x0:x1].astype(np.uint8), (ww, hh), interpolation=cv2.INTER_NEAREST) > 0
    # the letters' blur spills past the tracked outline: extend into nearby still-fabric-tinted pixels only
    ext = dil(reg, P.px(30) / 2) & (s > 0.2 * fab.mag)
    reg |= cv2.morphologyEx(ext.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    if forbid is not None:
        reg &= ~(cv2.resize(forbid[y0:y1, x0:x1].astype(np.uint8), (ww, hh), interpolation=cv2.INTER_NEAREST) > 0)
    fabm = fab.is_fabric(y, u, v, strict=0.55).astype(np.float32)
    fab_out = fabm * ~dil(reg, 3)
    yfab, _ = nconv(y, fab_out, 25)
    reg &= (s > -5) & (y > 0.85 * yfab)          # never skin / anti-fabric colours / shadows
    neut = (np.hypot(u, v) < 9) & (y > yfab + 15)
    reg &= ~dil(neut & ~drop_long(neut, P.px(110) / 2), 3)   # long neutral stripes (reflective tape)
    rs, rp = s / np.maximum(y, 1.0), pp / np.maximum(y, 1.0)
    csm, d1 = nconv(rs, fab_out, 12); csm2, _ = nconv(rs, fab_out, 40)
    cpm, _ = nconv(rp, fab_out, 12); cpm2, _ = nconv(rp, fab_out, 40)
    w1 = np.clip(d1 / 0.15, 0, 1)
    csm = np.maximum(csm * w1 + csm2 * (1 - w1), 0.02)
    cpm = cpm * w1 + cpm2 * (1 - w1)
    A = np.minimum(np.clip(s / csm, 0, None), y)    # (1-a) * fabric luma
    best = None
    for R in Rs:
        a = np.clip((y - A) / np.maximum(R * A + y - A, 1e-3), 0, amax)
        yf = A / (1 - a)
        hp = yf - cv2.GaussianBlur(yf, (0, 0), 7)
        sel = reg & (a > 0.06) & (a < 0.5)
        if sel.sum() < 150:
            best = (0, 1.9); break
        aa = a[sel] - a[sel].mean()
        cov = abs(float((aa * hp[sel]).mean()))
        if best is None or cov < best[0]:
            best = (cov, R)
    R = best[1]
    a = np.clip((y - A) / np.maximum(R * A + y - A, 1e-3), 0, amax)
    yf = A / (1 - a)
    sf = s / (1 - a)
    pf = cpm * yf
    sel = reg & (a > 0.03) & (a < 0.6)
    if sel.sum() > 300:                                   # remove any remaining letter-shaped imprint
        basis = a * cv2.GaussianBlur(yf, (0, 0), 10)
        hb = basis - cv2.GaussianBlur(basis, (0, 0), 8)
        den = max(float((hb[sel] ** 2).sum()), 1e-6)
        for name in ('y', 's'):
            tgt = yf if name == 'y' else sf
            ht = tgt - cv2.GaussianBlur(tgt, (0, 0), 8)
            beta = float((ht[sel] * hb[sel]).sum() / den)
            if name == 'y':
                yf = yf - beta * basis
            else:
                sf = sf - beta * basis
    t = np.clip((a - 0.25) / 0.3, 0, 1)                  # tame noise amplification
    yf = yf * (1 - t) + cv2.GaussianBlur(yf, (0, 0), 1.0) * t
    sf = sf * (1 - t) + cv2.GaussianBlur(sf, (0, 0), 1.0) * t
    uf = sf * fab.du + pf * fab.dv
    vf = sf * fab.dv - pf * fab.du
    m = cv2.GaussianBlur(reg.astype(np.float32), (0, 0), 1.5) * np.clip(a / 0.04, 0, 1)
    m[~dil(reg, 3)] = 0
    FW, FH = x1 - x0, y1 - y0
    up = lambda z, it=cv2.INTER_CUBIC: cv2.resize(z, (FW, FH), interpolation=it)
    hf = yfull - up(y)
    ynew = up(y + m * (yf - y))
    kk = np.clip(up(a * m, cv2.INTER_LINEAR) / 0.12, 0, 1)
    clean = (up(m, cv2.INTER_LINEAR) < 0.02) & (up(fabm, cv2.INTER_NEAREST) > 0)
    gs = float(hf[clean].std()) if clean.sum() > 500 else 1.0
    g = cv2.GaussianBlur(np.random.default_rng().standard_normal((FH, FW)).astype(np.float32), (0, 0), 0.7)
    g *= gs / max(float(g.std()), 1e-6)
    Y[y0:y1, x0:x1] = np.clip(ynew + hf * (1 - kk) + g * kk + 0.5, 0, 255).astype(np.uint8)
    U[y0 // 2:y1 // 2, x0 // 2:x1 // 2] = np.clip(u + m * (uf - u) + 128.5, 0, 255).astype(np.uint8)
    V[y0 // 2:y1 // 2, x0 // 2:x1 // 2] = np.clip(v + m * (vf - v) + 128.5, 0, 255).astype(np.uint8)
    core = np.zeros((H, W), bool)
    core[y0:y1, x0:x1] = cv2.resize(((a > core_thr) & reg).astype(np.uint8), (FW, FH), interpolation=cv2.INTER_NEAREST) > 0
    return core
