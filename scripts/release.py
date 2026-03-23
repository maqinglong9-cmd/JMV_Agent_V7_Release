#!/usr/bin/env python3
"""
JMV智伴 一键发布脚本

功能：
  1. 读取 version.py 中的版本号
  2. 计算 dist/ 目录中已打包的 EXE/APK 的 SHA256
  3. 生成 latest.json 版本清单文件
  4. （可选）上传到 GitHub Releases

用法：
  python scripts/release.py
  python scripts/release.py --upload  # 同时上传到 GitHub Releases

依赖：
  --upload 模式需要安装 gh CLI 并已登录：https://cli.github.com/
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

# ── 项目根目录 ──────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from version import __version__, APP_NAME


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_artifact(pattern: str) -> str | None:
    """在 dist/ 目录中查找匹配 pattern 的文件"""
    dist = os.path.join(ROOT, "dist")
    for name in os.listdir(dist):
        if pattern.lower() in name.lower():
            return os.path.join(dist, name)
    return None


def build_latest_json(
    version: str,
    release_notes: str,
    windows_url: str,
    windows_sha256: str,
    android_url: str,
    android_sha256: str,
    linux_url: str = "",
    linux_sha256: str = "",
) -> dict:
    assets = {
        "windows": {"url": windows_url, "sha256": windows_sha256},
        "android": {"url": android_url, "sha256": android_sha256},
    }
    if linux_url:
        assets["linux"] = {"url": linux_url, "sha256": linux_sha256}
    return {
        "version": version,
        "release_notes": release_notes,
        "assets": assets,
    }


def main():
    parser = argparse.ArgumentParser(description="JMV智伴 发布脚本")
    parser.add_argument("--upload", action="store_true", help="上传到 GitHub Releases")
    parser.add_argument("--notes", default="", help="本次更新说明")
    args = parser.parse_args()

    version = __version__
    print(f"[release] 版本号: {version}")

    # ── 查找制品 ────────────────────────────────────────────
    exe_path   = find_artifact("BrainAgent.exe")
    apk_path   = find_artifact(".apk")
    linux_path = find_artifact("BrainAgent_linux")

    if not exe_path and not apk_path and not linux_path:
        print("[release] 错误：dist/ 目录中未找到任何制品，请先执行构建。")
        sys.exit(1)

    exe_sha256   = sha256_of(exe_path)   if exe_path   else ""
    apk_sha256   = sha256_of(apk_path)   if apk_path   else ""
    linux_sha256 = sha256_of(linux_path) if linux_path else ""

    print(f"[release] Windows EXE : {exe_path or '未找到'}")
    print(f"[release] Windows SHA256: {exe_sha256[:16]}..." if exe_sha256 else "")
    print(f"[release] Android APK : {apk_path or '未找到'}")
    print(f"[release] Android SHA256: {apk_sha256[:16]}..." if apk_sha256 else "")
    print(f"[release] Linux ELF   : {linux_path or '未找到'}")
    print(f"[release] Linux SHA256: {linux_sha256[:16]}..." if linux_sha256 else "")

    # ── 占位 URL（上传后替换）──────────────────────────────
    tag        = f"v{version}"
    base_url   = f"https://github.com/maqinglong9-cmd/JMV_Agent_V7_Release/releases/download/{tag}"
    exe_url    = f"{base_url}/{os.path.basename(exe_path)}"   if exe_path   else ""
    apk_url    = f"{base_url}/{os.path.basename(apk_path)}"   if apk_path   else ""
    linux_url  = f"{base_url}/{os.path.basename(linux_path)}" if linux_path else ""

    # ── 生成 latest.json ────────────────────────────��──────
    latest = build_latest_json(
        version       = version,
        release_notes = args.notes or f"JMV智伴 {version} 正式版",
        windows_url   = exe_url,
        windows_sha256= exe_sha256,
        android_url   = apk_url,
        android_sha256= apk_sha256,
        linux_url     = linux_url,
        linux_sha256  = linux_sha256,
    )

    out_path = os.path.join(ROOT, "latest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=2)

    print(f"[release] latest.json 已生成: {out_path}")

    # ── 上传到 GitHub Releases ─────────────────────────────
    if args.upload:
        print(f"[release] 正在创建 GitHub Release {tag} ...")
        artifacts = [p for p in [exe_path, apk_path, linux_path, out_path] if p and os.path.isfile(p)]
        cmd = [
            "gh", "release", "create", tag,
            "--title", f"{APP_NAME} {version}",
            "--notes", latest["release_notes"],
        ] + artifacts

        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode == 0:
            print(f"[release] 上传成功！Release: {tag}")
        else:
            print("[release] 上传失败，请检查 gh CLI 配置。")
            sys.exit(1)
    else:
        print("[release] 提示：使用 --upload 参数可同时上传到 GitHub Releases。")

    print("[release] 完成。")


if __name__ == "__main__":
    main()
