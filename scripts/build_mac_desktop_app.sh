#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Build the Mac app on macOS. Cross-compiling from Linux is not supported."
  exit 1
fi
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Create the environment first: python3 -m venv .venv"
  exit 1
fi
cd "$PROJECT_ROOT"
"$VENV_PYTHON" -m pip install -r requirements.txt -r requirements-mac-build.txt
FFMPEG_PATH="${BLACK_PIONEERS_FFMPEG:-$(command -v ffmpeg || true)}"
if [[ -z "$FFMPEG_PATH" ]]; then
  FFMPEG_PATH="$("$VENV_PYTHON" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
fi
if [[ ! -x "$FFMPEG_PATH" ]]; then
  echo "FFmpeg is unavailable: $FFMPEG_PATH"
  exit 1
fi
export BLACK_PIONEERS_FFMPEG="$FFMPEG_PATH"
"$VENV_PYTHON" -m PyInstaller --noconfirm --clean "Black Pioneers Studio.spec"
"$VENV_PYTHON" scripts/verify_mac_bundle.py "dist/Black Pioneers Studio.app"
echo "Verified app: $PROJECT_ROOT/dist/Black Pioneers Studio.app"
