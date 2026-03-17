"""
语音输出工具（零外部依赖）
==========================
将文本转换为 WAV 音频并播放。
- Windows: 使用 winsound（标准库）
- macOS:   使用 afplay（系统命令）
- Linux:   使用 aplay（系统命令）

合成引擎使用 NativeMouthComponent（纯数学正弦波），
无网络、无云端 API 依赖。
"""
import os
import sys
import subprocess
import threading

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTPUT_WAV   = os.path.join(_PROJECT_ROOT, 'jmv_output_speech.wav')

# 最大朗读字符数（避免生成过大的 WAV 文件）
_MAX_SPEAK_CHARS = 80


def speak_async(text: str, on_done=None) -> None:
    """
    在后台线程合成并播放语音，不阻塞主线程。
    on_done: 可选回调，播放完毕后在主线程调用。
    """
    threading.Thread(
        target=_speak_worker,
        args=(text, on_done),
        daemon=True
    ).start()


def _speak_worker(text: str, on_done=None) -> None:
    """合成 WAV → 播放 → 回调"""
    # 截断过长文本
    truncated = text[:_MAX_SPEAK_CHARS]

    # 合成 WAV
    try:
        from agent.native_mouth_component import NativeMouthComponent
        mouth = NativeMouthComponent()
        _, status = mouth.speak_to_file(truncated, _OUTPUT_WAV)
        if "ERROR" in status:
            print(f"  [语音] 合成失败: {status}")
            return
    except Exception as e:
        print(f"  [语音] 合成异常: {e}")
        return

    # 播放 WAV
    _play_wav(_OUTPUT_WAV)

    # 回调（调度到 Kivy 主线程）
    if on_done:
        try:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: on_done(), 0)
        except Exception:
            on_done()


def _play_wav(wav_path: str) -> None:
    """跨平台 WAV 播放"""
    if not os.path.isfile(wav_path):
        return
    try:
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        elif sys.platform == "darwin":
            subprocess.run(["afplay", wav_path], check=False, timeout=30)
        else:
            # Linux: 尝试 aplay，失败则静默
            subprocess.run(["aplay", wav_path], check=False, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"  [语音] 播放失败: {e}")


def is_supported() -> bool:
    """当前平台是否支持语音播放"""
    if sys.platform == "win32":
        return True
    if sys.platform == "darwin":
        return True
    # Linux：检查 aplay 是否存在
    return subprocess.run(
        ["which", "aplay"], capture_output=True
    ).returncode == 0
