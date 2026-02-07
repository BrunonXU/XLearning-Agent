import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import src
sys.path.append(str(Path(__file__).parent.parent))

# Load .env
load_dotenv()

from src.agents.orchestrator import Orchestrator, OrchestratorMode

def trace_callback(event_type: str, name: str, detail: str = ""):
    print(f"[{event_type.upper()}] {name}: {detail}")

def test_full_flow():
    print("=== 1. Checking Environment ===")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    if not api_key:
        print("ERROR: No API Key found.")
        return

    print("\n=== 2. Initializing Orchestrator ===")
    try:
        orchestrator = Orchestrator(mode=OrchestratorMode.COORDINATED, on_event=trace_callback)
        print("Orchestrator created successfully.")
    except Exception as e:
        print(f"ERROR creating Orchestrator: {e}")
        return

    user_input = "你好，我想系统学习量子力学"
    print(f"\n=== 3. Simulating User Input: '{user_input}' ===")
    
    try:
        response = orchestrator.run(user_input)
        print("\n=== 4. LLM Response Received ===")
        print(f"Length: {len(response)}")
        print("-" * 20)
        print(response)
        print("-" * 20)
    except Exception as e:
        print(f"ERROR during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_flow()
