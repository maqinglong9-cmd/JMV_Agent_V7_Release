"""纯原生 WAV 音频合成器，不依赖外部 TTS 库"""
import math
import struct
import wave


class NativeMouthComponent:
    def __init__(self):
        self.status = "ONLINE"
        self.sample_rate = 44100
        self.amplitude = 16000

    def speak_to_file(self, text, output_filename="jmv_output_speech.wav"):
        try:
            print(f"  [嘴部] 正在启动底层声码器，将文本「{text[:20]}...」编译为音频流...")

            with wave.open(output_filename, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)

                frames = []
                duration_per_char = 0.1

                for char in text:
                    freq = 300 + (ord(char) % 500)
                    num_samples = int(self.sample_rate * duration_per_char)
                    for i in range(num_samples):
                        t = float(i) / self.sample_rate
                        value = int(self.amplitude * math.sin(2.0 * math.pi * freq * t))
                        frames.append(struct.pack('<h', value))

                    silence_samples = int(self.sample_rate * 0.05)
                    for _ in range(silence_samples):
                        frames.append(struct.pack('<h', 0))

                wav_file.writeframes(b''.join(frames))

            return f"成功生成真实本地音频文件: {output_filename}", "SUCCESS"

        except Exception as e:
            return None, f"ERROR: AUDIO_GENERATION_FAILED_{str(e)}"
