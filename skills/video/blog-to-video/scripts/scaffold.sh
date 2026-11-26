#!/usr/bin/env bash
#
# Scaffold a new blog-to-video project using a brand config
#
# Usage:
#   ./scaffold.sh "15 Best Webinar Platforms" WebinarPlatforms 15 zuddl
#
# Args:
#   $1 — Project folder name
#   $2 — Composition ID (PascalCase, no spaces)
#   $3 — Number of items
#   $4 — Brand name (must have brands/<name>/brand-config.json)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"

PROJECT_NAME="${1:?Usage: scaffold.sh <project-name> <composition-id> <count> <brand-name>}"
COMP_ID="${2:?Usage: scaffold.sh <project-name> <composition-id> <count> <brand-name>}"
COUNT="${3:?Usage: scaffold.sh <project-name> <composition-id> <count> <brand-name>}"
BRAND_NAME="${4:?Usage: scaffold.sh <project-name> <composition-id> <count> <brand-name>}"

PROJECT_DIR="$ROOT_DIR/$PROJECT_NAME"
BRAND_DIR="$ROOT_DIR/brands/$BRAND_NAME"
BRAND_CONFIG="$BRAND_DIR/brand-config.json"

if [ -d "$PROJECT_DIR" ]; then
  echo "ERROR: Project directory already exists: $PROJECT_DIR"
  exit 1
fi

if [ ! -f "$BRAND_CONFIG" ]; then
  echo "ERROR: Brand config not found: $BRAND_CONFIG"
  echo "Run brand setup first: python3 $SKILL_DIR/scripts/generate_tokens.py --brand <config> --output brands/$BRAND_NAME/"
  exit 1
fi

echo "Creating project: $PROJECT_NAME"
echo "  Composition ID: $COMP_ID"
echo "  Platform count: $COUNT"
echo "  Brand: $BRAND_NAME"
echo ""

# Create directory structure
mkdir -p "$PROJECT_DIR/src/scenes"
mkdir -p "$PROJECT_DIR/src/components"
mkdir -p "$PROJECT_DIR/public"

# Generate tokens.ts and fonts.ts from brand config
python3 "$SKILL_DIR/scripts/generate_tokens.py" --brand "$BRAND_CONFIG" --output "$PROJECT_DIR/src/"

# Copy shared components
cp "$SKILL_DIR/shared/components/FadeIn.tsx" "$PROJECT_DIR/src/components/FadeIn.tsx"
cp "$SKILL_DIR/shared/components/WordReveal.tsx" "$PROJECT_DIR/src/components/WordReveal.tsx"
cp "$SKILL_DIR/shared/components/PlatformScene.tsx" "$PROJECT_DIR/src/components/PlatformScene.tsx"

# Copy outro image from brand config path
OUTRO_SOURCE=$(python3 -c "import json; c=json.load(open('$BRAND_CONFIG')); print(c.get('outro_image_source',''))")
if [ -n "$OUTRO_SOURCE" ] && [ -f "$ROOT_DIR/$OUTRO_SOURCE" ]; then
  cp "$ROOT_DIR/$OUTRO_SOURCE" "$PROJECT_DIR/public/outro.png"
  echo "  Copied outro.png from $OUTRO_SOURCE"
elif [ -f "$BRAND_DIR/outro.png" ]; then
  cp "$BRAND_DIR/outro.png" "$PROJECT_DIR/public/outro.png"
  echo "  Copied outro.png from brand directory"
else
  echo "  WARNING: No outro image found — copy manually to public/outro.png"
fi

# Copy run_whisper.py
cp "$SKILL_DIR/scripts/run_whisper.py" "$PROJECT_DIR/run_whisper.py"

# Generate index.ts
cat > "$PROJECT_DIR/src/index.ts" << 'EOF'
import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
EOF

# Generate package.json
SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')
cat > "$PROJECT_DIR/package.json" << EOF
{
  "name": "$SLUG",
  "version": "1.0.0",
  "description": "$PROJECT_NAME — video",
  "scripts": {
    "start": "npx remotion studio",
    "build": "npx remotion render $COMP_ID out/video.mp4"
  },
  "dependencies": {
    "@remotion/cli": "^4.0.434",
    "@remotion/google-fonts": "^4.0.434",
    "@remotion/media": "4.0.434",
    "@remotion/transitions": "^4.0.434",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "remotion": "4.0.434"
  },
  "devDependencies": {
    "@types/react": "18.3.1",
    "@types/react-dom": "18.3.1",
    "typescript": "5.4.5"
  }
}
EOF

# Generate tsconfig.json
cat > "$PROJECT_DIR/tsconfig.json" << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "noEmit": true
  },
  "include": ["src"]
}
EOF

# Generate remotion.config.ts
cat > "$PROJECT_DIR/remotion.config.ts" << 'EOF'
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
EOF

# Generate platforms.json template
PLATFORMS_ENTRIES=""
for i in $(seq 1 "$COUNT"); do
  COMMA=""
  if [ "$i" -lt "$COUNT" ]; then
    COMMA=","
  fi
  PLATFORMS_ENTRIES="$PLATFORMS_ENTRIES
    {
      \"name\": \"Platform $i\",
      \"bestFor\": \"Best for ...\",
      \"strengths\": [\"Strength 1\", \"Strength 2\", \"Strength 3\"],
      \"strength_keywords\": [\"keyword1\", \"keyword2\", \"keyword3\"],
      \"limitation\": \"Watch out for...\",
      \"pricing\": \"Custom pricing\",
      \"g2\": \"4.5 / 5\",
      \"name_keyword\": \"platform\",
      \"g2_keyword\": [\"4\", \"5\"]
    }$COMMA"
done

cat > "$PROJECT_DIR/platforms.json" << EOF
{
  "title": "$PROJECT_NAME",
  "compositionId": "$COMP_ID",
  "count": $COUNT,
  "intro_beat_key": "PLATFORMS_IN",
  "intro_keywords": ["here"],
  "platforms": [$PLATFORMS_ENTRIES
  ]
}
EOF

# Create VO_SCRIPT.txt template
cat > "$PROJECT_DIR/VO_SCRIPT.txt" << EOF
$PROJECT_NAME
$(printf '=%.0s' $(seq 1 ${#PROJECT_NAME}))

[Opening hook — describe the problem your audience faces]

[Bridge — "Here are the $COUNT best..."]

Number one. [Platform]. [Strength 1]. [Strength 2]. [Strength 3]. Caveat — [limitation]. [Pricing]. [G2 score] on G2.

Number two. [Platform]. ...

[Repeat for all $COUNT items — NO summary paragraph at the end]
EOF

echo ""
echo "Project scaffolded at: $PROJECT_DIR"
echo "  Brand: $BRAND_NAME"
echo ""
echo "Next steps:"
echo "  1. Fill in VO_SCRIPT.txt"
echo "  2. Generate voiceover MP3 (ElevenLabs) -> public/voiceover.mp3"
echo "  3. cd \"$PROJECT_DIR\" && python3 run_whisper.py"
echo "  4. Fill in platforms.json with real data + keywords"
echo "  5. python3 $SKILL_DIR/scripts/generate_timing.py"
echo "  6. python3 $SKILL_DIR/scripts/generate_scenes.py"
echo "  7. Customize src/scenes/S01_Intro.tsx"
echo "  8. npm install && npx tsc --noEmit && npm run build"
