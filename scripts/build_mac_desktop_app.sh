#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing virtual environment python at: $VENV_PYTHON"
  echo "Create it first: python3 -m venv .venv && source .venv/bin/activate"
  exit 1
fi

cd "$PROJECT_ROOT"

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install pyinstaller

"$VENV_PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "Black Pioneers Studio" \
  desktop_launcher.py

echo "Build complete. App bundle:"
echo "$PROJECT_ROOT/dist/Black Pioneers Studio.app"
