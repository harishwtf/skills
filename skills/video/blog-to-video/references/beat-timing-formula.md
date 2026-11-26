# Beat Timing Formula

## Frame Conversion

Whisper gives timestamps in seconds. Convert to frames at 30fps:
```
frame = round(seconds * 30)
```

## Local Frame Calculation

Each scene has its own local frame counter. Convert absolute Whisper frames to scene-local frames:

```
local_frame = abs_whisper_frame - scene_whisper_start + T
```

Where `T = TRANSITION_FRAMES = 15`.

**S01 exception** (no incoming transition):
```
local_frame = abs_whisper_frame
```

## Scene Duration Formulas

Where `T = 15` (TRANSITION_FRAMES):

```
D[1]             = whisper_start[S02]
D[k]             = whisper_start[k+1] - whisper_start[k] + T
D[last narrated] = (audio_end - whisper_start[last]) + T + 60
D[conclusion]    = 120
```

The `+60` on the last narrated scene ensures the voiceover fully finishes before the outro transition begins. **Do not omit this.**

## TOTAL_FRAMES

```
TOTAL_FRAMES = sum(all durations) - (num_transitions * T)
```

Where `num_transitions = num_scenes - 1`.

## timing.ts Structure

```ts
export const TRANSITION_FRAMES = 15;

export const DURATIONS = {
  S01: ...,
  S02: ...,
  // ...
  SXX: 120,  // conclusion — static outro
} as const;

export const TOTAL_FRAMES = ...;

// One BEATS export per scene
export const S01_BEATS = { TEXT_IN: 0, PLATFORMS_IN: ... } as const;
export const S02_BEATS = { NAME_IN: ..., STRENGTH1_IN: ..., ... } as const;
// ...
export const SXX_BEATS = { FADE_IN: 0 } as const;
```

## Common Beat Keys for Listicle Scenes

- `TEXT_IN` — intro text reveal
- `PLATFORMS_IN` / `APPS_IN` — "here are the N best" moment
- `NAME_IN` — platform name spoken
- `STRENGTH1_IN`, `STRENGTH2_IN`, `STRENGTH3_IN` — each strength callout
- `GAP_IN` — "caveat" / "watch out" moment
- `PRICING_IN` — pricing info
- `G2_IN` — G2 rating mention
- `FADE_IN` — conclusion scene fade

## Verification

After generating timing.ts, verify:
1. Sum of DURATIONS - (transitions * 15) == TOTAL_FRAMES
2. D[last narrated] includes +60 buffer
3. D[conclusion] == 120
4. S01 beats use absolute frames (no +15)
5. S02+ beats use `abs - scene_start + 15`
