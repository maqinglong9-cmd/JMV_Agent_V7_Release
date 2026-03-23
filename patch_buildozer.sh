#!/bin/bash
# 修补 buildozer root 检查 + pip --user 问题 + 运行 APK 打包

BUILDOZER_PKG="/opt/buildozer-env/lib/python3.12/site-packages/buildozer"

# 修补 1：root 检查（正确路径：opt/buildozer-env）
python3 - <<'EOF'
path = "/opt/buildozer-env/lib/python3.12/site-packages/buildozer/__init__.py"
with open(path, "r") as f:
    content = f.read()

patched = content.replace(
    "warn_on_root = self.config.getdefault('buildozer', 'warn_on_root', '1')",
    "warn_on_root = '0'  # patched: skip root prompt"
)

with open(path, "w") as f:
    f.write(patched)

if "patched: skip root prompt" in patched:
    print("PATCH1_OK: root check")
else:
    print("PATCH1_SKIP: already patched or not found")
EOF

# 修补 2：pip --user 问题（android.py 虚拟环境检测）
python3 - <<'EOF'
path = "/opt/buildozer-env/lib/python3.12/site-packages/buildozer/targets/android.py"
with open(path, "r") as f:
    content = f.read()

# 将 options = ["--user"] 改为 options = []（root 环境不需要 --user）
patched = content.replace(
    'options = ["--user"]',
    'options = []  # patched: root env, no --user needed'
)

with open(path, "w") as f:
    f.write(patched)

if "patched: root env, no --user needed" in patched:
    print("PATCH2_OK: pip --user removed")
else:
    print("PATCH2_SKIP: already patched or not found")
EOF

# 设置环境变量
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:/opt/buildozer-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export VIRTUAL_ENV=/opt/buildozer-env
export HOME=/root

# 进入项目并打包
cd /mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app
echo "=== 开始 buildozer android debug ==="
/opt/buildozer-env/bin/buildozer android debug
BUILD_STATUS=$?

# 检查产物
echo ""
if ls bin/*.apk 2>/dev/null | head -1; then
    APK=$(ls bin/*.apk | head -1)
    SIZE=$(du -sh "$APK" | cut -f1)
    echo "=== BUILD_SUCCESS: $APK ($SIZE) ==="
else
    echo "=== BUILD_FAILED: 未找到 APK ==="
fi

exit $BUILD_STATUS
