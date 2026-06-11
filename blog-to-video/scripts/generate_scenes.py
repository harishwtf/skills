#!/usr/bin/env python3
"""
Generate scene files and Composition.tsx from platforms.json

Usage:
  python3 generate_scenes.py --platforms platforms.json

Generates:
  - src/scenes/S01_Intro.tsx (template — needs manual customization)
  - src/scenes/S02_PlatformName.tsx ... (data-driven, fully automatic)
  - src/scenes/SXX_Conclusion.tsx
  - src/Composition.tsx (TransitionSeries wiring)
"""

import json
import argparse
import re
from pathlib import Path


def sanitize_name(name: str) -> str:
    """Convert platform name to valid identifier: 'Webex Events' -> 'WebexEvents'"""
    return re.sub(r'[^a-zA-Z0-9]', '', name)


def generate_platform_scene(idx: int, platform: dict) -> str:
    sid = f"S{idx:02d}"
    safe_name = sanitize_name(platform["name"])
    export_name = f"{sid}_{safe_name}"

    strengths_arr = ",\n        ".join(f"'{s}'" for s in platform["strengths"])

    lines = [
        "import React from 'react';",
        "import { useCurrentFrame } from 'remotion';",
        "import { PlatformScene } from '../components/PlatformScene';",
        f"import {{ {sid}_BEATS }} from '../timing';",
        "",
        f"export const {export_name}: React.FC = () => {{",
        "  const frame = useCurrentFrame();",
        "  return (",
        "    <PlatformScene",
        "      frame={frame}",
        f'      number="{idx - 1:02d}"',
        f'      name="{platform["name"]}"',
    ]

    if platform.get("subName"):
        lines.append(f'      subName="{platform["subName"]}"')

    lines.append(f'      bestFor="{platform["bestFor"]}"')
    lines.append(f"      strengths={{[")
    lines.append(f"        {strengths_arr},")
    lines.append(f"      ]}}")
    lines.append(f'      limitation="{platform.get("limitation", "")}"')
    lines.append(f'      pricing="{platform["pricing"]}"')
    lines.append(f'      g2="{platform.get("g2", "")}"')
    lines.append(f"      beats={{{sid}_BEATS}}")
    lines.append("    />")
    lines.append("  );")
    lines.append("};")
    lines.append("")

    return "\n".join(lines)


