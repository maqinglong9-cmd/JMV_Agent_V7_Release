#!/usr/bin/env python3
"""修补 buildozer: root检查 + pip --user 问题"""

# 修补 1: root 检查
path1 = '/opt/buildozer-env/lib/python3.12/site-packages/buildozer/__init__.py'
with open(path1, 'r') as f:
    c = f.read()
p = c.replace(
    "warn_on_root = self.config.getdefault('buildozer', 'warn_on_root', '1')",
    "warn_on_root = '0'  # patched: skip root prompt"
)
with open(path1, 'w') as f:
    f.write(p)
print('PATCH1:', 'OK' if 'patched: skip root prompt' in p else 'SKIP')

# 修补 2: pip --user 问题
path2 = '/opt/buildozer-env/lib/python3.12/site-packages/buildozer/targets/android.py'
with open(path2, 'r') as f:
    c = f.read()
p = c.replace('options = ["--user"]', 'options = []  # patched: no --user in root env')
with open(path2, 'w') as f:
    f.write(p)
print('PATCH2:', 'OK' if 'patched: no --user in root env' in p else 'SKIP')
