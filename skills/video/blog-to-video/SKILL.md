---
name: blog-to-video
description: Convert a blog post into a Remotion video — handles brand setup, VO scripting, Whisper timing, scene generation, and rendering. Use when creating a new video from a blog, setting up a brand config, or managing the video pipeline.
disable-model-invocation: true
---

# Blog-to-Video Skill

Convert blog posts into polished Remotion videos with voiceover sync.

## Current State
- Working directory: !`pwd`
- Existing brands: !`ls brands/ 2>/dev/null || echo "No brands/ directory yet"`
- Existing projects: !`ls -d */ 2>/dev/null | grep -v -E '(video-toolkit|brands|Brand|Font|brand-consitency|\.claude|node_modules)' | head -20`

## Step 1: Determine Intent

Ask the user what they want to do:

1. **Set up a new brand** — Create a brand configuration (colors, fonts, style rules)
2. **Create a new video** — Full pipeline from blog to rendered video
3. **Resume a video in progress** — Pick up where they left off on an existing project

## Step 2: Brand Setup (if needed)

If no brand config exists yet, or user wants a new brand, collect these details:

### Required Brand Information

Ask the user for ALL of these. Do not guess — every brand is different:

**Identity:**
- Brand name (e.g., "Zuddl", "HubSpot", "Loom")
- Brand website URL (optional — to pull visual reference)

**Colors:**
- Background color (the main canvas bg — light or dark theme?)
- Surface/card color
- Heading text color
- Body text color
- Muted/secondary text color
- Primary accent color
- Primary dark accent color
- Border colors (soft + strong)
- Should the overall theme be light or dark?

**Typography:**
- Primary font (must be available in Google Fonts for @remotion/google-fonts)
- Font weights to load (e.g., 400, 500, 600, 700, 800)

**Visual Style:**
- Gradient direction and colors for brand accent
- Shadow color base (usually derived from primary — not black)
- Card border-radius range (e.g., 20-32px)
- Any specific design rules (e.g., "never use blue accents", "always round corners")

**Assets:**
- Path to outro/closing image (or should we generate a simple one?)

Once collected, generate `brands/<brand-name>/brand-config.json` using the schema from [templates/brand-config.json](templates/brand-config.json).

Then generate the brand's tokens and components:
```bash
python3 .claude/skills/blog-to-video/scripts/generate_tokens.py --brand brands/<brand-name>/brand-config.json --output brands/<brand-name>/
```

This creates:
- `brands/<brand-name>/tokens.ts`
- `brands/<brand-name>/fonts.ts`

## Step 3: Determine Video Type

Ask what type of video they want:

### Listicle (N Best X)
- Structure: Intro → N platform/item scenes → Outro
- Best for: "10 Best...", "8 Top...", "14 Leading..." blog posts
- Uses shared PlatformScene component for each item
- Each item shows: name, best-for tag, strengths, limitation, pricing, G2/rating

### Explainer (coming soon)
- Structure: Hook → Problem → Solution → Features → CTA
- Best for: Product launches, feature announcements

### Comparison (coming soon)
- Structure: Intro → Side-by-side → Winner → CTA
- Best for: "X vs Y" blog posts

## Step 4: Listicle Video Pipeline

Reference: [process.md](references/process.md) for detailed steps.

### 4a. Scaffold the project
```bash
bash .claude/skills/blog-to-video/scripts/scaffold.sh "<Title>" <CompositionId> <count> <brand-name>
```

### 4b. Write the VO Script
Create `VO_SCRIPT.txt` in the project root. Rules:
- Each scene maps to one topic/section
- **No summary paragraph at the end** — VO ends when content ends
- Structure: Opening hook → bridge → "Number one. Name. Strengths. Caveat. Pricing. G2."
- Keep it conversational, not robotic

### 4c. Generate Voiceover
User generates MP3 from their TTS provider (ElevenLabs, etc.) and places it at `public/voiceover.mp3`.

### 4d. Run Whisper
```bash
cd "<project-dir>" && python3 run_whisper.py
```
This creates `whisper_output.json` with word-level timestamps.

### 4e. Fill in platforms.json
Edit the generated `platforms.json` with real platform data:
- Names, strengths, limitations, pricing, G2 scores
- Keyword hints for beat detection (name_keyword, strength_keywords, etc.)

### 4f. Generate timing.ts
```bash
python3 .claude/skills/blog-to-video/scripts/generate_timing.py \
  --whisper whisper_output.json \
  --platforms platforms.json
```
Review output — adjust any beats that weren't auto-detected.

Reference: [beat-timing-formula.md](references/beat-timing-formula.md)

### 4g. Generate scene files
```bash
python3 .claude/skills/blog-to-video/scripts/generate_scenes.py \
  --platforms platforms.json
```
Then customize `src/scenes/S01_Intro.tsx` with:
- The actual headline from the VO script
- Problem pills specific to this blog topic
- Correct beat key names

### 4h. Build and Render
```bash
cd "<project-dir>" && npm install && npx tsc --noEmit && npx remotion render <CompositionId> out/video.mp4
```

## Brand Design Rules (enforced across all brands)

These rules apply regardless of brand:
- Cards: content-sized — never let flex:1 stretch sparse cards
- Card border-radius: must be within the brand's configured range
- Shadows: use brand's shadow base color, never plain black
- Accents: use only the brand's color family — no rogue hues
- Font: always load the brand's configured Google Font

## File References

- Brand config schema: [templates/brand-config.json](templates/brand-config.json)
- Platform config schema: [templates/platforms.json](templates/platforms.json)
- Process reference: [references/process.md](references/process.md)
- Timing math: [references/beat-timing-formula.md](references/beat-timing-formula.md)
- Video types: [references/video-types.md](references/video-types.md)
- Shared components: [shared/components/](shared/components/)
