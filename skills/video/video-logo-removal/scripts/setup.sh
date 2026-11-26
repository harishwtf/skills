#!/usr/bin/env bash
# One-time setup for the video-logo-removal skill. Safe to re-run (skips what is already there).
#   - Python venv with PyTorch, OpenCV, SAM 2 (Meta, Apache-2.0)
#   - SAM 2.1 base+ checkpoint (~320 MB, Meta's official download server)
#   - LaMa big-lama TorchScript weights (~200 MB, Apache-2.0)
# Everything goes to ~/.cache/video-logo-removal (override with VLR_HOME). Needs ffmpeg + git on PATH.
set -euo pipefail
HOME_DIR="${VLR_HOME:-$HOME/.cache/video-logo-removal}"
VENV="$HOME_DIR/venv"
MODELS="$HOME_DIR/models"
mkdir -p "$MODELS"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found (macOS: brew install ffmpeg)"; exit 1; }
command -v git >/dev/null || { echo "git not found"; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  if command -v uv >/dev/null; then
    uv venv -q --python 3.12 "$VENV"
  else
    python3 -m venv "$VENV"
  fi
fi
PY="$VENV/bin/python"
if ! "$PY" -c "import torch, cv2, sam2" 2>/dev/null; then
  if command -v uv >/dev/null; then
    uv pip install -q --python "$PY" torch torchvision numpy opencv-python-headless pillow "git+https://github.com/facebookresearch/sam2.git"
  else
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install -q torch torchvision numpy opencv-python-headless pillow "git+https://github.com/facebookresearch/sam2.git"
  fi
fi

# SAM 2 stores its tracking memory in bfloat16, which crashes on Apple's MPS backend
# ("Destination NDArray and Accumulator NDArray cannot have different datatype"). Use float32 instead.
SAMPY=$("$PY" -c "import sam2, os; print(os.path.join(os.path.dirname(sam2.__file__), 'sam2_video_predictor.py'))")
if grep -q "maskmem_features.to(torch.bfloat16)" "$SAMPY"; then
  sed -i.bak 's/maskmem_features = maskmem_features.to(torch.bfloat16)/maskmem_features = maskmem_features.to(torch.float32)/' "$SAMPY"
  echo "patched SAM 2 for float32 memory (MPS compatible)"
fi

dl() { # url dest min_bytes
  if [ ! -s "$2" ] || [ "$(stat -f%z "$2" 2>/dev/null || stat -c%s "$2")" -lt "$3" ]; then
    echo "downloading $(basename "$2") ..."
    curl -fL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"
  fi
}
dl https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt "$MODELS/sam2.1_hiera_base_plus.pt" 300000000
dl https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt "$MODELS/big-lama.pt" 190000000

"$PY" - <<'EOF'
import torch, cv2, sam2
dev = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
print(f'ready: torch {torch.__version__}, opencv {cv2.__version__}, device {dev}')
EOF
echo "python: $PY"
