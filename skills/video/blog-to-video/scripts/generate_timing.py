#!/usr/bin/env python3
"""
Generate timing.ts from whisper_output.json + platforms.json

Usage:
  python3 generate_timing.py                          # uses defaults in current dir
  python3 generate_timing.py --whisper whisper_output.json --platforms platforms.json

Input: whisper_output.json (from run_whisper.py)
       platforms.json (scene config with platform names and beat keywords)

Output: src/timing.ts with correct DURATIONS, TOTAL_FRAMES, and per-scene BEATS
"""

import json
import argparse
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Union


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def find_word_frame(words: list, target: str, after_frame: int = 0) -> Optional[int]:
    """Find the start_frame of the first word matching target after a given frame."""
    target_lower = target.lower().strip(".,!?:-")
    for w in words:
        if w["start_frame"] < after_frame:
            continue
        if w["word"].lower().strip(".,!?:-") == target_lower:
            return w["start_frame"]
    return None


def find_phrase_frame(words: list, phrase_words: List[str], after_frame: int = 0) -> Optional[int]:
    """Find start_frame of a multi-word phrase after a given frame."""
    targets = [w.lower().strip(".,!?:-") for w in phrase_words]
    for i, w in enumerate(words):
        if w["start_frame"] < after_frame:
            continue
        wc = w["word"].lower().strip(".,!?:-")
        if wc == targets[0]:
            match = True
            for j in range(1, len(targets)):
                if i + j >= len(words):
                    match = False
                    break
                nc = words[i + j]["word"].lower().strip(".,!?:-")
                if nc != targets[j]:
                    match = False
                    break
            if match:
                return w["start_frame"]
    return None


NUMBER_WORDS = {
    1: ["number", "one"],
    2: ["number", "two"],
    3: ["number", "three"],
    4: ["number", "four"],
    5: ["number", "five"],
    6: ["number", "six"],
    7: ["number", "seven"],
    8: ["number", "eight"],
    9: ["number", "nine"],
    10: ["number", "ten"],
    11: ["number", "eleven"],
    12: ["number", "twelve"],
    13: ["number", "thirteen"],
    14: ["number", "fourteen"],
    15: ["number", "fifteen"],
    16: ["number", "sixteen"],
    17: ["number", "seventeen"],
    18: ["number", "eighteen"],
    19: ["number", "nineteen"],
    20: ["number", "twenty"],
}


def detect_scene_boundaries(words: list, num_platforms: int) -> List[int]:
    """Auto-detect scene start frames by finding 'number one', 'number two', etc."""
    boundaries = []
    for n in range(1, num_platforms + 1):
        if n not in NUMBER_WORDS:
            print(f"  WARNING: No phrase mapping for number {n}", file=sys.stderr)
            continue
        phrase = NUMBER_WORDS[n]
        after = boundaries[-1] + 30 if boundaries else 0
        frame = find_phrase_frame(words, phrase, after_frame=after)
        if frame is not None:
            boundaries.append(frame)
            print(f"  Scene {n+1:02d}: 'number {phrase[-1]}' at frame {frame}")
        else:
            print(f"  WARNING: Could not find '{' '.join(phrase)}' in whisper output", file=sys.stderr)
    return boundaries


def find_beat_keywords(words: list, keywords: Dict[str, Union[str, List[str]]], scene_start: int, scene_end: int) -> Dict[str, int]:
    """
    Find beat frames for a scene given keyword mappings.
    keywords: { "STRENGTH1_IN": "full", "GAP_IN": "caveat", ... }
    Values can be a single word or a list of fallback words to try.
    """
    beats = {}
    for beat_name, kw in keywords.items():
        targets = [kw] if isinstance(kw, str) else kw
        found = False
        for target in targets:
            frame = find_word_frame(words, target, after_frame=scene_start)
            if frame is not None and frame < scene_end:
                beats[beat_name] = frame
                found = True
                break
        if not found:
            print(f"    WARNING: Beat '{beat_name}' keyword(s) {targets} not found in scene range [{scene_start}, {scene_end}]", file=sys.stderr)
    return beats


