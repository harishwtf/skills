"""Shared core for the video-logo-removal skill.

Everything works on 8-bit yuv420p frames (Y full-res, U/V half-res), which is what ffmpeg decodes most
camera / phone / editor exports to. A project is a folder with a config.json (see references/config.md);
all intermediate data lives inside that folder.

Coordinates: prompts, crops and grids use HALF-resolution pixel coordinates (the frames SAM 2 sees);
masks are stored at half resolution and upsampled to full resolution when used.
"""
import os, sys, json, glob, subprocess
import numpy as np, cv2

HOME = os.path.expanduser(os.environ.get('VLR_HOME', '~/.cache/video-logo-removal'))
MODELS = os.path.join(HOME, 'models')


# ----------------------------------------------------------------------------- small helpers
def ell(r):
    r = max(0, int(round(r)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def dil(m, r):
    return cv2.dilate(m.astype(np.uint8), ell(r)) > 0 if r > 0 else m.astype(bool)


def ero(m, r):
    return cv2.erode(m.astype(np.uint8), ell(r)) > 0 if r > 0 else m.astype(bool)


def nconv(val, w, sig):
    """normalized convolution: local mean of `val` over pixels where w>0"""
    w = w.astype(np.float32)
    den = cv2.GaussianBlur(w, (0, 0), sig)
    return cv2.GaussianBlur(val * w, (0, 0), sig) / np.maximum(den, 1e-6), den


def local_ref(vals, w, sigs=(25, 70, 200)):
    """multi-scale local means of each array in `vals` over the pixels in w (fabric). Wide logos still get a
    valid reference at their far edge. Pixels with no fabric anywhere near get NaN."""
    outs = [np.full(vals[0].shape, np.nan, np.float32) for _ in vals]
    got = np.zeros(vals[0].shape, bool)
    wf = w.astype(np.float32)
    for sig in sigs:
        den = cv2.GaussianBlur(wf, (0, 0), sig)
        ok = ~got & (den > 0.02)
        for o, val in zip(outs, vals):
            o[ok] = (cv2.GaussianBlur(val * wf, (0, 0), sig) / np.maximum(den, 1e-6))[ok]
        got |= ok
    return outs


def drop_long(mask, lng, ratio=4.5):
    """remove long thin components (reflective stripes, seams, piping): they are never logo letters"""
    m = mask.astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    out = mask.copy()
    for i in range(1, n):
        if st[i, 4] < 5:
            continue
        pts = np.column_stack(np.nonzero(lab == i)).astype(np.float32)
        (_, _), (a, b), _ = cv2.minAreaRect(pts)
        if max(a, b) > lng and max(a, b) / max(1.0, min(a, b)) > ratio:
            out[lab == i] = False
    return out


def hysteresis(weak, strong):
    n, lab = cv2.connectedComponents((weak | strong).astype(np.uint8), connectivity=8)
    hit = np.zeros(n, bool)
    hit[np.unique(lab[strong])] = True
    hit[0] = False
    return hit[lab]


def fill_enclosed(mask, max_area):
    """fill holes fully enclosed by mask (e.g. counters of letters) up to max_area px"""
    m = mask.astype(np.uint8)
    hh, ww = m.shape
    n, lab, st, _ = cv2.connectedComponentsWithStats(1 - m, 8)
    out = mask.copy()
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if not (x == 0 or y == 0 or x + w >= ww or y + h >= hh) and a < max_area:
            out[lab == i] = True
    return out


def large_components(mask, min_area):
    m = mask.astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    return np.isin(lab, [i for i in range(1, n) if st[i, 4] >= min_area])


# ----------------------------------------------------------------------------- video io
def probe(video):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,color_space,'
                          'color_transfer,color_primaries,color_range,codec_name,bit_rate',
                          '-show_entries', 'format=duration', '-of', 'json', video],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j['streams'][0]
    s['duration'] = float(j.get('format', {}).get('duration', 0) or 0)
    has_audio = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index',
                                '-of', 'csv=p=0', video], capture_output=True, text=True).stdout.strip() != ''
    s['has_audio'] = has_audio
    return s


