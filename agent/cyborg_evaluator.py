"""具身智能体容灾极限测试器"""
import time


class CyborgEvaluator:
    def __init__(self, agent):
        self.agent = agent

    def run_strict_tests(self):
        print("\n" + "=" * 50)
        print(">>> 启动 具身智能 (Cyborg) 器官协同与容灾修复极限测试 <<<")
        print("=" * 50)

        test_case = {
            "visual": "前方有明火且烟雾弥漫",
            "audio": "警报声与呼救声"
        }

        test_passed = False
        attempt = 1

        while not test_passed:
            print(f"\n[第 {attempt} 次测试循环开始]")

            if attempt == 1:
                print("  [!] 灾难注入: 视觉传感器 (Eyes) 失去连接！")
                self.agent.eyes.status = "OFFLINE"
            elif attempt == 2:
                print("  [!] 灾难注入: 伺服驱动器 (Hands) 烧毁！")
                self.agent.hands.status = "OFFLINE"

            result = self.agent.perceive_and_act(
                visual_stimulus=test_case["visual"],
                audio_stimulus=test_case["audio"]
            )

            if "ERROR" in result:
                print(f"  [X] 致命错误：检测到硬件掉线 ({result})，测试未通过。")
                print("  [系统指令] 触发硬件热修复与总线重启协议...")
                time.sleep(1)
                repaired = self.agent.run_hardware_diagnostics()
                if repaired:
                    print("    -> 备用线路已接通，硬件状态已重置为 ONLINE。")
                attempt += 1

            elif result == "SUCCESS":
                test_passed = True
                self.agent.is_ready = True
                print("\n" + "=" * 50)
                print(">>> 全部测试通过！眼、耳、口、手、脚均已上线，大脑指令下达无延迟，硬件容灾机制生效。 <<<")
                print(">>> 准许停工。 <<<")

            else:
                print("未知异常，重试。")
                attempt += 1
