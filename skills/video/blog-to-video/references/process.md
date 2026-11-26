# Blog-to-Video Process

## Pipeline Overview

```
Blog post
  → Write VO_SCRIPT.txt
  → ElevenLabs → voiceover.mp3
  → run_whisper.py → whisper_output.json
  → generate_timing.py → timing.ts
  → generate_scenes.py → scene files + Composition.tsx
  → Customize S01_Intro.tsx
  → npx tsc --noEmit → npx remotion render → MP4
```

## Project Structure

```
<Blog Title>/
  src/
    index.ts              — registers composition with Remotion
    Root.tsx              — mounts the composition
    Composition.tsx       — TransitionSeries wiring (one Sequence per scene)
    timing.ts             — DURATIONS, TOTAL_FRAMES, all scene BEATS
    tokens.ts             — COLORS, FONTS, TYPE, SPRING_CONFIG (from brand config)
    fonts.ts              — Google Font loading (from brand config)
    scenes/
      S01_Intro.tsx
      S02_...tsx
      ...
      SXX_Conclusion.tsx  — always a static outro
    components/
      FadeIn.tsx
      WordReveal.tsx
      PlatformScene.tsx   — for listicle videos
  public/
    voiceover.mp3
    outro.png
  VO_SCRIPT.txt
  whisper_output.json
  platforms.json
  run_whisper.py
  package.json
```

## VO Script Rules

- Each scene maps to one section of the blog
- No summary or "bottom line" paragraph at the end
- VO ends when content ends
- Keep it conversational

## Scene Naming

- `S01_Intro.tsx` — always the intro
- `S02_PlatformName.tsx` through `S{N+1}_PlatformName.tsx` — one per item
- `S{N+2}_Conclusion.tsx` — always a static outro with 120 frames

## Composition Wiring

- Uses `TransitionSeries` from `@remotion/transitions`
- Fade transitions between all scenes (TRANSITION_FRAMES = 15)
- Audio loaded at frame 0 via `<Sequence from={0}><Audio /></Sequence>`
- Resolution: 1920x1080 at 30fps

## Conclusion Scene

Always a static image fade-in:
- Duration: 120 frames
- outro.png from public/ with fade-in over 20 frames
- No animated content
