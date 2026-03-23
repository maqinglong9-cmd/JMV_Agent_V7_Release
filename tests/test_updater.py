"""unix_updater / win_updater 单元测试"""
import os
import sys
import stat
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUnixUpdater:
    """unix_updater.apply_update 的单元测试"""

    def test_download_failure_raises_runtime_error(self, tmp_path):
        """下载失败时应抛出 RuntimeError"""
        import importlib
        import updater.unix_updater as uu

        with mock.patch('updater.unix_updater.download_file',
                        side_effect=OSError('network down')):
            with mock.patch('updater.unix_updater.get_update_dir',
                            return_value=str(tmp_path)):
                try:
                    uu.apply_update('http://example.com/bin', 'abc123')
                    assert False, "应该抛出 RuntimeError"
                except RuntimeError as e:
                    assert '下载失败' in str(e)

    def test_sha256_mismatch_raises_and_deletes(self, tmp_path):
        """SHA256 不匹配时应删除文件并抛出 RuntimeError"""
        import updater.unix_updater as uu

        fake_bin = tmp_path / 'BrainAgent_new'
        fake_bin.write_bytes(b'fake content')

        with mock.patch('updater.unix_updater.download_file'):
            with mock.patch('updater.unix_updater.verify_sha256', return_value=False):
                with mock.patch('updater.unix_updater.get_update_dir',
                                return_value=str(tmp_path)):
                    try:
                        uu.apply_update('http://example.com/bin', 'wronghash')
                        assert False, "应该抛出 RuntimeError"
                    except RuntimeError as e:
                        assert 'SHA256' in str(e)
        # 文件应已被删除
        assert not fake_bin.exists()

    def test_success_generates_shell_script(self, tmp_path):
        """下载+校验成功时应生成 .sh 脚本并调用 subprocess.Popen"""
        import updater.unix_updater as uu

        fake_bin = tmp_path / 'BrainAgent_new'
        fake_bin.write_bytes(b'binary content')

        popen_calls = []

        def fake_popen(cmd, **kwargs):
            popen_calls.append(cmd)
            return mock.MagicMock()

        with mock.patch('updater.unix_updater.download_file'):
            with mock.patch('updater.unix_updater.verify_sha256', return_value=True):
                with mock.patch('updater.unix_updater.get_update_dir',
                                return_value=str(tmp_path)):
                    with mock.patch('subprocess.Popen', side_effect=fake_popen):
                        with mock.patch('sys.exit'):
                            uu.apply_update('http://example.com/bin', 'goodhash')

        # Popen 应被调用一次
        assert len(popen_calls) == 1
        # 调用的是 /bin/sh
        assert popen_calls[0][0] == '/bin/sh'
        # 脚本文件应存在
        sh_path = str(tmp_path / 'do_update.sh')
        assert os.path.exists(sh_path)

    def test_shell_script_content(self, tmp_path):
        """生成的 shell 脚本应包含 kill -0、mv -f 和 sys.executable"""
        import updater.unix_updater as uu

        fake_bin = tmp_path / 'BrainAgent_new'
        fake_bin.write_bytes(b'binary')

        with mock.patch('updater.unix_updater.download_file'):
            with mock.patch('updater.unix_updater.verify_sha256', return_value=True):
                with mock.patch('updater.unix_updater.get_update_dir',
                                return_value=str(tmp_path)):
                    with mock.patch('subprocess.Popen', return_value=mock.MagicMock()):
                        with mock.patch('sys.exit'):
                            uu.apply_update('http://example.com/bin', 'goodhash')

        sh_path = str(tmp_path / 'do_update.sh')
        # 显式指定 UTF-8，避免 Windows 默认 GBK 解码失败
        content = open(sh_path, encoding='utf-8').read()
        assert 'kill -0' in content
        assert 'mv -f' in content
        assert sys.executable in content

    def test_shell_script_is_executable(self, tmp_path):
        """生成的 shell 脚本应有可执行权限（仅 Unix 可验证）"""
        import pytest
        if sys.platform == 'win32':
            pytest.skip("Windows 不支持 Unix 执行权限位，仅在 Unix 上验证")

        import updater.unix_updater as uu

        fake_bin = tmp_path / 'BrainAgent_new'
        fake_bin.write_bytes(b'binary')

        with mock.patch('updater.unix_updater.download_file'):
            with mock.patch('updater.unix_updater.verify_sha256', return_value=True):
                with mock.patch('updater.unix_updater.get_update_dir',
                                return_value=str(tmp_path)):
                    with mock.patch('subprocess.Popen', return_value=mock.MagicMock()):
                        with mock.patch('sys.exit'):
                            uu.apply_update('http://example.com/bin', 'goodhash')

        sh_path = str(tmp_path / 'do_update.sh')
        mode = os.stat(sh_path).st_mode
        assert mode & stat.S_IXUSR, "脚本应有用户可执行权限"

    def test_new_binary_gets_executable_permission(self, tmp_path):
        """下载的新二进制应被赋予可执行权限"""
        import updater.unix_updater as uu

        fake_bin = tmp_path / 'BrainAgent_new'
        fake_bin.write_bytes(b'binary content')

        chmod_calls = []
        original_chmod = os.chmod

        def fake_chmod(path, mode):
            chmod_calls.append((path, mode))
            original_chmod(path, mode)

        with mock.patch('updater.unix_updater.download_file'):
            with mock.patch('updater.unix_updater.verify_sha256', return_value=True):
                with mock.patch('updater.unix_updater.get_update_dir',
                                return_value=str(tmp_path)):
                    with mock.patch('os.chmod', side_effect=fake_chmod):
                        with mock.patch('subprocess.Popen', return_value=mock.MagicMock()):
                            with mock.patch('sys.exit'):
                                uu.apply_update('http://example.com/bin', 'goodhash')

        # 应有对新二进制的 chmod 调用
        new_bin_path = str(tmp_path / 'BrainAgent_new')
        chmod_targets = [p for p, _ in chmod_calls]
        assert new_bin_path in chmod_targets


class TestUpdaterRouter:
    """updater.__init__.apply_update 平台路由测试"""

    def test_routes_to_unix_on_darwin(self):
        import updater
        with mock.patch('sys.platform', 'darwin'):
            with mock.patch('updater.unix_updater.apply_update') as m:
                updater.apply_update('http://x.com', 'abc')
                m.assert_called_once_with('http://x.com', 'abc', None)

    def test_routes_to_unix_on_linux_desktop(self):
        import updater
        with mock.patch('sys.platform', 'linux'):
            # 非 Android（没有 /data/data）
            with mock.patch('os.path.exists', return_value=False):
                with mock.patch('updater.unix_updater.apply_update') as m:
                    updater.apply_update('http://x.com', 'abc')
                    m.assert_called_once_with('http://x.com', 'abc', None)

    def test_routes_to_win_on_windows(self):
        import updater
        with mock.patch('sys.platform', 'win32'):
            with mock.patch('updater.win_updater.apply_update') as m:
                updater.apply_update('http://x.com', 'abc')
                m.assert_called_once_with('http://x.com', 'abc', None)

    def test_unknown_platform_raises(self):
        import updater
        import pytest
        with mock.patch('sys.platform', 'freebsd14'):
            with mock.patch('os.path.exists', return_value=False):
                try:
                    updater.apply_update('http://x.com', 'abc')
                    assert False, "应该抛出 NotImplementedError"
                except NotImplementedError as e:
                    assert 'freebsd14' in str(e)