def generate_timing_ts(
    whisper_data: dict,
    platforms_config: dict,
    transition_frames: int = 15,
) -> str:
    words = whisper_data["words"]
    audio_end = whisper_data["total_frames"]
    num_platforms = platforms_config["count"]
    title = platforms_config["title"]
    platforms = platforms_config.get("platforms", [])

    print(f"\nAudio: {whisper_data['duration']:.1f}s = {audio_end} frames at 30fps")
    print(f"Detecting {num_platforms} scene boundaries...\n")

    # Detect scene boundaries (S02, S03, ..., S{N+1})
    boundaries = detect_scene_boundaries(words, num_platforms)

    if len(boundaries) != num_platforms:
        print(f"\nERROR: Expected {num_platforms} boundaries, found {len(boundaries)}", file=sys.stderr)
        print("You may need to manually specify scene_start frames in platforms.json", file=sys.stderr)
        sys.exit(1)

    T = transition_frames
    num_scenes = num_platforms + 2  # intro + platforms + conclusion

    # Scene start frames (S01 always starts at 0)
    scene_starts = [0] + boundaries
    # Add a virtual "end" for the last narrated scene
    scene_ends = boundaries + [audio_end]

    # Compute durations
    durations = {}
    scene_labels = ["Intro"]
    for i, p in enumerate(platforms):
        scene_labels.append(p.get("name", f"Platform {i+1}"))
    scene_labels.append("Conclusion")

    # S01
    durations["S01"] = boundaries[0]

    # S02 through S{N} (middle scenes)
    for i in range(num_platforms - 1):
        sid = f"S{i+2:02d}"
        durations[sid] = boundaries[i + 1] - boundaries[i] + T

    # Last narrated scene
    last_sid = f"S{num_platforms + 1:02d}"
    durations[last_sid] = (audio_end - boundaries[-1]) + T + 60

    # Conclusion
    conclusion_sid = f"S{num_platforms + 2:02d}"
    durations[conclusion_sid] = 120

    # Total frames
    num_transitions = num_scenes - 1
    total_frames = sum(durations.values()) - (num_transitions * T)

    # Build beats for each scene
    all_beats = {}

    # S01 beats — always TEXT_IN: 0, and an intro beat
    intro_beat_key = platforms_config.get("intro_beat_key", "APPS_IN")
    intro_keywords = platforms_config.get("intro_keywords", ["here"])
    intro_frame = None
    for kw in intro_keywords:
        intro_frame = find_word_frame(words, kw, after_frame=0)
        if intro_frame is not None and intro_frame < boundaries[0]:
            break
    all_beats["S01"] = {"TEXT_IN": 0}
    if intro_frame is not None:
        all_beats["S01"][intro_beat_key] = intro_frame
        print(f"  S01: {intro_beat_key} at frame {intro_frame}")

    # Platform scene beats
    default_beat_keywords = {
        "STRENGTH1_IN": None,  # filled from platform config
        "STRENGTH2_IN": None,
        "STRENGTH3_IN": None,
        "GAP_IN": ["caveat", "cavia", "watch"],
        "PRICING_IN": ["from", "custom", "pricing", "free"],
        "G2_IN": ["4", "3", "5"],
    }

    for i, platform in enumerate(platforms):
        sid = f"S{i+2:02d}"
        scene_start = boundaries[i]
        scene_end = boundaries[i + 1] if i + 1 < len(boundaries) else audio_end

        print(f"\n  {sid} ({platform.get('name', '?')}) — range [{scene_start}, {scene_end}]")

        beats = {}

        # NAME_IN: find platform name word
        name_word = platform.get("name_keyword", platform.get("name", "").split()[0])
        name_frame = find_word_frame(words, name_word, after_frame=scene_start)
        if name_frame and name_frame < scene_end:
            beats["NAME_IN"] = name_frame - scene_start + T
            print(f"    NAME_IN: abs {name_frame} -> local {beats['NAME_IN']}")

        # Strength keywords from platform config
        strength_keywords = platform.get("strength_keywords", [])
        for si, skw in enumerate(strength_keywords):
            beat_key = f"STRENGTH{si+1}_IN"
            targets = [skw] if isinstance(skw, str) else skw
            for target in targets:
                frame = find_word_frame(words, target, after_frame=scene_start)
                if frame and frame < scene_end:
                    beats[beat_key] = frame - scene_start + T
                    print(f"    {beat_key}: abs {frame} -> local {beats[beat_key]}")
                    break

        # GAP_IN
        gap_keywords = platform.get("gap_keyword", ["caveat", "cavia", "watch"])
        if isinstance(gap_keywords, str):
            gap_keywords = [gap_keywords]
        for gkw in gap_keywords:
            frame = find_word_frame(words, gkw, after_frame=scene_start)
            if frame and frame < scene_end:
                beats["GAP_IN"] = frame - scene_start + T
                print(f"    GAP_IN: abs {frame} -> local {beats['GAP_IN']}")
                break

        # PRICING_IN
        pricing_keywords = platform.get("pricing_keyword", ["from", "custom"])
        if isinstance(pricing_keywords, str):
            pricing_keywords = [pricing_keywords]
        # Search backwards from G2 mention for pricing
        for pkw in pricing_keywords:
            frame = find_word_frame(words, pkw, after_frame=scene_start + (beats.get("GAP_IN", 0)))
            if frame and frame < scene_end:
                beats["PRICING_IN"] = frame - scene_start + T
                print(f"    PRICING_IN: abs {frame} -> local {beats['PRICING_IN']}")
                break

        # G2_IN
        g2_keywords = platform.get("g2_keyword", ["4", "3", "5"])
        if isinstance(g2_keywords, str):
            g2_keywords = [g2_keywords]
        # Search from near end of scene for the G2 rating number
        g2_search_start = scene_end - 120  # last ~4 seconds
        for gkw in g2_keywords:
            frame = find_word_frame(words, gkw, after_frame=max(scene_start, g2_search_start))
            if frame and frame < scene_end:
                beats["G2_IN"] = frame - scene_start + T
                print(f"    G2_IN: abs {frame} -> local {beats['G2_IN']}")
                break

        all_beats[sid] = beats

    # Conclusion beats
    all_beats[conclusion_sid] = {"FADE_IN": 0}

    # Generate TypeScript
    lines = []
    lines.append(f"// Timing — {title}")
    lines.append(f"// Derived from Whisper on public/voiceover.mp3 ({whisper_data['duration']:.2f}s, {audio_end} frames at 30fps)")
    lines.append("// Formula: D[1] = whisper_start[S02]; D[k] = whisper_start[k+1] - whisper_start[k] + T")
    lines.append("// local_frame = abs_whisper_frame - scene_whisper_start + T  (S01: local = abs_frame)")
    lines.append("")
    lines.append(f"export const TRANSITION_FRAMES = {T};")
    lines.append("")
    lines.append("export const DURATIONS = {")

    duration_keys = sorted(durations.keys(), key=lambda k: int(k[1:]))
    for i, sid in enumerate(duration_keys):
        label = scene_labels[i] if i < len(scene_labels) else ""
        # Add formula comment
        idx = int(sid[1:])
        if idx == 1:
            comment = f"Intro         — whisper_start[S02]"
        elif idx == num_platforms + 2:
            comment = f"Conclusion    — static outro"
        elif idx == num_platforms + 1:
            ws = boundaries[-1]
            comment = f"{label:14s}— ({audio_end} - {ws}) + {T} + 60"
        else:
            bi = idx - 2
            if bi + 1 < len(boundaries):
                comment = f"{label:14s}— {boundaries[bi+1]} - {boundaries[bi]} + {T}"
            else:
                comment = label
        lines.append(f"  {sid}: {durations[sid]},{'':4s}// {comment}")

    lines.append("} as const;")
    lines.append("")
    lines.append(f"export const TOTAL_FRAMES = {total_frames};")
    lines.append("")
    lines.append("// ─── SCENE BEATS (local frames) ──────────────────────────────────────────────")

    for sid in sorted(all_beats.keys(), key=lambda k: int(k[1:])):
        beats = all_beats[sid]
        lines.append("")
        lines.append(f"export const {sid}_BEATS = {{")
        for bk, bv in beats.items():
            lines.append(f"  {bk}: {bv},")
        lines.append("} as const;")

    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate timing.ts from Whisper output")
    parser.add_argument("--whisper", default="whisper_output.json", help="Path to whisper_output.json")
    parser.add_argument("--platforms", default="platforms.json", help="Path to platforms.json config")
    parser.add_argument("--output", default="src/timing.ts", help="Output path for timing.ts")
    args = parser.parse_args()

    whisper_data = load_json(args.whisper)
    platforms_config = load_json(args.platforms)

    ts_content = generate_timing_ts(whisper_data, platforms_config)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ts_content)

    print(f"\nGenerated {args.output}")
    print("Review the file and adjust any beats that weren't auto-detected.")


if __name__ == "__main__":
    main()
