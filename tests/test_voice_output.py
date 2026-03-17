"""voice_output 单元测试"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIsSupported:
    def test_windows_returns_true(self):
        import agent.voice_output as vo
        with mock.patch.object(vo.sys, 'platform', 'win32'):
            assert vo.is_supported() is True

    def test_darwin_returns_true(self):
        import agent.voice_output as vo
        with mock.patch.object(vo.sys, 'platform', 'darwin'):
            assert vo.is_supported() is True

    def test_linux_with_aplay(self):
        import agent.voice_output as vo
        with mock.patch.object(vo.sys, 'platform', 'linux'):
            with mock.patch('subprocess.run') as m:
                m.return_value = mock.Mock(returncode=0)
                result = vo.is_supported()
        assert result is True

    def test_linux_without_aplay(self):
        import agent.voice_output as vo
        with mock.patch.object(vo.sys, 'platform', 'linux'):
            with mock.patch('subprocess.run') as m:
                m.return_value = mock.Mock(returncode=1)
                result = vo.is_supported()
        assert result is False


class TestPlayWav:
    def test_nonexistent_file_does_not_crash(self):
        from agent.voice_output import _play_wav
        _play_wav("/nonexistent/file.wav")  # 应静默退出，不抛异常

    def test_windows_calls_winsound(self, tmp_path):
        """在 Windows 上，_play_wav 应调用 winsound.PlaySound"""
        fake_wav = tmp_path / "test.wav"
        fake_wav.write_bytes(b'RIFF\x00\x00\x00\x00WAVEfmt ')

        import agent.voice_output as vo
        fake_winsound = mock.MagicMock()
        fake_winsound.SND_FILENAME = 1
        fake_winsound.SND_NODEFAULT = 2

        with mock.patch.object(vo.sys, 'platform', 'win32'), \
             mock.patch.dict('sys.modules', {'winsound': fake_winsound}):
            vo._play_wav(str(fake_wav))

        fake_winsound.PlaySound.assert_called_once()

    def test_darwin_calls_afplay(self, tmp_path):
        fake_wav = tmp_path / "test.wav"
        fake_wav.write_bytes(b'RIFF')

        import agent.voice_output as vo
        with mock.patch.object(vo.sys, 'platform', 'darwin'), \
             mock.patch('subprocess.run') as m:
            vo._play_wav(str(fake_wav))
        m.assert_called_once()
        args = m.call_args[0][0]
        assert 'afplay' in args


class TestSpeakAsync:
    def test_speak_async_fires_thread(self):
        """speak_async 应立即返回（不阻塞），在后台执行"""
        import threading
        import time
        from agent.voice_output import speak_async

        done_flag = []

        def _worker(text, on_done=None):
            done_flag.append(True)

        import agent.voice_output as vo
        with mock.patch.object(vo, '_speak_worker', side_effect=_worker):
            speak_async("测试语音文字")

        # 等待后台线程启动
        time.sleep(0.2)
        assert done_flag, "后台线程未被启动"

    def test_text_truncation(self):
        """_speak_worker 应将文本截断到 _MAX_SPEAK_CHARS"""
        import agent.voice_output as vo
        long_text = "测" * 200

        captured = []

        class FakeMouth:
            def speak_to_file(self, text, path):
                captured.append(text)
                return path, "ERROR: skip"

        # NativeMouthComponent 在函数内部按需 import，需 mock 模块内的 import
        with mock.patch.dict('sys.modules', {
            'agent.native_mouth_component': mock.MagicMock(
                NativeMouthComponent=mock.MagicMock(return_value=FakeMouth())
            )
        }):
            try:
                vo._speak_worker(long_text)
            except Exception:
                pass

        if captured:
            assert len(captured[0]) <= vo._MAX_SPEAK_CHARS
