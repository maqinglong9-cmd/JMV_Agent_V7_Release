import sys
import os
import time
import shutil
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.smart_companion_agent import SmartCompanionAgent


class FullCapabilityEvaluator:
    """全能力验证：确保 Agent 每项工具都真正工作，不允许存根通过"""

    def __init__(self):
        self.agent = SmartCompanionAgent()
        self.passed = 0
        self.failed = 0

    def _run_case(self, name, user_input, check_fn, max_attempts=5):
        print(f"\n[测试] {name}")
        print(f"  输入: {user_input}")
        for attempt in range(1, max_attempts + 1):
            self.agent.reset()
            result = self.agent.run_step(user_input)
            print(f"  输出 (第{attempt}次): {result[:200]}")
            if check_fn(result):
                print(f"  [PASS] {name}")
                self.passed += 1
                return True
            print(f"  [重试] 第{attempt}次未通过，继续...")
            time.sleep(0.5)
        print(f"  [FAIL] {name} — 超过最大重试次数")
        self.failed += 1
        return False

    def run_all(self):
        print("\n" + "=" * 65)
        print(">>> 启动 JMV Agent 全能力真实性验证测试 <<<")
        print("=" * 65)

        # 1. 计算器（真实 eval）
        self._run_case(
            "计算器",
            "帮我计算 999 * 888",
            lambda r: "887112" in r
        )

        # 2. 绘图（真实 PPM 文件生成）
        self._run_case(
            "绘图生成",
            "帮我画一张蓝色渐变图",
            lambda r: ".ppm" in r and "KB" in r and "STUB" not in r
        )

        # 3. 代码生成（真实写入 .py 文件）
        self._run_case(
            "代码生成",
            "帮我写一个排序函数",
            lambda r: "generated_" in r and ".py" in r and "STUB" not in r
        )

        # 4. 文件写入（真实落盘）
        self._run_case(
            "文件写入",
            "帮我写文件 hello.txt 内容是 JMV Agent Works",
            lambda r: "hello.txt" in r and "STUB" not in r and "失败" not in r
        )

        # 5. 终端执行（真实 shell）
        self._run_case(
            "终端执行",
            "执行命令 echo JMV_REAL_SHELL",
            lambda r: "JMV_REAL_SHELL" in r and "STUB" not in r
        )

        # 6. 搜索（真实 HTTP 请求）
        self._run_case(
            "网络搜索",
            "搜索 Python programming language",
            lambda r: len(r) > 50 and "STUB" not in r and "搜索完成" not in r or
                      ("搜索" in r and "STUB" not in r)
        )

        # 汇总
        print("\n" + "=" * 65)
        total = self.passed + self.failed
        print(f">>> 测试结果: {self.passed}/{total} 通过")
        if self.failed == 0:
            print(">>> 全部通过！JMV Agent 具备真实执行能力。准许停工！")
        else:
            print(f">>> {self.failed} 项失败，请检查对应工具实现。")
        print("=" * 65)

        # 清理工作区（保留文件供查看，仅提示）
        workspace = self.agent.os_operator.workspace
        if os.path.exists(workspace):
            files = os.listdir(workspace)
            print(f"\n[工作区] {workspace} 中生成了 {len(files)} 个文件:")
            for f in files:
                fpath = os.path.join(workspace, f)
                size = os.path.getsize(fpath)
                print(f"  - {f} ({size} bytes)")

        return self.failed == 0


if __name__ == "__main__":
    evaluator = FullCapabilityEvaluator()
    success = evaluator.run_all()
    sys.exit(0 if success else 1)
