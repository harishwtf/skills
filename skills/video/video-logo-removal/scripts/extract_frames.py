#!/usr/bin/env python
"""Extract half-resolution JPEG frames for the configured shots (what SAM 2 tracks on, and what prompt
coordinates refer to). usage: extract_frames.py PROJECT [shot ...]"""
import os, sys, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlr import Project, decode

P = Project(sys.argv[1])
shots = [int(x) for x in sys.argv[2:]] or sorted(P.shots)
w, h = P.W // 2, P.H // 2
for sid in shots:
    a, b = P.shots[sid]
    d = P.frames_dir(sid)
    os.makedirs(d, exist_ok=True)
    n = 0
    for j, buf in enumerate(decode(P.video, a, b, scale=(w, h))):
        img = cv2.cvtColor(np.frombuffer(buf, np.uint8).reshape(h * 3 // 2, w), cv2.COLOR_YUV2BGR_I420)
        cv2.imwrite(os.path.join(d, f'{j:05d}.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        n += 1
    print(f'shot {sid}: {n} frames -> {d}')
    if n != b - a + 1:
        sys.exit(f'shot {sid}: expected {b - a + 1} frames')
