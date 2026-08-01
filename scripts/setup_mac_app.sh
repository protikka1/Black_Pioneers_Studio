#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="Black Pioneers Studio.app"
APP_SRC="$PROJECT_ROOT/dist/$APP_NAME"
APP_DST="$HOME/Applications/$APP_NAME"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/setup_mac_app.sh [--rebuild] [--open]

Options:
  --rebuild   Rebuild the .app bundle before installing
  --open      Open the installed app after install

Default behavior:
  - If dist app exists: install only
  - If dist app missing: build then install
EOF
}

REBUILD=false
OPEN_APP=false

for arg in "$@"; do
  case "$arg" in
    --rebuild)
      REBUILD=true
      ;;
    --open)
      OPEN_APP=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      usage
      exit 1
      ;;
  esac
done

if [[ "$REBUILD" == "true" || ! -d "$APP_SRC" ]]; then
  echo "Building macOS app bundle..."
  bash "$PROJECT_ROOT/scripts/build_mac_desktop_app.sh"
fi

if [[ ! -d "$APP_SRC" ]]; then
  echo "Build failed: $APP_SRC not found"
  exit 1
fi

mkdir -p "$HOME/Applications"
rm -rf "$APP_DST"
cp -R "$APP_SRC" "$APP_DST"

echo "Installed: $APP_DST"

echo "Tip: Open once from Applications, then Keep in Dock."

if [[ "$OPEN_APP" == "true" ]]; then
  open "$APP_DST"
fi
