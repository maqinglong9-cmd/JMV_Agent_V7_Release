#!/bin/bash
set -e
APK_IN="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/bin/jmvagent-1.1.0-arm64-v8a_armeabi-v7a-release-unsigned.apk"
APK_ALIGNED="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/bin/jmvagent-1.1.0-aligned.apk"
APK_SIGNED="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/bin/jmvagent-1.1.0-signed.apk"
KS="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/jmv_release.keystore"
ZIPALIGN="/root/.buildozer/android/platform/android-sdk/build-tools/37.0.0-rc2/zipalign"
APKSIGNER="/root/.buildozer/android/platform/android-sdk/build-tools/37.0.0-rc2/apksigner"

echo "=== Step 1: zipalign ==="
$ZIPALIGN -v 4 "$APK_IN" "$APK_ALIGNED"
echo "zipalign OK"

echo "=== Step 2: apksigner ==="
$APKSIGNER sign --ks "$KS" --ks-key-alias jmvagent --ks-pass pass:jmvagent2024 --key-pass pass:jmvagent2024 --out "$APK_SIGNED" "$APK_ALIGNED"
echo "apksigner OK"

echo "=== Step 3: verify ==="
$APKSIGNER verify --verbose "$APK_SIGNED" 2>&1 | head -5

echo "=== Done ==="
ls -lh "$APK_SIGNED"