def generate_intro_scene(platforms_config: dict) -> str:
    """Generate S01_Intro.tsx template with placeholders."""
    count = platforms_config["count"]
    title_lower = platforms_config["title"].lower()
    # Extract the subject part (e.g., "mobile event apps")
    subject = re.sub(r'^\d+\s+best\s+', '', title_lower, flags=re.IGNORECASE)

    return f"""import React from 'react';
import {{ AbsoluteFill, useCurrentFrame, interpolate, Easing }} from 'remotion';
import {{ COLORS, GRADIENTS, RADIUS }} from '../tokens';
import {{ fontFamily }} from '../fonts';
import {{ WordReveal }} from '../components/WordReveal';
import {{ S01_BEATS }} from '../timing';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = {{ extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const }};

export const S01_Intro: React.FC = () => {{
  const frame = useCurrentFrame();

  const bgOpacity = interpolate(frame, [0, 20], [0, 1], {{ ...clamp, easing: EASE_OUT }});

  // TODO: Replace with actual beat key from timing.ts
  const countBeat = (S01_BEATS as Record<string, number>)['APPS_IN'] ?? (S01_BEATS as Record<string, number>)['PLATFORMS_IN'] ?? 400;
  const countF = Math.max(0, frame - countBeat);
  const countScale = interpolate(countF, [0, 18], [0.6, 1], {{ ...clamp, easing: EASE_OUT }});
  const countOpacity = interpolate(countF, [0, 18], [0, 1], {{ ...clamp, easing: EASE_OUT }});

  const subtitleF = Math.max(0, frame - (countBeat + 12));
  const subtitleOpacity = interpolate(subtitleF, [0, 20], [0, 1], {{ ...clamp, easing: EASE_OUT }});
  const subtitleY = interpolate(subtitleF, [0, 20], [16, 0], {{ ...clamp, easing: EASE_OUT }});

  // TODO: Customize problem pills for this blog topic
  const problems = ['Problem one', 'Problem two', 'Problem three'];

  return (
    <AbsoluteFill style={{{{ backgroundColor: COLORS.BG, fontFamily, opacity: bgOpacity }}}}>
      <div
        style={{{{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at 50% 40%, rgba(132,61,245,0.12) 0%, transparent 65%)',
          pointerEvents: 'none',
        }}}}
      />

      <div
        style={{{{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 120px',
          gap: 0,
        }}}}
      >
        <div style={{{{ textAlign: 'center', maxWidth: 1100, marginBottom: 56 }}}}>
          {{/* TODO: Replace headline and subline with VO script text */}}
          <WordReveal
            text="Your headline from the VO script goes here."
            startAt={{S01_BEATS.TEXT_IN}}
            frame={{frame}}
            color={{COLORS.HEADING}}
            fontSize={{68}}
            fontWeight={{800}}
            lineHeight="80px"
            letterSpacing="-0.03em"
            stagger={{4}}
            wordDuration={{16}}
          />
          <div style={{{{ height: 24 }}}} />
          <WordReveal
            text="Your subline from the VO script goes here."
            startAt={{S01_BEATS.TEXT_IN + 40}}
            frame={{frame}}
            color={{COLORS.BODY}}
            fontSize={{32}}
            fontWeight={{500}}
            lineHeight="46px"
            letterSpacing="-0.01em"
            stagger={{3}}
            wordDuration={{14}}
          />
        </div>

        <div style={{{{ display: 'flex', gap: 16, marginBottom: 56 }}}}>
          {{problems.map((p, i) => {{
            const f = Math.max(0, frame - (S01_BEATS.TEXT_IN + 80 + i * 18));
            const op = interpolate(f, [0, 18], [0, 1], {{ ...clamp, easing: EASE_OUT }});
            const y = interpolate(f, [0, 18], [12, 0], {{ ...clamp, easing: EASE_OUT }});
            return (
              <div
                key={{p}}
                style={{{{
                  opacity: op,
                  transform: `translateY(${{y}}px)`,
                  padding: '10px 24px',
                  borderRadius: RADIUS.PILL,
                  background: COLORS.SURFACE,
                  border: `1px solid ${{COLORS.BORDER}}`,
                  fontSize: 20,
                  fontWeight: 600,
                  color: COLORS.BODY,
                  fontFamily,
                }}}}
              >
                {{p}}
              </div>
            );
          }})}}
        </div>

        <div
          style={{{{
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            opacity: subtitleOpacity,
            transform: `translateY(${{subtitleY}}px)`,
          }}}}
        >
          <div style={{{{ width: 60, height: 2, background: GRADIENTS.BRAND, borderRadius: 1 }}}} />
          <div style={{{{ fontSize: 26, fontWeight: 600, color: COLORS.MUTED, letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily }}}}>
            Here are the
          </div>
          <div
            style={{{{
              fontSize: 100,
              fontWeight: 800,
              background: GRADIENTS.BRAND,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              lineHeight: '1',
              letterSpacing: '-0.04em',
              opacity: countOpacity,
              transform: `scale(${{countScale}})`,
              filter: 'drop-shadow(0 0 20px rgba(132,61,245,0.5))',
            }}}}
          >
            {count}
          </div>
          <div style={{{{ fontSize: 26, fontWeight: 600, color: COLORS.MUTED, letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily }}}}>
            best {subject}
          </div>
          <div style={{{{ width: 60, height: 2, background: GRADIENTS.BRAND, borderRadius: 1 }}}} />
        </div>
      </div>
    </AbsoluteFill>
  );
}};
"""


def generate_conclusion_scene(idx: int) -> str:
    sid = f"S{idx:02d}"
    return f"""import React from 'react';
import {{ AbsoluteFill, Img, interpolate, Easing, useCurrentFrame, staticFile }} from 'remotion';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = {{ extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const }};

export const {sid}_Conclusion: React.FC = () => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {{ ...clamp, easing: EASE_OUT }});
  return (
    <AbsoluteFill style={{{{ opacity }}}}>
      <Img
        src={{staticFile('outro.png')}}
        style={{{{ width: '100%', height: '100%', objectFit: 'cover' }}}}
      />
    </AbsoluteFill>
  );
}};
"""


