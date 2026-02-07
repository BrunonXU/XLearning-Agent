
import sys
import os
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.agents.orchestrator import Orchestrator, OrchestratorMode

def test_generate_plan():
    print("🚀 Simulating 'Generate Study Plan' request...")
    orchestrator = Orchestrator(mode=OrchestratorMode.COORDINATED)
    
    # Simulate user input
    user_input = "生成一个学习计划"
    
    try:
        # This triggers _handle_create_plan -> PlannerAgent.run
        response = orchestrator.run(user_input)
        print("✅ Response:", response)
    except Exception as e:
        print("❌ Error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_plan()