def decode(video, a=None, b=None, scale=None):
    """yield raw yuv420p frames (bytes); a..b inclusive frame indices, or the whole video"""
    vf = []
    if a is not None:
        vf.append(f'select=between(n\\,{a}\\,{b})')
    if scale:
        vf.append(f'scale={scale[0]}:{scale[1]}:flags=area')
    cmd = ['ffmpeg', '-v', 'error', '-threads', '8', '-i', video, '-an']
    if vf:
        cmd += ['-vf', ','.join(vf), '-fps_mode', 'passthrough']
    cmd += ['-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']
    info = probe(video)
    w, h = (scale if scale else (info['width'], info['height']))
    fs = w * h * 3 // 2
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=fs * 2)
    try:
        while True:
            buf = p.stdout.read(fs)
            if len(buf) < fs:
                break
            yield buf
    finally:
        p.stdout.close()
        p.kill()
        p.wait()


def planes(buf, W, H, copy=True):
    a = np.frombuffer(buf, np.uint8)
    if copy:
        a = a.copy()
    return a, a[:W * H].reshape(H, W), a[W * H:W * H * 5 // 4].reshape(H // 2, W // 2), a[W * H * 5 // 4:].reshape(H // 2, W // 2)


def to_bgr(buf, W, H):
    return cv2.cvtColor(np.frombuffer(buf, np.uint8).reshape(H * 3 // 2, W), cv2.COLOR_YUV2BGR_I420)


# ----------------------------------------------------------------------------- project
class Project:
    def __init__(self, pdir):
        self.dir = os.path.abspath(pdir)
        cfg_path = os.path.join(self.dir, 'config.json')
        self.cfg = json.load(open(cfg_path))
        self.video = os.path.expanduser(self.cfg['video'])
        self.info = probe(self.video)
        self.W, self.H = int(self.info['width']), int(self.info['height'])
        if self.W % 2 or self.H % 2:
            sys.exit('video width/height must be even')
        self.FS = self.W * self.H * 3 // 2
        self.k = max(self.W, self.H) / 3840.0          # all pixel constants are tuned at 4K and scaled by k
        self.shots = {int(s): tuple(v) for s, v in self.cfg.get('shots', {}).items()}
        self.objects = {int(s): {int(o): spec for o, spec in d.items()} for s, d in self.cfg.get('objects', {}).items()}
        cb = self.cfg.get('caption_band')
        self.caption_band = tuple(cb) if cb else None

    def px(self, n):
        return max(1, int(round(n * self.k)))

    def p(self, *parts, mk=False):
        path = os.path.join(self.dir, *parts)
        if mk:
            os.makedirs(os.path.dirname(path) if os.path.splitext(path)[1] else path, exist_ok=True)
        return path

    def frames_dir(self, sid):
        return self.p('frames', f'shot{sid:02d}')

    def yuv(self, stage, sid):
        return self.p(stage, f'shot{sid:02d}.yuv')

    def shot_of(self, n):
        for sid, (a, b) in self.shots.items():
            if a <= n <= b:
                return sid, n - a
        return None

    # --- object specs -------------------------------------------------------------------------
    def spec(self, sid, oid, j=None):
        sp = dict(self.objects.get(sid, {}).get(oid, {}))
        if j is not None:
            for ov in sp.get('overrides', []):
                a, b = ov['frames']
                if a <= j <= b:
                    sp.update({k: v for k, v in ov.items() if k != 'frames'})
        return sp

    def mask(self, sid, oid, j, full=True, respect_valid=True):
        if respect_valid:
            v = self.spec(sid, oid).get('valid')
            if v and not (v[0] <= j <= v[1]):
                return None
        path = self.p('masks', f'shot{sid:02d}', f'obj{oid}', f'{j:05d}.png')
        if not os.path.exists(path):
            return None
        m = cv2.imread(path, 0)
        if m is None or m.max() <= 127:
            return None
        if full:
            m = cv2.resize(m, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        return m > 127

    def objs_with_role(self, sid, role):
        return [o for o, sp in self.objects.get(sid, {}).items() if sp.get('role', 'logo') == role]


# ----------------------------------------------------------------------------- colour model
class Fabric:
    """Colour of the material the logo is printed on, as a chroma direction (u, v centred at 0).
    sat(): how strongly a pixel shows the fabric hue; logos are lighter and less saturated."""

    def __init__(self, uv):
        cu, cv_ = float(uv[0]), float(uv[1])
        self.mag = max(4.0, float(np.hypot(cu, cv_)))
        self.du, self.dv = cu / self.mag, cv_ / self.mag

    def sat(self, u, v):
        return u * self.du + v * self.dv

    def perp(self, u, v):
        return u * self.dv - v * self.du

    def is_fabric(self, y, u, v, strict=0.55):
        s = self.sat(u, v)
        return (s > strict * self.mag) & (np.abs(self.perp(u, v)) < 0.8 * s + 4) & (y > 15)

    def __repr__(self):
        return f'Fabric(u={self.du * self.mag:.1f}, v={self.dv * self.mag:.1f})'


def estimate_fabric(Y, U, V, obj, k=1.0):
    """dominant saturated colour in a ring around the tracked logo (half-res chroma)"""
    h, w = U.shape
    o = cv2.resize(obj.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    ring = dil(o, 20 * k) & ~dil(o, 4 * k)
    u = U.astype(np.float32)[ring] - 128
    v = V.astype(np.float32)[ring] - 128
    c = np.hypot(u, v)
    sel = c > 8
    if sel.sum() < 50:
        return None
    ang = np.arctan2(v[sel], u[sel])
    hist, edges = np.histogram(ang, bins=36, range=(-np.pi, np.pi))
    pk = int(np.argmax(hist))
    lo, hi = edges[max(0, pk - 1)], edges[min(36, pk + 2)]
    pick = (ang >= lo) & (ang <= hi)
    return Fabric((float(np.median(u[sel][pick])), float(np.median(v[sel][pick]))))


def fabric_for(P, sid, oid, Y, U, V, obj, cache):
    sp = P.spec(sid, oid)
    key = (sid, oid)
    if key in cache:
        return cache[key]
    f = sp.get('fabric', 'auto')
    fab = Fabric(f) if isinstance(f, (list, tuple)) else estimate_fabric(Y, U, V, obj, P.k)
    cache[key] = fab
    if fab is not None:
        print(f'shot {sid} obj {oid}: fabric colour {fab}', file=sys.stderr)
    return fab


# ----------------------------------------------------------------------------- captions
def caption_mask(P, Y, U, V):
    """burned-in captions (white glyphs with dark outline) inside caption_band rows: protected from edits"""
    m = np.zeros((P.H, P.W), bool)
    if not P.caption_band:
        return m
    y0, y1 = P.caption_band
    y0, y1 = max(0, y0) & ~1, min(P.H, y1) & ~1
    y = Y[y0:y1].astype(np.int16)
    u = cv2.resize(U[y0 // 2:y1 // 2], (P.W, y1 - y0), interpolation=cv2.INTER_NEAREST).astype(np.int16) - 128
    v = cv2.resize(V[y0 // 2:y1 // 2], (P.W, y1 - y0), interpolation=cv2.INTER_NEAREST).astype(np.int16) - 128
    white = (y > 215) & (np.abs(u) < 10) & (np.abs(v) < 10)
    ring = dil(white, P.px(12))
    dark = (y < 60) & ring
    m[y0:y1] = dil(white | dark, P.px(3))
    return m


# ----------------------------------------------------------------------------- inpainting
_LAMA = None
_DEV = None


def device():
    import torch
    global _DEV
    if _DEV is None:
        if torch.cuda.is_available():
            _DEV = torch.device('cuda')
        elif torch.backends.mps.is_available():
            _DEV = torch.device('mps')
        else:
            _DEV = torch.device('cpu')
    return _DEV


def lama():
    import torch
    global _LAMA
    if _LAMA is None:
        _LAMA = torch.jit.load(os.path.join(MODELS, 'big-lama.pt'), map_location='cpu').to(device()).eval()
    return _LAMA


def run_lama(rgb, hole):
    import torch
    h, w = hole.shape
    t = torch.from_numpy(rgb).permute(2, 0, 1)[None].float().div(255)
    mk = torch.from_numpy(hole.astype(np.float32))[None, None]
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8
    t = torch.nn.functional.pad(t, (0, pw, 0, ph), mode='reflect')
    mk = torch.nn.functional.pad(mk, (0, pw, 0, ph), mode='reflect')
    with torch.inference_mode():
        o = lama()(t.to(device()), mk.to(device()))
    return o[0, :, :h, :w].permute(1, 2, 0).clamp(0, 1).mul(255).cpu().numpy().astype(np.float32)


def lama_fill(rgb, hole, max_side):
    ch, cw = hole.shape
    sc = min(1.0, max_side / max(ch, cw))
    if sc < 1.0:
        sw, sh = int(round(cw * sc)), int(round(ch * sc))
        small = cv2.resize(rgb, (sw, sh), interpolation=cv2.INTER_AREA)
        sh_hole = cv2.resize(hole.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_AREA) > 0
        return cv2.resize(run_lama(small, sh_hole), (cw, ch), interpolation=cv2.INTER_CUBIC)
    return run_lama(rgb, hole)


def paint_out(rgb, src, todo):
    """replace `todo` pixels with a smooth extension of the `src` pixels (so LaMa never sees them)"""
    rf = rgb.astype(np.float32)
    filled = rf.copy()
    srcf = src.astype(np.float32)
    todo = todo.copy()
    for sig in (12, 35, 100):
        den = cv2.GaussianBlur(srcf, (0, 0), sig)
        est = cv2.GaussianBlur(rf * srcf[..., None], (0, 0), sig) / np.maximum(den, 1e-6)[..., None]
        sel = todo & (den > 0.03)
        filled[sel] = est[sel]
        todo &= ~sel
    if todo.any() and src.sum() > 0:
        filled[todo] = rf[src > 0].mean(axis=0)
    return np.clip(filled + 0.5, 0, 255).astype(np.uint8)


def nearest_fill(rgb, src):
    """each pixel takes the colour of its nearest src pixel (edge extension), lightly smoothed"""
    _, lab = cv2.distanceTransformWithLabels((~src).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    cols = np.zeros((lab.max() + 1, 3), np.float32)
    cols[lab[src]] = rgb[src].astype(np.float32)
    return cv2.GaussianBlur(cols[lab], (0, 0), 1.5)


def fix_region(P, Y, U, V, hole, cap, clip=None, bg='lama', max_side=1600, feather=3.0):
    """Inpaint `hole` (full-res bool) in place in the Y/U/V planes.
    clip: the surface the logo sits on (garment / bag). If given, LaMa only ever sees that surface; hole pixels
          outside it are filled from the outside world (bg='lama' or 'nearest') and the two fills are joined
          with a soft edge along the surface outline (a 'split' fill). Captions (cap) are never modified."""
    hole = hole & ~cap
    ys, xs = np.nonzero(hole)
    if len(ys) == 0:
        return
    H, W = P.H, P.W
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    mg = int(max(P.px(96), 0.6 * max(y1 - y0, x1 - x0)))
    y0, x0 = max(0, y0 - mg) & ~1, max(0, x0 - mg) & ~1
    y1, x1 = min(H, (y1 + mg + 1) & ~1), min(W, (x1 + mg + 1) & ~1)
    ch, cw = y1 - y0, x1 - x0
    hc, capc = hole[y0:y1, x0:x1], cap[y0:y1, x0:x1]
    i420 = np.concatenate([Y[y0:y1, x0:x1].reshape(-1), U[y0 // 2:y1 // 2, x0 // 2:x1 // 2].reshape(-1),
                           V[y0 // 2:y1 // 2, x0 // 2:x1 // 2].reshape(-1)]).reshape(ch * 3 // 2, cw)
    rgb = cv2.cvtColor(i420, cv2.COLOR_YUV2BGR_I420)[..., ::-1].copy()
    lh = hc | capc
    if clip is not None:
        cc = clip[y0:y1, x0:x1]
        fill = lama_fill(paint_out(rgb, cc & ~hc & ~capc, ~cc), lh, max_side)
        src_b = ~cc & ~hc & ~capc
        if src_b.sum() > 200 and (hc & ~cc).any():
            fill_b = nearest_fill(rgb, src_b) if bg == 'nearest' else lama_fill(paint_out(rgb, src_b, cc), lh, max_side)
            soft = cv2.GaussianBlur(cc.astype(np.float32), (0, 0), 3.0)[..., None]
            fill = fill * soft + fill_b * (1 - soft)
    else:
        fill = lama_fill(rgb, lh, max_side)
    f420 = cv2.cvtColor(np.clip(fill[..., ::-1], 0, 255).astype(np.uint8), cv2.COLOR_BGR2YUV_I420).reshape(-1)
    q = (ch // 2) * (cw // 2)
    fY = f420[:ch * cw].reshape(ch, cw).astype(np.float32)
    fU = f420[ch * cw:ch * cw + q].reshape(ch // 2, cw // 2).astype(np.float32)
    fV = f420[ch * cw + q:].reshape(ch // 2, cw // 2).astype(np.float32)
    # grain: LaMa output is smoother than camera footage; add noise to match the surrounding texture
    oY = Y[y0:y1, x0:x1].astype(np.float32)
    hp = oY - cv2.GaussianBlur(oY, (0, 0), 1.2)
    ring = dil(hc, P.px(30)) & ~hc & ~capc
    sig = float(hp[ring].std()) if ring.sum() > 100 else 0.0
    fhp = fY - cv2.GaussianBlur(fY, (0, 0), 1.2)
    fsig = float(fhp[hc].std()) if hc.sum() > 100 else 0.0
    add = max(0.0, sig ** 2 - fsig ** 2) ** 0.5
    if add > 0.2:
        g = cv2.GaussianBlur(np.random.default_rng().standard_normal((ch, cw)).astype(np.float32), (0, 0), 0.6)
        fY = fY + g * (add / max(1e-6, g.std()))
    a = np.clip(cv2.GaussianBlur(hc.astype(np.float32), (0, 0), feather) * 1.6, 0, 1)
    a[capc] = 0
    aU = cv2.resize(a, (cw // 2, ch // 2), interpolation=cv2.INTER_AREA)
    Y[y0:y1, x0:x1] = np.clip(oY * (1 - a) + fY * a + 0.5, 0, 255).astype(np.uint8)
    for Pl, F in ((U, fU), (V, fV)):
        o = Pl[y0 // 2:y1 // 2, x0 // 2:x1 // 2].astype(np.float32)
        Pl[y0 // 2:y1 // 2, x0 // 2:x1 // 2] = np.clip(o * (1 - aU) + F * aU + 0.5, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- crops
def crop_yuv_full(P, Y, U, V, y0, y1, x0, x1):
    y = Y[y0:y1, x0:x1].astype(np.float32)
    hh, ww = y.shape
    u = cv2.resize(U[y0 // 2:y1 // 2, x0 // 2:x1 // 2], (ww, hh), interpolation=cv2.INTER_LINEAR).astype(np.float32) - 128
    v = cv2.resize(V[y0 // 2:y1 // 2, x0 // 2:x1 // 2], (ww, hh), interpolation=cv2.INTER_LINEAR).astype(np.float32) - 128
    return y, u, v


def box_around(P, mask, pad):
    ys, xs = np.nonzero(mask)
    y0, y1 = max(0, ys.min() - pad) & ~1, min(P.H, (ys.max() + pad + 2) & ~1)
    x0, x1 = max(0, xs.min() - pad) & ~1, min(P.W, (xs.max() + pad + 2) & ~1)
    return y0, y1, x0, x1


# ----------------------------------------------------------------------------- leftover detector (QA + cleanup)
def leftovers(P, Y, U, V, zone_half, fab, min_area=6, enclose=0.7):
    """light, less-saturated blobs enclosed by fabric (half-res bool). Edges against walls / skin don't count
    because the blob must be mostly surrounded by fabric; long thin stripes are ignored."""
    h, w = U.shape
    y = cv2.resize(Y, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    u = U.astype(np.float32) - 128
    v = V.astype(np.float32) - 128
    fabric = fab.is_fabric(y, u, v, strict=0.5)
    s = fab.sat(u, v)
    f = fabric.astype(np.float32)
    den = cv2.blur(f, (45, 45))
    yl = cv2.blur(y * f, (45, 45)) / np.maximum(den, 1e-3)
    sl = cv2.blur(s * f, (45, 45)) / np.maximum(den, 1e-3)
    cand = ~fabric & (s < sl - 6) & (y > yl + 22) & (den > 0.35) & zone_half
    if P.caption_band:
        a, b = P.caption_band[0] // 2, P.caption_band[1] // 2
        cand[a:b] &= ~((y[a:b] > 200) & (np.abs(u[a:b]) < 12) & (np.abs(v[a:b]) < 12))
    cand = cv2.morphologyEx(cand.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cand, 8)
    out = np.zeros((h, w), bool)
    for i in range(1, n):
        x0, y0, bw, bh, area = st[i]
        if area < min_area:
            continue
        sl_ = (slice(max(0, y0 - 8), y0 + bh + 8), slice(max(0, x0 - 8), x0 + bw + 8))
        comp = lab[sl_] == i
        if not drop_long(comp, P.px(110) / 2).any():
            continue
        ring = dil(comp, 5) & ~comp & (lab[sl_] == 0)
        if ring.sum() == 0 or fabric[sl_][ring].mean() < enclose:
            continue
        out[sl_] |= comp
    return out