def generate_composition(platforms_config: dict) -> str:
    """Generate Composition.tsx with TransitionSeries wiring."""
    comp_id = platforms_config["compositionId"]
    comp_name = sanitize_name(comp_id)
    num_platforms = platforms_config["count"]
    platforms = platforms_config["platforms"]
    num_scenes = num_platforms + 2
    conclusion_sid = f"S{num_scenes:02d}"

    # Build imports
    imports = [
        "import React from 'react';",
        "import { AbsoluteFill, Audio, CalculateMetadataFunction, Sequence, staticFile } from 'remotion';",
        "import { TransitionSeries, linearTiming } from '@remotion/transitions';",
        "import { fade } from '@remotion/transitions/fade';",
        "",
        "import { fontFamily } from './fonts';",
        "import { DURATIONS, TOTAL_FRAMES, TRANSITION_FRAMES } from './timing';",
        "",
        "import { S01_Intro } from './scenes/S01_Intro';",
    ]

    for i, p in enumerate(platforms):
        sid = f"S{i+2:02d}"
        safe = sanitize_name(p["name"])
        imports.append(f"import {{ {sid}_{safe} }} from './scenes/{sid}_{safe}';")

    imports.append(f"import {{ {conclusion_sid}_Conclusion }} from './scenes/{conclusion_sid}_Conclusion';")
    imports.append("")

    # Build component
    lines = imports + [
        f"export type {comp_name}Props = Record<string, unknown>;",
        "",
        f"export const calculateMetadata: CalculateMetadataFunction<{comp_name}Props> = async () => {{",
        "  return {",
        "    durationInFrames: TOTAL_FRAMES,",
        "    fps: 30,",
        "    width: 1920,",
        "    height: 1080,",
        "  };",
        "};",
        "",
        "const T = TRANSITION_FRAMES;",
        "",
        f"export const {comp_name}: React.FC = () => {{",
        "  return (",
        "    <AbsoluteFill style={{ fontFamily }}>",
        "      <Sequence from={0}>",
        "        <Audio src={staticFile('voiceover.mp3')} />",
        "      </Sequence>",
        "",
        "      <TransitionSeries>",
        "        <TransitionSeries.Sequence durationInFrames={DURATIONS.S01} premountFor={30}>",
        "          <S01_Intro />",
        "        </TransitionSeries.Sequence>",
    ]

    for i, p in enumerate(platforms):
        sid = f"S{i+2:02d}"
        safe = sanitize_name(p["name"])
        lines.append("")
        lines.append("        <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: T })} />")
        lines.append("")
        lines.append(f"        <TransitionSeries.Sequence durationInFrames={{DURATIONS.{sid}}} premountFor={{30}}>")
        lines.append(f"          <{sid}_{safe} />")
        lines.append("        </TransitionSeries.Sequence>")

    lines.append("")
    lines.append("        <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: T })} />")
    lines.append("")
    lines.append(f"        <TransitionSeries.Sequence durationInFrames={{DURATIONS.{conclusion_sid}}} premountFor={{30}}>")
    lines.append(f"          <{conclusion_sid}_Conclusion />")
    lines.append("        </TransitionSeries.Sequence>")
    lines.append("      </TransitionSeries>")
    lines.append("    </AbsoluteFill>")
    lines.append("  );")
    lines.append("};")
    lines.append("")

    return "\n".join(lines)


def generate_root(platforms_config: dict) -> str:
    comp_id = platforms_config["compositionId"]
    comp_name = sanitize_name(comp_id)
    return f"""import React from 'react';
import {{ Composition }} from 'remotion';
import {{ {comp_name}, calculateMetadata }} from './Composition';

export const RemotionRoot: React.FC = () => {{
  return (
    <Composition
      id="{comp_id}"
      component={{{comp_name}}}
      calculateMetadata={{calculateMetadata}}
      defaultProps={{{{}}}}
    />
  );
}};
"""


def main():
    parser = argparse.ArgumentParser(description="Generate scene files from platforms.json")
    parser.add_argument("--platforms", default="platforms.json", help="Path to platforms.json config")
    parser.add_argument("--output-dir", default="src", help="Output directory for generated files")
    args = parser.parse_args()

    with open(args.platforms) as f:
        config = json.load(f)

    out = Path(args.output_dir)
    scenes_dir = out / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    platforms = config["platforms"]
    num_scenes = config["count"] + 2

    # Generate intro scene template
    intro_path = scenes_dir / "S01_Intro.tsx"
    if intro_path.exists():
        print(f"  SKIP {intro_path} (already exists — customize manually)")
    else:
        intro_path.write_text(generate_intro_scene(config))
        print(f"  CREATED {intro_path} (template — customize headline + problems)")

    # Generate platform scenes
    for i, platform in enumerate(platforms):
        sid = f"S{i+2:02d}"
        safe = sanitize_name(platform["name"])
        path = scenes_dir / f"{sid}_{safe}.tsx"
        path.write_text(generate_platform_scene(i + 2, platform))
        print(f"  CREATED {path}")

    # Generate conclusion
    conclusion_path = scenes_dir / f"S{num_scenes:02d}_Conclusion.tsx"
    conclusion_path.write_text(generate_conclusion_scene(num_scenes))
    print(f"  CREATED {conclusion_path}")

    # Generate Composition.tsx
    comp_path = out / "Composition.tsx"
    comp_path.write_text(generate_composition(config))
    print(f"  CREATED {comp_path}")

    # Generate Root.tsx
    root_path = out / "Root.tsx"
    root_path.write_text(generate_root(config))
    print(f"  CREATED {root_path}")

    print(f"\nDone! {len(platforms) + 2} scenes + Composition.tsx + Root.tsx generated.")
    print("Next: customize S01_Intro.tsx headline, subline, and problem pills.")


if __name__ == "__main__":
    main()
