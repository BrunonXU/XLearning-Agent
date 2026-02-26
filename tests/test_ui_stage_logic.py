import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.ui.state import calculate_stage_logic

def test_stage_logic_transitions():
    """Test the simplified 2-tab stage logic: Plan, Study."""
    print("🚀 Starting UI Stage Logic Verification (2-tab)...")

    # Case 1: Brand new session
    session_new = {
        "has_input": False, "plan": None, "kb_count": 0,
        "study_progress": 0,
        "current_stage": "Plan",
    }
    logic = calculate_stage_logic(session_new)
    stages = logic["stages"]
    assert "Plan" in stages
    assert "Study" in stages
    assert "Quiz" not in stages
    assert stages["Plan"]["ready"] == True
    assert stages["Plan"]["done"] == False
    print("✅ Case 1: New session — 2 tabs present (Plan, Study), no Quiz.")

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
    print("✅ Case 4: Study progress — Study marked done.")

    print("\n✨ All 2-tab Stage Logic Assertions PASSED!")

if __name__ == "__main__":
    test_stage_logic_transitions()
