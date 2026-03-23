#!/usr/bin/env python3
"""运行 buildozer android debug，输出到 /root/build4.log"""
import subprocess

env = {
    "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk-amd64",
    "PATH": "/usr/lib/jvm/java-17-openjdk-amd64/bin:/opt/buildozer-env/bin:/usr/local/bin:/usr/bin:/bin",
    "HOME": "/root",
    "VIRTUAL_ENV": "/opt/buildozer-env",
    "ANDROID_SDK_ROOT": "/root/.buildozer/android/platform/android-sdk",
    "ANDROID_NDK_HOME": "/root/.buildozer/android/platform/android-ndk-r25b",
}

with open("/root/build4.log", "w") as logf:
    r = subprocess.run(
        ["/opt/buildozer-env/bin/buildozer", "android", "debug"],
        cwd="/mnt/d/Users/Administrator/Desktop/testapp/brain-agent-app",
        env=env,
        stdout=logf,
        stderr=subprocess.STDOUT,
    )

with open("/root/build4_exit.txt", "w") as f:
    f.write(str(r.returncode))

print("EXIT:", r.returncode)
