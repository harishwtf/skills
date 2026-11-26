# config.json reference

One project folder per video. `config.json` lives at its root; every script takes the folder as its first
argument and writes its data inside it (`frames/`, `masks/`, `clean/`, `stab/`, `review/` …).

```json
{
  "video": "/abs/path/input.mp4",
  "output": "/abs/path/input_nologo.mp4",
  "caption_band": [2880, 3460],
  "shots": { "3": [57, 153], "5": [263, 302] },
  "objects": {
    "3": {
      "1":  { "mode": "flat", "prompts": [[0, [715,1005,870,1095]], [96, [730,1055,890,1145]]] },
      "2":  { "mode": "edge", "prompts": [[96, [150,1030,345,1215]]] },
      "20": { "mode": "edge", "bg": "nearest", "edge_band": 10,
              "prompts": [[18, [808,1352,852,1474]], [58, [734,1410,802,1476]]] },
      "30": { "role": "protect", "prompts": [[8, [600,1730,890,1920], [[700,1800,1], [800,1850,1]]]] }
    },
    "14": {
      "2": { "mode": "edge", "prompts": [[8, [660,880,760,1030]]],
             "overrides": [ { "frames": [46, 72], "mode": "unblend" } ] }
    }
  },
  "stabilize_skip": { "14": [43, 75] }
}
```

## Top level

| key | meaning |
|---|---|
| `video` | source file. Never overwritten. |
| `output` | final render path (default: `<video>_clean.mp4`). |
| `caption_band` | `[y0, y1]` full-res rows that contain burned-in captions (white text with a dark outline). Those pixels are never modified and are hidden from the inpainter. `null` if the video has no captions. |
| `shots` | `{shot_id: [first_frame, last_frame]}` global frame numbers, inclusive. Only list shots that need work; copy them from `shots_detected.json`. |
| `objects` | `{shot_id: {object_id: spec}}` (object ids are per shot; reuse the same id for the same logo across shots if you like). |
| `stabilize_skip` | `{shot_id: [a, b]}` local frame ranges that `stabilize.py` leaves alone (fast whip pans, heavy motion blur). |

## Object spec

| key | default | meaning |
|---|---|---|
| `role` | `"logo"` | `"logo"` = remove it. `"protect"` = never modify these pixels (hands, a watch, a face that overlaps a logo). `"surface"` = a tracked silhouette (the whole garment/bag) used by `edge` mode via `"surface": <id>`. |
| `prompts` | required | SAM 2 prompts in **half-res** coordinates (the frames in `frames/shotNN`): `[frame, [x0,y0,x1,y1]]` or `[frame, [x0,y0,x1,y1], [[x,y,1], [x,y,0]]]` (1 = on the object, 0 = not the object). Prompt the same object on several frames: first, last, and wherever it turns, blurs, or gets occluded. |
| `mode` | `"flat"` | `flat` / `edge` / `tight` / `unblend` (see SKILL.md "Choosing a mode"). |
| `valid` | all frames | `[a, b]` local frames where the track is trustworthy. Outside it the object is ignored (use when the tracker jumps to something else after the logo leaves the frame). |
| `overrides` | `[]` | per-frame-range changes, e.g. `{"frames": [46, 72], "mode": "unblend"}` or `{"frames": [0, 45], "mode": "tight"}`. Any spec key can be overridden. |
| `fabric` | `"auto"` | colour the logo is printed on, as centred chroma `[u, v]` (e.g. green ≈ `[0, -25]`, orange ≈ `[-17, 23]`). `auto` samples a ring around the first tracked mask. Set it explicitly if the log prints a wrong colour. |
| `surface` | `"auto"` | for `edge`/`tight`: `"auto"` (outline of the fabric colour around the logo), an object id with `role: "surface"` (a tracked silhouette; best when the garment edge is busy), or `null` (no split fill). |
| `bg` | `"lama"` | how hole pixels *outside* the surface are filled: `"lama"` (inpaint from the outside world) or `"nearest"` (copy the nearest outside pixel; best for thin rims against a door/wall and next to another garment). |
| `edge_band` | `0` | px (4K scale) to extend the fill past the logo into non-fabric pixels, so the logo's soft rim against the background is redrawn too. |
| `protect` | all `protect` objects in the shot | list of object ids this logo must avoid. |
| `dilate` | `9` | px (4K scale) added around SAM's mask (anti-aliased letter edges). |
| `extra` | `0` | extra px dilation of the final hole (heavy motion smear past the mask). |
| `reach` | `60` | px (4K scale) around the mask in which loose letter fragments are also removed. |
| `cleanup` | `true` | after filling, re-detect leftover fragments near the logo and fill them. |

All pixel sizes are written at 4K scale and automatically scaled for other resolutions.

## Folder layout produced

```
project/
  config.json
  shots_detected.json      probe_shots.py
  frames/shotNN/*.jpg      extract_frames.py (half-res)
  masks/shotNN/objK/*.png  track.py (half-res probability masks)
  clean/shotNN.yuv         clean.py (raw yuv420p, full-res; ~12 MB per 4K frame)
  stab/shotNN.yuv          stabilize.py
  review/*.png             review.py / qa.py output to look at
```

The `.yuv` folders are large (a 4K shot of 100 frames ≈ 1.2 GB). Delete the project folder when done.
