#!/bin/bash
# JMV Agent - Android APK 全自动打包脚本
# 用法：
#   Debug:   bash build_android.sh
#   Release: bash build_android.sh --release
#   清理:    bash build_android.sh --clean
#   全新:    bash build_android.sh --clean --release

set -e

echo "============================================================"
echo " JMV Agent - Android APK 全自动打包脚本"
echo "============================================================"

PROJECT_DIR="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app"

# ── 参数解析 ─────────────────────────────────────────────────
BUILD_TYPE="debug"
DO_CLEAN=0
for arg in "$@"; do
    case $arg in
        --release) BUILD_TYPE="release" ;;
        --clean)   DO_CLEAN=1 ;;
    esac
done
echo "[模式] 构建类型: $BUILD_TYPE"

# ── 检查项目目录 ──────────────────────────────────────────────
if [ ! -d "$PROJECT_DIR" ]; then
    echo "[错误] 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# ── 检查是否在 WSL2 内运行 ────────────────────────────────────
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "[警告] 当前不在 WSL2 环境中"
    exit 1
fi
echo "[检测] WSL2 环境确认 OK"

# ── 从 version.py 读取版本号并注入 buildozer.spec ─────────────
VERSION=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from version import __version__
print(__version__)
" 2>/dev/null || echo "1.1.0")
echo "[版本] 当前版本: $VERSION"

# 同步 buildozer.spec 中的版本号
sed -i "s/^version = .*/version = $VERSION/" "$PROJECT_DIR/buildozer.spec"
echo "[版本] buildozer.spec version 已同步为 $VERSION"

# ── 第一步：安装系统依赖 ──────────────────────────────────────
echo "[1/4] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip python3-venv git zip unzip \
    openjdk-17-jdk \
    autoconf libtool pkg-config \
    libffi-dev libssl-dev \
    build-essential \
    ccache

export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
echo "JAVA_HOME=$JAVA_HOME"

# ── 第二步：安装 Buildozer + Cython ──────────────────────────
echo "[2/4] 安装 Buildozer + Cython..."
pip3 install --upgrade pip --quiet
pip3 install "buildozer==1.5.0" "cython==0.29.33"
buildozer --version
echo "[OK] Buildozer 就绪"

# ── 第三步：进入项目目录 ──────────────────────────────────────
echo "[3/4] 进入项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

if [ "$DO_CLEAN" = "1" ]; then
    echo "[清理] 删除 .buildozer 缓存..."
    rm -rf .buildozer
fi

# ── 第四步：打包 ─────────────────────────────────────────────
echo "[4/4] 开始打包 Android APK ($BUILD_TYPE)..."
echo "      首次构建需下载 Android SDK/NDK，约需 30-60 分钟"

if [ "$BUILD_TYPE" = "release" ]; then
    # Release 包：需要签名密钥
    KEYSTORE="$PROJECT_DIR/jmv_release.keystore"
    if [ ! -f "$KEYSTORE" ]; then
        echo "[签名] 未找到签名密钥，自动生成 jmv_release.keystore..."
        keytool -genkey -v \
            -keystore "$KEYSTORE" \
            -alias jmvagent \
            -keyalg RSA -keysize 2048 \
            -validity 10000 \
            -storepass jmvagent2024 \
            -keypass jmvagent2024 \
            -dname "CN=JMV Agent, OU=JMV, O=JMV, L=Beijing, ST=Beijing, C=CN" \
            2>/dev/null
        echo "[签名] 密钥已生成: $KEYSTORE"
        echo "[签名] ⚠️  请妥善保存此密钥文件，更新应用时必须使用同一密钥！"
    fi

    # 配置 buildozer.spec 签名
    if ! grep -q "android.keystore" "$PROJECT_DIR/buildozer.spec"; then
        cat >> "$PROJECT_DIR/buildozer.spec" << EOF

# Release 签名配置（由 build_android.sh 自动添加）
android.keystore = %(source.dir)s/jmv_release.keystore
android.keystore_passwd = jmvagent2024
android.keyalias = jmvagent
android.keyalias_passwd = jmvagent2024
EOF
        echo "[签名] buildozer.spec 签名配置已写入"
    fi

    buildozer android release
else
    buildozer android debug
fi

# ── 验证产物 ──────────────────────────────────────────────────
APK=$(ls bin/*.apk 2>/dev/null | tail -1)
if [ -n "$APK" ]; then
    SIZE=$(du -sh "$APK" | cut -f1)
    # 重命名为含版本号的规范文件名
    OUTNAME="bin/JMVAgent-${VERSION}-${BUILD_TYPE}.apk"
    [ "$APK" != "$OUTNAME" ] && cp "$APK" "$OUTNAME" 2>/dev/null || true
    echo ""
    echo "============================================================"
    echo " [成功] Android 打包完成！"
    echo " 产物路径: $APK ($SIZE)"
    echo " 规范命名: $OUTNAME"
    echo " 安装到设备: adb install \"$APK\""
    echo "============================================================"
else
    echo "[错误] 打包失败"
    exit 1
fi
