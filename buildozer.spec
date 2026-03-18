[app]
title = JMV智伴
package.name = jmvagent
package.domain = org.jmv
source.dir = .
source.include_exts = py,png,jpg,json,kv,ttc,ttf
source.exclude_dirs = venv311,tests,.buildozer,dist,build,__pycache__,.git,.github,scripts
version = 1.2.0

requirements = python3,kivy==2.3.0

# 包含字体目录（CJK 中文字体）
source.include_patterns = fonts/*.ttc,fonts/*.ttf,jmv_workspace/*

orientation = portrait
fullscreen = 0

# 图标和启动画面（需自行提供图片文件）
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, REQUEST_INSTALL_PACKAGES
android.archs = arm64-v8a, armeabi-v7a
android.minapi = 21
android.targetapi = 33
android.release_artifact = apk

# 允许备份（记忆文件）
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

# Release 签名
android.keystore = %(source.dir)s/jmv_release.keystore
android.keystore_passwd = jmvagent2024
android.keyalias = jmvagent
android.keyalias_passwd = jmvagent2024
