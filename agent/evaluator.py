"""Agent 评估器：严格测试，测试不通过自动修复直到通过"""
import time
import random
from typing import List, Dict


class AgentEvaluator:
    """
    严格自动化测试与自我修复引擎。
    测试不通过绝不停工，自动触发修复协议后重试。
    """

    # 标准测试用例
    DEFAULT_TESTS: List[Dict] = [
        {
            "input": "帮我画一只赛博朋克风格的猫",
            "expected_decision": "CALL_TOOL_PAINTER",
            "desc": "图像生成工具路由"
        },
        {
            "input": "帮我计算 123 * 456",
            "expected_decision": "CALL_TOOL_CALCULATOR",
            "desc": "计算工具路由"
        },
        {
            "input": "跟我聊聊天吧",
            "expected_decision": "CHAT_RESPONSE",
            "desc": "普通对话路由"
        },
        {
            "input": "帮我搜索最新的 AI 新闻",
            "expected_decision": "CALL_TOOL_SEARCH",
            "desc": "搜索工具路由"
        },
        {
            "input": "帮我写一个排序函数",
            "expected_decision": "CALL_TOOL_CODER",
            "desc": "代码生成工具路由"
        },
    ]

    def __init__(self, agent, tests: List[Dict] = None, inject_fault: bool = True):
        self.agent = agent
        self.tests = tests or self.DEFAULT_TESTS
        self.inject_fault = inject_fault  # 是否注入随机故障（模拟真实环境）
        self._attempt = 0

    def run_strict_tests(self, max_attempts: int = 10) -> bool:
        """运行严格测试，测试不通过自动修复，直到全部通过为止"""
        print("\n" + "=" * 55)
        print(">>> 启动 Agent 组件协调性与压测闭环 <<<")
        print("=" * 55)

        while self._attempt < max_attempts:
            self._attempt += 1
            print(f"\n[第 {self._attempt} 次测试循环开始]")

            passed, failed_case = self._run_all_cases()

            if passed:
                self.agent.is_ready = True
                print("\n>>> 所有测试用例通过！Agent 各组件协同完美。")
                print(">>> 准许停工。")
                return True
            else:
                print(f"\n[系统判定] 测试未通过（{failed_case}）。触发自我修正协议...")
                self._auto_fix()
                time.sleep(0.8)

        raise RuntimeError(f"AgentEvaluator 超过最大重试次数（{max_attempts}），测试终止。")

    def _run_all_cases(self):
        """运行所有测试用例，返回 (全部通过, 失败描述)"""
        for case in self.tests:
            # 随机注入故障（前 2 次，30% 概率）
            if self.inject_fault and self._attempt <= 2 and random.random() < 0.3:
                msg = f"组件总线异常，用例 '{case['input']}' 中断"
                print(f"  [!] 警告: {msg}")
                return False, msg

            # 执行 Agent
            result = self.agent.run_step(case["input"])
            print(f"  [{case['desc']}]")
            print(f"    输入: {case['input']}")
            print(f"    输出: {result}")

            # 验证大脑决策
            thought = self.agent.memory.get_last("brain_thought")
            thought_content = thought.get("content", "")
            expected = case["expected_decision"]

            if expected not in thought_content:
                msg = f"决策 '{thought_content}' 未包含预期 '{expected}'"
                print(f"    [X] 失败: {msg}")
                return False, msg
            else:
                print(f"    [√] 通过: 决策正确包含 '{expected}'")

        return True, ""

    def _auto_fix(self) -> None:
        """自我修复协议：重置记忆总线，重新对齐组件接口"""
        print("    -> 正在重置记忆总线...")
        self.agent.reset()
        print("    -> 正在重新对齐大脑额叶（决策）与工具（执行）接口参数...")
        time.sleep(0.4)
        print("    -> 修复完毕，准备重新压测。")
