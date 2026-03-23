@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo  JMV Agent v1.1 - Windows EXE + Android APK Auto Build
echo ============================================================
echo.

set WIN_OK=0
set APK_OK=0
set APK_FILE=

:: ── Windows EXE Build ─────────────────────────────────────────
echo [Windows] Building EXE with CJK font...
echo ------------------------------------------------------------
call "%~dp0build_windows.bat"
if exist "%~dp0dist\BrainAgent.exe" (
    set WIN_OK=1
    echo [Windows] SUCCESS: %~dp0dist\BrainAgent.exe
) else (
    echo [Windows] FAILED - check errors above
)

echo.

:: ── Android APK Build via WSL2 ────────────────────────────────
echo [Android] Checking WSL2 + Ubuntu...
echo ------------------------------------------------------------

:: 检查 wsl.exe 是否可用
where wsl.exe >nul 2>&1
if errorlevel 1 (
    echo [Android] SKIP - wsl.exe not found.
    echo   Please install WSL2: https://aka.ms/wsl
    set APK_OK=2
    goto :summary
)

:: 检查 Ubuntu 发行版
wsl.exe -d Ubuntu -e bash -c "echo wsl_ok" >nul 2>&1
if errorlevel 1 (
    echo [Android] Ubuntu not found in WSL2.
    echo   To fix:
    echo     1. Enable Hyper-V in BIOS (virtualization)
    echo     2. Run as Admin: wsl --install -d Ubuntu
    echo     3. Restart Windows, then re-run this script
    set APK_OK=2
    goto :summary
)

echo [Android] WSL2 + Ubuntu ready. Starting APK build...
wsl.exe -d Ubuntu bash "/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app/build_android.sh"

:: 检查 APK 产物
for /f "delims=" %%f in ('dir /b "%~dp0bin\*.apk" 2^>nul') do (
    set APK_FILE=%%f
    set APK_OK=1
)

:summary
echo.
echo ============================================================
echo  BUILD SUMMARY
echo ============================================================
if !WIN_OK!==1 (
    echo  [PASS] Windows EXE  : dist\BrainAgent.exe
) else (
    echo  [FAIL] Windows EXE
)

if !APK_OK!==1 (
    echo  [PASS] Android APK  : bin\!APK_FILE!
) else if !APK_OK!==2 (
    echo  [SKIP] Android APK  : WSL2/Ubuntu setup required
) else (
    echo  [FAIL] Android APK
)
echo ============================================================
echo.
pause
