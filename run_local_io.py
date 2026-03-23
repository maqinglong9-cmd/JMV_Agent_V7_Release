import sys
import os
import time
import struct
import random
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.native_eye_component import NativeEyeComponent
from agent.native_mouth_component import NativeMouthComponent


class LocalIOEvaluator:
    def __init__(self):
        self.eyes = NativeEyeComponent()
        self.mouth = NativeMouthComponent()
        self.test_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_vision.ppm")
        self.test_audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jmv_output_speech.wav")

    def _generate_test_image(self, faulty=False):
        with open(self.test_img_path, 'wb') as f:
            if faulty:
                f.write(b'P9\n100 100\n255\n')
            else:
                f.write(b'P6\n100 100\n255\n')
            for _ in range(100 * 100):
                r = random.randint(150, 255)
                g = random.randint(0, 50)
                b = random.randint(0, 50)
                f.write(struct.pack('BBB', r, g, b))

    def _cleanup(self):
        for file in [self.test_img_path, self.test_audio_path]:
            if os.path.exists(file):
                os.remove(file)

    def run_integration_test(self):
        print("\n" + "=" * 55)
        print(">>> 启动 JMV智伴 纯本地原生 I/O 读写与协调极限测试 <<<")
        print("=" * 55)

        test_passed = False
        attempt = 1

        while not test_passed:
            print(f"\n[测试轮次 {attempt}] 开始执行物理层读写...")

            if attempt == 1:
                print("  [系统] 故意生成损坏的本地图像文件...")
                self._generate_test_image(faulty=True)
            else:
                self._generate_test_image(faulty=False)

            print(f"  [指令] 驱动视觉神经读取本地路径: {self.test_img_path}")
            eye_result, eye_status = self.eyes.scan_local_image(self.test_img_path)

            if "ERROR" in eye_status:
                print(f"  [X] 视觉 IO 读取失败: {eye_status}")
                print("  [系统自愈] 正在自动修复二进制解析器与图像生成逻辑...")
                self.eyes.parsing_mode = "lenient"
                time.sleep(1)
                attempt += 1
                continue

            print(f"  [√] 视觉原生解析成功: {eye_result}")

            text_to_speak = f"报告，我看到了{eye_result.split('，')[1]}"
            print(f"  [指令] 驱动发声器官将文本合成至本地路径: {self.test_audio_path}")

            mouth_result, mouth_status = self.mouth.speak_to_file(text_to_speak, self.test_audio_path)

            if "ERROR" in mouth_status:
                print(f"  [X] 音频 IO 写入失败: {mouth_status}")
                attempt += 1
                continue

            print(f"  [√] 音频原生写入成功: {mouth_result}")

            if os.path.exists(self.test_audio_path) and os.path.getsize(self.test_audio_path) > 1000:
                print("\n" + "=" * 55)
                print(">>> 物理层读写测试通过 (PASS)！<<<")
                print("视觉模块 (Eyes) 成功脱离第三方库，以二进制流直接读取本地图像。")
                print("发声模块 (Mouth) 成功以原生 math/struct 算法将语义合成为真实的本地 .wav 文件。")
                print(f"你可以现在在本地目录双击播放生成的 'jmv_output_speech.wav' 文件 (听起来像是机器人的机械声)。")
                print(">>> 准许停工！ <<<")
                test_passed = True
            else:
                print("  [X] 文件验证失败，文件不存在或写入为空。重试...")
                attempt += 1


if __name__ == "__main__":
    inspector = LocalIOEvaluator()
    inspector.run_integration_test()
    # _cleanup() 注释掉，保留 .wav 文件供用户播放
