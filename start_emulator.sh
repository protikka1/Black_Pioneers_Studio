#!/bin/bash
# Start BlackPioneer Android Emulator
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Library/Android/sdk}}"
EMULATOR="${EMULATOR_BIN:-$SDK/emulator/emulator}"
ADB="${ADB_BIN:-$SDK/platform-tools/adb}"
AVD="${AVD_NAME:-BlackPioneer_API33}"

export ANDROID_SDK_ROOT="$SDK"
export ANDROID_HOME="$SDK"

echo "Starting emulator: $AVD"
"$EMULATOR" -avd "$AVD" -no-snapshot-load &
EMULATOR_PID=$!

echo "Emulator PID: $EMULATOR_PID"
echo "Waiting for device to boot..."
"$ADB" wait-for-device

echo "Waiting for boot animation to finish..."
until "$ADB" shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; do
    sleep 3
    echo "  still booting..."
done

echo ""
echo "✅ Emulator is ready!"
echo ""
echo "To install an APK:"
echo "  $ADB install bin/<your-app>.apk"
