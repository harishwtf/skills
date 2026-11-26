# Pitfalls (learned the hard way on a real 4K job)

Each of these produced a result the client could see during playback. Check for all of them before
calling a job done.

## Finding the branding
- **The obvious logo is never the only one.** A jacket had a chest logo, both forearm logos, a back logo and
  partial letters at a pocket edge. Look at the full-res frames of every shot, not just the hero shot.
- **Shots you think are clean usually aren't.** A logo fragment peeking between a customer's chin and hand,
  a big "G" sliding in at the frame edge for half a second, a sleeve logo on the *other* arm. Run
  `qa.py sweep` on the final render (it scans every frame, processed or not) and review every flagged run.
- **Other brands count too.** A delivery bag had its own logo (and a separate vertical word-mark under it).
  Ask the user whether secondary brands (bags, cups, packaging) should go before you render.
- Not everything light on a uniform is a logo: reflective stripes, zip pulls, flag patches, caption text.
  The detectors skip long thin stripes; verify the rest by eye.

## Tracking
- One box on one frame drifts. Prompt each object on several frames (start, end, every big change).
- Tracks jump to similar-looking things once the logo leaves the frame (a chest logo jumped to a wall
  painting). Check overlays at the end of every shot and set `valid`.
- Big motion blur: SAM often tracks only part of a smeared word. Add a second object on the missed part
  (same mode), limited with `valid` to the frames that need it.
- A box around a forearm logo also swallows the cuff / hand. Use point prompts (positive on letters,
  negative on the hand) or `tight` mode.

## Filling
- **Background smears into the garment.** When a logo touches the silhouette, a plain inpaint pulls wall /
  sofa / door colour into the sleeve (grey smudges on the arm). Use `edge` mode: the garment side is filled
  only from the garment, the outside only from the outside.
- **Thin dark blotches along an edge** came from hole pixels next to a sleeve being filled from a mix of the
  sleeve and a dark door. `"bg": "nearest"` fills each outside pixel from whatever is actually next to it.
- **Hands, watches, cuffs get damaged** when they overlap the hole. Track them as `role: "protect"`
  objects; never rely on colour rules to find skin (skin, wood doors and orange bags overlap in colour).
- **Faint ghost letters** remain when only the bright core of a blurred letter is filled: the halo around
  it is lighter than the fabric too. The hole builder uses hysteresis to include the halo; check for ghosts
  at full resolution.
- **Motion-blurred letters** (whip pans): inpainting invents texture that doesn't match the blur and looks
  like patches. `unblend` mode subtracts the semi-transparent letters instead and keeps the real folds.
- LaMa output is smoother than camera footage; `fix_region` adds matched grain. Without it fills look like
  flat plastic.
- Never touch captions: `caption_band` protects them and hides them from the inpainter (otherwise caption
  white bleeds into fills).

## Playback (the part single-frame checks miss)
- Each frame inpainted independently **shimmers on playback** even when every still looks perfect. Run
  `stabilize.py` on every processed shot, then `qa.py wobble` (median should be < 1, few pairs > 1.5).
- Stabilizing fast whip frames creates blotches (optical flow is unreliable there); list those ranges in
  `stabilize_skip`.
- Mode switches mid-shot (e.g. `tight` -> `edge`) can pop; review the frames on both sides of the switch
  with `review.py compare --frames a:b`.
- Look at consecutive-frame strips (`--frames a:b:1`), not only spaced samples.

## Delivery
- Keep the source untouched; render to a new file. Match frame rate, colour tags and copy audio as-is.
- Report PSNR/SSIM for untouched frames (should be ~45 dB / 0.995+), the frame count, and what was NOT
  changed (other brands, restaurant packaging) so the user can decide.
- The working data is huge (tens of GB for a 1-minute 4K clip). Offer to delete it at the end.
