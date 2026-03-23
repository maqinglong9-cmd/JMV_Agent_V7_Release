import sys
import os
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.cyborg_companion_agent import CyborgCompanionAgent
from agent.cyborg_evaluator import CyborgEvaluator

if __name__ == "__main__":
    jmv_cyborg = CyborgCompanionAgent()
    tester = CyborgEvaluator(jmv_cyborg)
    tester.run_strict_tests()
