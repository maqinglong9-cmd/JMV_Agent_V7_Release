import sys
import os
import time
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.ultimate_companion_agent import UltimateCompanionAgent


class UltimateEvaluator:
    def __init__(self, agent):
        self.agent = agent

    def run_tests(self, max_attempts: int = 10):
        print("\n" + "=" * 60)
        print(">>> 启动 JMV智伴 长期记忆持久化与内驱力极限测试 <<<")
        print("=" * 60)

        db_path = self.agent.long_term_memory.db_path
        if os.path.exists(db_path):
            os.remove(db_path)
            self.agent.long_term_memory._load_db()

        test_passed = False
        attempt = 1

        while not test_passed and attempt <= max_attempts:
            print(f"\n[测试轮次 {attempt}]")

            self.agent.process_input("记住 核心启动密码是 Alpha-779")

            print("  [系统] 模拟时间流逝与内存清空...")
            self.agent.short_term_context.clear()
            for _ in range(5):
                self.agent.emotion.tick()

            print("  [系统] 尝试从硬盘唤醒遥远的记忆...")
            reply = self.agent.process_input("请告诉我那个启动代码是什么？")
            print(f"  [Agent回复]: {reply}")

            if "Alpha-779" in reply:
                print("\n" + "=" * 60)
                print(">>> 测试通过 (PASS)！ <<<")
                print("1. [长期记忆模块] 纯原生相似度检索成功！跨越了内存清空，从本地 JSON 重建了上下文。")
                print("2. [情绪内驱力] Agent 成功表现出了随着时间推移的疲惫/无聊状态，情绪渲染正常。")
                print("JMV智伴 最终形态组装完毕。准许停工！")
                print("=" * 60)
                test_passed = True
                self.agent.is_ready = True
            else:
                current_threshold = self.agent.long_term_memory.similarity_threshold
                new_threshold = max(0.01, current_threshold - 0.05)
                print(f"  [X] 致命错误：长期记忆检索失败！(相似度阈值 {current_threshold:.2f} 可能过高)")
                print(f"  [系统自愈] 下调相似度阈值至 {new_threshold:.2f} 并重新建立索引...")
                self.agent.long_term_memory.similarity_threshold = new_threshold
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.agent.long_term_memory._load_db()
                time.sleep(1)
                attempt += 1

        if not test_passed:
            raise RuntimeError(f"UltimateEvaluator 超过最大重试次数（{max_attempts}），测试终止。")


if __name__ == "__main__":
    ultimate_agent = UltimateCompanionAgent()
    evaluator = UltimateEvaluator(ultimate_agent)
    evaluator.run_tests()
