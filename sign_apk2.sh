#!/bin/bash
set -e
ZIPALIGN="/root/.buildozer/android/platform/android-sdk/build-tools/37.0.0-rc2/zipalign"
APKSIGNER="/root/.buildozer/android/platform/android-sdk/build-tools/37.0.0-rc2/apksigner"
KS="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/jmv_release.keystore"
APK_IN="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/bin/jmvagent-1.1.0-arm64-v8a_armeabi-v7a-release-unsigned.apk"
APK_OUT="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/bin/jmvagent-1.1.0-release-signed.apk"
TMP="/tmp/jmvagent-aligned.apk"
echo "zipalign..."
$ZIPALIGN -v 4 "$APK_IN" "$TMP"
echo "apksigner..."
$APKSIGNER sign --ks "$KS" --ks-key-alias jmvagent --ks-pass pass:jmvagent2024 --key-pass pass:jmvagent2024 --out "$APK_OUT" "$TMP"
echo "verify..."
$APKSIGNER verify --verbose "$APK_OUT" | head -3
ls -lh "$APK_OUT"
echo "DONE"
