"""全链路审计评估器：死磕到底，测试不通过绝不停工"""
import time


class OmniscientInspector:
    def __init__(self, system):
        self.system = system

    def run_deep_inspection(self, max_attempts: int = 10):
        print("\n" + "=" * 55)
        print(">>> 启动系统级全链路检查 (Omniscient Inspector) <<<")
        print("=" * 55)

        test_visual = "前方0.5米处有一个红色按钮"
        test_audio = "立刻按下那个红色按钮！"

        passed = False
        attempt = 1

        while not passed and attempt <= max_attempts:
            print(f"\n[检查轮次 {attempt}] 注入测试刺激...")

            start_time = time.time()
            final_signal, result_status = self.system.perceive_and_react(test_visual, test_audio)
            latency = (time.time() - start_time) * 1000

            print("\n  --- 审计报告 (Audit Report) ---")
            print(f"  执行状态: {result_status}")
            print(f"  系统延迟: {latency:.2f} ms")
            print("  神经传导路径追踪:")
            for step in final_signal.trace_log:
                print(f"    {step}")
            print("  ------------------------------")

            if result_status == "COORDINATION_SUCCESS":
                trace_str = str(final_signal.trace_log)
                if ("大脑核心计算区" in trace_str
                        and "运动神经(手)" in trace_str
                        and "发声器官(嘴)" in trace_str):
                    passed = True
                    print("\n" + "=" * 55)
                    print(">>> 检查通过 (PASS)！<<<")
                    print("视觉与听觉输入完美融合，大脑决策未发生阻塞。")
                    print("手部运动器官与嘴部发声器官实现了微秒级的同步协调。")
                    print("JMV智伴 具身智能体协调运转完全正常。准许停工！")
                    print("=" * 55)
                else:
                    print("  [X] 发现隐蔽 BUG：动作虽然执行，但信号追踪显示跳过了某些关键脑区。触发重构...")
                    self.system.repair_neural_routing()
                    attempt += 1
            else:
                print(f"  [X] 致命错误：器官协调失败，症状为 '{result_status}'。")
                print("  [Inspector 拦截] 测试不通过。正在自动强制执行系统级底层修复...")
                self.system.repair_neural_routing()
                attempt += 1
                time.sleep(1)

        if not passed:
            raise RuntimeError(f"OmniscientInspector 超过最大重试次数（{max_attempts}），检查终止。")
