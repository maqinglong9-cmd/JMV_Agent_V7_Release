"""在 WSL 中运行 buildozer 构建 APK，然后签名"""
import subprocess
import sys
import os

PROJECT = '/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app'
KEYSTORE = f'{PROJECT}/jmv_release.keystore'
UNSIGNED = f'{PROJECT}/bin/jmvagent-1.2.0-arm64-v8a_armeabi-v7a-release-unsigned.apk'
ALIGNED  = f'{PROJECT}/bin/jmvagent-1.2.0-aligned.apk'
SIGNED   = f'{PROJECT}/bin/jmvagent-1.2.0-release-signed.apk'
BUILD_TOOLS = '/root/.buildozer/android/platform/android-sdk/build-tools/37.0.0-rc2'

script = f"""
set -e
echo "=== Step 1: buildozer android release ==="
cd {PROJECT}
buildozer android release 2>&1
echo "=== Build done ==="
echo "=== Step 2: zipalign ==="
{BUILD_TOOLS}/zipalign -v 4 "{UNSIGNED}" "{ALIGNED}"
echo "=== Step 3: apksigner ==="
{BUILD_TOOLS}/apksigner sign \\
  --ks "{KEYSTORE}" \\
  --ks-key-alias jmvagent \\
  --ks-pass pass:jmvagent2024 \\
  --key-pass pass:jmvagent2024 \\
  --out "{SIGNED}" \\
  "{ALIGNED}"
echo "=== Step 4: verify ==="
{BUILD_TOOLS}/apksigner verify --verbose "{SIGNED}" 2>&1 | head -5
echo "=== All done ==="
ls -lh "{SIGNED}"
"""

result = subprocess.run(
    ['C:/Windows/System32/wsl.exe', '-d', 'Ubuntu', 'bash', '-c', script],
    capture_output=True,
    timeout=7200,
)

stdout = result.stdout.decode('utf-8', errors='replace')
stderr = result.stderr.decode('utf-8', errors='replace')
print(stdout[-3000:])
if stderr:
    print('STDERR:', stderr[-500:], file=sys.stderr)
print('Exit code:', result.returncode)
