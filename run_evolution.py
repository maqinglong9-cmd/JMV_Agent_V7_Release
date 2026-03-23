"""
EvolutionaryAgent 独立运行入口。
测试不通过自动触发大脑进化，直到全部通过为止。
"""
import sys
import os
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.evolutionary_agent import EvolutionaryAgent
from agent.evolution_evaluator import EvolutionEvaluator

if __name__ == "__main__":
    agent = EvolutionaryAgent()
    evaluator = EvolutionEvaluator(agent)
    evaluator.run_strict_tests()
