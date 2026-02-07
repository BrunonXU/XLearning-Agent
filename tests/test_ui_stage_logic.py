import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ui.state import calculate_stage_logic

def test_stage_logic_transitions():
    print("🚀 Starting UI Stage Logic Verification...")
    
    # Case 1: Brand New Session
    session_new = {
        "has_input": False,
        "plan": None,
        "kb_count": 0,
        "study_progress": 0,
        "quiz_attempts": 0,
        "current_stage": "Input"
    }
    logic_1 = calculate_stage_logic(session_new)
    stages = logic_1["stages"]
    assert stages["Input"]["ready"] == True
    assert stages["Plan"]["ready"] == False
    assert stages["Quiz"]["ready"] == False
    print("✅ Case 1 Passed: New session correctly blocks forward stages.")

    # Case 2: Input provided (Doc uploaded)
    session_input = session_new.copy()
    session_input["has_input"] = True
    logic_2 = calculate_stage_logic(session_input)
    assert logic_2["stages"]["Plan"]["ready"] == True
    assert "生成专属学习计划" in logic_2["stages"]["Plan"]["banner"]
    print("✅ Case 2 Passed: Plan stage unlocks after input.")

    # Case 3: Plan generated
    session_planned = session_input.copy()
    session_planned["plan"] = {"status": "mock"}
    logic_3 = calculate_stage_logic(session_planned)
    assert logic_3["stages"]["Study"]["ready"] == True
    print("✅ Case 3 Passed: Study stage unlocks after plan.")

    # Case 4: Study completed (one chapter)
    session_studied = session_planned.copy()
    session_studied["study_progress"] = 1
    logic_4 = calculate_stage_logic(session_studied)
    assert logic_4["stages"]["Quiz"]["ready"] == True
    print("✅ Case 4 Passed: Quiz stage unlocks after study progress.")

    # Case 5: Report logic (No quiz yet)
    logic_5 = calculate_stage_logic(session_studied)
    assert logic_5["stages"]["Report"]["ready"] == True
    assert "建议做一次测验" in logic_5["stages"]["Report"]["banner"]
    print("✅ Case 5 Passed: Report available with suggestions if no quiz.")

    print("\n✨ All Stage Logic Assertions PASSED!")

if __name__ == "__main__":
    test_stage_logic_transitions()
