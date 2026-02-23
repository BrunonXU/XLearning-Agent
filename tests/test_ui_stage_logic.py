import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.ui.state import calculate_stage_logic

def test_stage_logic_transitions():
    """Test the simplified 3-tab stage logic: Plan, Study, Quiz."""
    print("🚀 Starting UI Stage Logic Verification (3-tab)...")

    # Case 1: Brand new session
    session_new = {
        "has_input": False, "plan": None, "kb_count": 0,
        "study_progress": 0, "quiz_attempts": 0,
        "current_stage": "Plan",
        "report": {"generated": False, "content": "", "ts": None},
    }
    logic = calculate_stage_logic(session_new)
    stages = logic["stages"]
    assert "Plan" in stages
    assert "Study" in stages
    assert "Quiz" in stages
    assert stages["Plan"]["ready"] == True
    assert stages["Plan"]["done"] == False
    print("✅ Case 1: New session — all 3 tabs present, Plan not done.")

    # Case 2: Input provided
    session_input = {**session_new, "has_input": True}
    logic2 = calculate_stage_logic(session_input)
    assert logic2["stages"]["Plan"]["done"] == True
    print("✅ Case 2: Input provided — Plan marked done.")

    # Case 3: Plan generated
    session_planned = {**session_input, "plan": {"status": "mock"}}
    logic3 = calculate_stage_logic(session_planned)
    assert logic3["stages"]["Plan"]["done"] == True
    assert logic3["stages"]["Study"]["ready"] == True
    print("✅ Case 3: Plan generated — Study ready.")

    # Case 4: Study progress
    session_studied = {**session_planned, "study_progress": 1}
    logic4 = calculate_stage_logic(session_studied)
    assert logic4["stages"]["Study"]["done"] == True
    assert logic4["stages"]["Quiz"]["ready"] == True
    print("✅ Case 4: Study progress — Quiz ready.")

    # Case 5: Quiz completed
    session_quizzed = {**session_studied, "quiz_attempts": 1}
    logic5 = calculate_stage_logic(session_quizzed)
    assert logic5["stages"]["Quiz"]["done"] == True
    print("✅ Case 5: Quiz done.")

    print("\n✨ All 3-tab Stage Logic Assertions PASSED!")

if __name__ == "__main__":
    test_stage_logic_transitions()
