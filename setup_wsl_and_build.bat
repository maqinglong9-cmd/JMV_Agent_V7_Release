@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo  JMV Agent - WSL2 Ubuntu 初始化 + Android APK 打包
echo ============================================================
echo.

:: ── Step 1: 确认 WSL Ubuntu 是否存在 ──────────────────────────
echo [1/4] 检查 WSL2 Ubuntu...
wsl.exe -d Ubuntu -u root -e bash -c "echo wsl_ok" >nul 2>&1
if errorlevel 1 (
    echo       Ubuntu 未找到，正在安装...
    wsl.exe --install -d Ubuntu --no-launch
    if errorlevel 1 (
        echo [错误] Ubuntu 安装失败。请确认已重启系统后再运行此脚本。
        pause
        exit /b 1
    )
    :: 等待安装完成
    timeout /t 5 /nobreak >nul
    wsl.exe -d Ubuntu -u root -e bash -c "echo wsl_ok" >nul 2>&1
    if errorlevel 1 (
        echo [错误] Ubuntu 安装后仍无法启动，请手动运行: wsl -d Ubuntu
        pause
        exit /b 1
    )
)
echo [OK] WSL2 Ubuntu 就绪

:: ── Step 2: 一键初始化 Ubuntu 环境（root 模式，无需交互）──────
echo [2/4] 初始化 Ubuntu + 安装构建工具...
wsl.exe -d Ubuntu -u root -e bash -c "
set -e
echo '--- 更新 apt ---'
apt-get update -qq

echo '--- 安装 Java + 构建工具 ---'
apt-get install -y -qq openjdk-17-jdk python3-pip python3-venv \
    git zip unzip autoconf libtool pkg-config \
    libffi-dev libssl-dev build-essential ccache \
    2>&1 | tail -5

echo '--- 安装 buildozer + cython ---'
pip3 install --upgrade pip -q
pip3 install 'buildozer==1.5.0' 'cython==0.29.33' -q

echo '--- 验证 ---'
buildozer --version
java -version 2>&1 | head -1
echo 'Ubuntu 环境初始化完成'
"
if errorlevel 1 (
    echo [错误] Ubuntu 环境初始化失败，请查看错误信息
    pause
    exit /b 1
)
echo [OK] Ubuntu 构建环境就绪

:: ── Step 3: 打包 Android APK ──────────────────────────────────
echo [3/4] 开始打包 Android APK（首次约需 30-60 分钟）...
wsl.exe -d Ubuntu -u root -e bash "/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/build_android.sh"
if errorlevel 1 (
    echo [错误] Android 打包失败，请查看上方错误信息
    pause
    exit /b 1
)

:: ── Step 4: 检查结果 ──────────────────────────────────────────
echo [4/4] 检查打包结果...
set APK_FOUND=0
for /f "delims=" %%f in ('dir /b "%~dp0bin\*.apk" 2^>nul') do (
    echo [成功] APK 文件: %~dp0bin\%%f
    set APK_FOUND=1
)

if !APK_FOUND!==0 (
    echo [失败] 未找到 APK 文件
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [全部完成] Android APK 打包成功！
echo  安装到设备: adb install bin\*.apk
echo ============================================================
pause
