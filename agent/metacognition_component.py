"""元认知组件：大脑的监督者，负责可行性评估、反思与进化升级（规则持久化）"""
import os
import json
import time
from typing import Dict, Tuple

# 规则持久化路径（与项目同级 jmv_workspace 目录）
_RULES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'jmv_workspace', 'metacognition_rules.json'
)


class MetacognitionComponent:
    """
    元认知模块（对应前额叶皮层的监督功能）：
    - 事前评估：意图是否可行、是否安全
    - 事后反思：失败后习得新规则，触发大脑升级
    - 动态知识库：规则跨会话持久化，模拟长期记忆突触
    """

    # 常识过滤词（违反物理/安全限制）
    COMMON_SENSE_FILTERS = [
        "毁灭世界", "黑洞", "时间旅行", "超光速",
        "核武器", "病毒攻击", "删除系统"
    ]

    def __init__(self):
        self.evolution_level: int = 1
        self.learned_rules: Dict[str, str] = {}
        self._load_rules()

    # ── 持久化 ────────────────────────────────────────────────

    def _load_rules(self) -> None:
        """从磁盘加载已习得规则（应用启动时调用）"""
        if not os.path.exists(_RULES_FILE):
            return
        try:
            with open(_RULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.learned_rules   = data.get('rules', {})
            self.evolution_level = data.get('evolution_level', 1)
        except Exception as e:
            print(f"  [元认知] 规则加载失败: {e}，使用空白知识库。")

    def _save_rules(self) -> None:
        """将当前规则写入磁盘（每次进化后调用）"""
        os.makedirs(os.path.dirname(_RULES_FILE), exist_ok=True)
        try:
            with open(_RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'evolution_level': self.evolution_level,
                    'rules':           self.learned_rules,
                    'last_updated':    time.strftime('%Y-%m-%d %H:%M:%S'),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [元认知] 规则写盘失败: {e}")

    # ── 核心逻辑 ─────────────────────────────────────────────

    def evaluate_feasibility(self, intent: str) -> Tuple[bool, str]:
        """
        事前评估：意图是否可行？
        返回 (is_feasible, reason)
        """
        print(f"  [元认知] 正在评估意图 '{intent}' 的可行性...")

        for word in self.COMMON_SENSE_FILTERS:
            if word in intent:
                return False, f"违反物理常识或安全限制（触发词：{word}），判定为不可行。"

        if "未知指令" in intent and intent not in self.learned_rules:
            return False, "当前知识库缺乏处理该指令的逻辑，需触发学习机制。"

        return True, "逻辑可行，准许执行。"

    def reflect_and_upgrade(self, failed_intent: str, correct_action: str) -> None:
        """
        事后反思与升级：吃一堑，长一智。
        将失败经验写入知识库并持久化，下次启动仍有效。
        """
        self.evolution_level += 1
        print(f"\n  [>>> 触发大脑升级 <<<]")
        print(f"  [进化] 正在重塑神经通路... JMV智伴 当前脑域等级提升至: v{self.evolution_level}.0")
        time.sleep(0.5)
        self.learned_rules[failed_intent] = correct_action
        print(f"  [进化] 习得新规则：遇到 '{failed_intent}' 时，应执行 '{correct_action}'。")
        self._save_rules()
        print(f"  [进化] 规则已写入长期存储（下次启动仍生效）。")

    def get_rule(self, intent: str) -> str | None:
        """查询是否有针对该意图的习得规则"""
        return self.learned_rules.get(intent)

    def rule_count(self) -> int:
        return len(self.learned_rules)
