#!/usr/bin/env python3
"""Run Whisper word-level alignment on voiceover.mp3"""
import json
import whisper
import sys

model = whisper.load_model("base")
print("Transcribing with word timestamps...", flush=True)

result = model.transcribe(
    "public/voiceover.mp3",
    word_timestamps=True,
    language="en"
)

# Extract all word-level segments
words = []
for segment in result["segments"]:
    for word_info in segment.get("words", []):
        words.append({
            "word": word_info["word"].strip(),
            "start": round(word_info["start"], 3),
            "end": round(word_info["end"], 3),
            "start_frame": round(word_info["start"] * 30),
            "end_frame": round(word_info["end"] * 30),
        })

output = {
    "full_text": result["text"],
    "duration": result["segments"][-1]["end"] if result["segments"] else 0,
    "total_frames": round(result["segments"][-1]["end"] * 30) if result["segments"] else 0,
    "words": words
}

with open("whisper_output.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Total duration: {output['duration']:.1f}s = {output['total_frames']} frames at 30fps")
print(f"Word count: {len(words)}")
print(f"Saved to whisper_output.json")

# Print scene boundary candidates
print("\n--- Scene boundaries (searching for 'number N' phrases) ---")
number_words = [
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
]

for n_word in number_words:
    for i, w in enumerate(words):
        wc = w["word"].lower().strip(".,!?:-")
        if wc == "number" and i + 1 < len(words):
            nc = words[i + 1]["word"].lower().strip(".,!?:-")
            if nc == n_word:
                print(f"  'number {n_word}' -> frame {w['start_frame']} (t={w['start']:.2f}s)")
                break

# Also look for "here are" (intro beat)
for i, w in enumerate(words):
    if w["word"].lower().strip(".,!?:-") == "here":
        print(f"\n  'here' -> frame {w['start_frame']} (t={w['start']:.2f}s)  [potential intro beat]")
        break

# Look for "bottom line" (should NOT exist per guidelines)
for i, w in enumerate(words):
    wc = w["word"].lower().strip(".,!?:-")
    if wc == "bottom" and i + 1 < len(words):
        nc = words[i + 1]["word"].lower().strip(".,!?:-")
        if nc == "line":
            print(f"\n  WARNING: 'bottom line' found at frame {w['start_frame']} — VO should NOT have a summary paragraph!")
            break
