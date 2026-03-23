"""
SmartCompanionAgent 独立运行入口。
执行严格测试，测试不通过自动修复直到通过为止。
"""
import sys
import os
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.smart_companion_agent import SmartCompanionAgent
from agent.evaluator import AgentEvaluator

if __name__ == "__main__":
    agent = SmartCompanionAgent()
    evaluator = AgentEvaluator(agent, inject_fault=True)
    evaluator.run_strict_tests()
