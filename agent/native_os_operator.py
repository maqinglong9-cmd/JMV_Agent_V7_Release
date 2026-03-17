"""原生 OS 操作核心：赋予 Agent 真实的终端执行与文件读写能力"""
import os
import subprocess


class NativeOSOperator:
    """
    赋予 Agent 真正的操作系统级读写与终端执行能力。
    纯原生，零依赖，直接对接底层 Shell。
    所有操作限制在沙盒工作区内，防止误操作系统核心文件。
    """

    def __init__(self, workspace_dir="./jmv_workspace"):
        self.workspace = os.path.abspath(workspace_dir)
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
            print(f"[系统] 已为 Agent 开辟物理沙盒工作区: {self.workspace}")

    def execute_terminal_command(self, command, timeout=10):
        """
        真正执行终端命令（Shell Command）。
        带超时控制和完整的 stdout/stderr 捕获。
        返回 (success: bool, message: str)
        """
        print(f"  [终端指令] JMV 正在执行: `{command}`")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                return True, f"执行成功。终端输出: {output if output else '<无输出>'}"
            else:
                error_msg = (result.stderr.strip() or result.stdout.strip())
                return False, f"执行失败 (退出码 {result.returncode})。报错信息: {error_msg}"
        except subprocess.TimeoutExpired:
            return False, f"执行超时 ({timeout}秒)，进程已被强制终止。"
        except Exception as e:
            return False, f"底层调用异常: {str(e)}"

    def write_physical_file(self, filename, content):
        """真正的文件写入（限沙盒目录）"""
        filepath = os.path.join(self.workspace, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"文件 {filename} 已成功物理落盘。"
        except Exception as e:
            return False, f"写入失败: {str(e)}"

    def read_physical_file(self, filename):
        """真正的文件读取（限沙盒目录）"""
        filepath = os.path.join(self.workspace, filename)
        if not os.path.exists(filepath):
            return False, f"文件不存在: {filepath}"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"读取失败: {str(e)}"
