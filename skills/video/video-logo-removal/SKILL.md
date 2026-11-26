---
name: video-logo-removal
description: Remove logos, brand names, wordmarks or printed text from clothing, bags and objects in real video footage (uniforms, delivery jackets, sponsor patches, branded bags) without losing quality - SAM 2 object tracking + LaMa inpainting + flow-guided temporal stabilization, with QA tools that catch leftovers and playback shimmer. Use this whenever someone wants a brand/logo/print taken out of a video clip, footage, reel, ad or short film - "remove the logo on his jacket", "get rid of the delivery-app branding on the uniform and bag", "blur out / clean the sponsor patch", "the logo is still visible / flickering in the hands", even if they don't say "inpainting" or "tracking". Not for still images, burned-in subtitles or overlay watermarks added in editing (those are a crop/delogo job).
---

# Video logo removal

Removes branding that is *physically in the scene* (printed on a jacket, a bag, a cup) from video, frame
by frame, and keeps everything else bit-for-bit close to the source. The hard parts are not the first
fill - they are finding every appearance of the logo, keeping hands/edges/captions intact, and making
the fills hold still during playback. This skill packages the tools and the checklist for those.

Read `references/pitfalls.md` before starting a job and again before declaring it done.
`references/config.md` documents the project config.

## Setup (once per machine)

```bash
bash <this skill's base directory>/scripts/setup.sh
```
Creates `~/.cache/video-logo-removal/{venv,models}`: PyTorch, OpenCV, SAM 2 (patched to run on Apple
MPS), SAM 2.1 base+ (~320 MB) and LaMa big-lama (~200 MB) weights. **Ask the user before the first run**
(it downloads ~600 MB from PyPI, GitHub and Meta's server). Needs ffmpeg and git.

Run every script with that venv's Python. Below, `PY=~/.cache/video-logo-removal/venv/bin/python`,
`SK=<this skill's base directory>/scripts` (e.g. `~/.claude/skills/video-logo-removal/scripts` for a manual
install; plugin installs live elsewhere - use the base directory you were given), `PROJ` = a project folder you create for this video
(put it in scratch space; it gets large - ~12 MB per processed 4K frame).

## Workflow

### 1. Inspect and scope
```bash
mkdir -p $PROJ && echo '{"video": "/abs/in.mp4"}' > $PROJ/config.json
$PY $SK/probe_shots.py $PROJ [--color U,V]     # shots + contact sheet PROJ/review/shots.jpg
```
Look at the contact sheet, then at full-resolution frames of every shot where the garment/object appears.
List every logo instance (chest, sleeves, back, bag, cap…) and tell the user what you found, including
secondary brands they did not mention - ask whether those should go too. `--color` (centred chroma of the
uniform, e.g. green ≈ `0,-25`) prints per-shot coverage, which helps find shots where it only peeks in.

Write `shots` (only the shots that need work) and `caption_band` (if the video has burned-in captions)
into config.json. Explain the approach and rough time cost to the user before heavy processing.

### 2. Prompt and track
```bash
$PY $SK/extract_frames.py $PROJ
$PY $SK/review.py grid $PROJ --shot 3 --frames 0,48,96 --crop 500,900,1080,1500   # coordinates (half-res)
# add objects + prompts to config.json, then:
$PY $SK/track.py $PROJ 3
$PY $SK/review.py overlay $PROJ --shot 3 --frames 0:96:12 --crop 0,800,1080,1600   # check every track
```
- One object per logo instance; prompt it on several frames (first, last, and where it turns/blurs).
- Track hands, watches, faces that overlap a logo as `"role": "protect"`.
- Fix drifting tracks with more prompts, point prompts (positive on letters, negative on the hand) or a
  `valid` range. Add a second object for letters the tracker misses in blurred frames.

### 3. Choose a mode per object

| situation | mode |
|---|---|
| logo inside a garment area (chest, back) | `flat` |
| logo reaching the garment's outline (sleeve against a wall, bag next to a door or another garment) | `edge` (`"bg": "nearest"` + `"edge_band": 10` when the outside is a thin rim / another solid colour) |
| SAM's blob also covers detail that must stay (cuff, folds, fingers) | `tight` |
| letters smeared by fast motion (whip pans) - inpainting would invent mismatched texture | `unblend` |

Modes can change mid-shot with `overrides` (e.g. `tight` while the hand is on the sleeve, `unblend` during
the whip). The fabric colour is estimated automatically per object; set `"fabric": [u, v]` if the log shows
a wrong colour.

### 4. Clean, review, iterate
```bash
$PY $SK/clean.py $PROJ 3
$PY $SK/review.py compare $PROJ --shot 3 --frames 0,24,48,72,96 --crop 1300,1900,2160,3000 --stages clean
$PY $SK/qa.py scan $PROJ 3 --stage clean
```
Look at every compare image (Read the PNG) at full resolution. Typical fixes: missed letters -> more
prompts / extra object; smudges at an edge -> `edge` mode or `bg: nearest`; damaged hand -> protect object;
ghost outline -> larger `dilate`/`extra` or `unblend`. Re-run only the shots you changed.

To add a second logo on top of approved work (e.g. a bag logo after the jacket is done), run only the new
objects on the approved frames: `clean.py $PROJ 3 --in stab --out bag --objects 20,21`, then
`stabilize.py $PROJ 3 --in bag --out bagstab --ref stab`, and render with `--stages bagstab,stab,clean`.

### 5. Stabilize for playback
```bash
$PY $SK/stabilize.py $PROJ 3          # clean -> stab
$PY $SK/qa.py wobble $PROJ 3 --stage stab
$PY $SK/review.py compare $PROJ --shot 3 --frames 40:52:1 --crop ... --stages clean,stab
```
Independent per-frame fills shimmer on playback even when every still looks right - users notice it
("something is moving in the hands"). Always stabilize. Put fast whip-pan ranges in `stabilize_skip`.

### 6. Render and verify
```bash
$PY $SK/render.py $PROJ --range 250 320 --out /tmp/preview.mp4      # optional quick preview
$PY $SK/render.py $PROJ                                              # full render + PSNR/SSIM report
$PY $SK/qa.py sweep $PROJ --video OUT.mp4                            # every frame, every shot
$PY $SK/review.py videos --a IN.mp4 --b OUT.mp4 --frames 1104,1110 --crop ...
```
Review every sweep sheet (most flags are zippers, stripes, wall edges - confirm each by eye). If the user
sends a screenshot of a problem, find the frame by template matching against the render, fix that shot,
then re-sweep the whole video: a missed spot usually means a whole missed shot.

## Reporting to the user

State plainly: which logos were removed and where (timestamps), what was deliberately left (other brands,
packaging), the output path, the measured quality (untouched frames ~45 dB PSNR / 0.996 SSIM = visually
identical; frame count, colour tags and audio copied), and any frames that are known to be imperfect
(e.g. a 1-second blur). Offer a half-speed side-by-side preview for subtle playback issues. Offer to
delete the project folder (it can be tens of GB).
