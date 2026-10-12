#!/usr/bin/env bash
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "DMG creation requires macOS and hdiutil."
  exit 1
fi
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"
bash scripts/build_mac_desktop_app.sh
STAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/black-pioneers-dmg.XXXXXX")"
trap 'rm -rf "$STAGE_DIR"' EXIT
# ditto preserves the symlinks required by PyInstaller's macOS bundle layout.
ditto "dist/Black Pioneers Studio.app" "$STAGE_DIR/Black Pioneers Studio.app"
ln -s /Applications "$STAGE_DIR/Applications"
DMG_PATH="$PROJECT_ROOT/dist/Black-Pioneers-Studio-macos-$(uname -m).dmg"
hdiutil create -volname "Black Pioneers Studio" -srcfolder "$STAGE_DIR" \
  -format UDZO -ov "$DMG_PATH"
hdiutil verify "$DMG_PATH"
if [[ -n "${BLACK_PIONEERS_CODESIGN_IDENTITY:-}" ]]; then
  codesign --force --sign "$BLACK_PIONEERS_CODESIGN_IDENTITY" "$DMG_PATH"
fi
if [[ -n "${BLACK_PIONEERS_NOTARY_PROFILE:-}" ]]; then
  if [[ -z "${BLACK_PIONEERS_CODESIGN_IDENTITY:-}" ]]; then
    echo "Notarization requires BLACK_PIONEERS_CODESIGN_IDENTITY."
    exit 1
  fi
  xcrun notarytool submit "$DMG_PATH" --keychain-profile "$BLACK_PIONEERS_NOTARY_PROFILE" --wait
  xcrun stapler staple "$DMG_PATH"
  xcrun stapler validate "$DMG_PATH"
fi
echo "DMG ready: $DMG_PATH"
echo "Internet is required for Microsoft Edge TTS narration."
