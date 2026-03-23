import sys
import os
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.central_nervous_system import CentralNervousSystem
from agent.omniscient_inspector import OmniscientInspector

if __name__ == "__main__":
    nervous_system = CentralNervousSystem()
    inspector = OmniscientInspector(nervous_system)
    inspector.run_deep_inspection()
