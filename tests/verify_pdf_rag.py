"""
验证脚本：PDF RAG 全链路测试 (Aloha Version)
========================================
验证 docs/test_cases/aloha.pdf 的处理流程。
"""

import sys
import os
import shutil
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env vars
load_dotenv()

try:
    from src.agents.orchestrator import Orchestrator, OrchestratorMode
    import streamlit as st
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

# Mock Streamlit session for logic dependencies
if not hasattr(st, "session_state"):
    st.session_state = {}
if "current_session" not in st.session_state:
    st.session_state["current_session"] = {"messages": []}

def test_pdf_pipeline():
    print("🚀 Starting PDF RAG Pipeline Test (Aloha)...")
    
    # 1. Setup
    # Use the user-provided PDF
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(project_root, "docs", "test_cases", "aloha.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    # Use Coordinated mode to test full flow (though process_file is mode-agnostic mostly)
    orchestrator = Orchestrator(mode=OrchestratorMode.COORDINATED)
    
    try:
        # 2. Upload
        print(f"\n[Step 1] Processing PDF: {pdf_path}...")
        with open(pdf_path, "rb") as f:
            content = f.read()
            filename = os.path.basename(pdf_path)
            


            result = orchestrator.process_file(content, filename)
            
        print(f"   Result: {result}")
        if not result["success"] or result["chunks"] == 0:
            print("   ❌ Upload Failed!")
            return
        print(f"   ✅ PDF Processed. Chunks: {result['chunks']}")
        
        # 3. Query
        question = "What is ALOHA?"
        print(f"\n[Step 2] Asking Question: '{question}'...")
        
        answer = orchestrator.run(question)
        print(f"   🤖 Answer: {answer}")
        
        # 4. Verify
        if len(answer) > 20: 
            print("\n✅ TEST PASSED: Agent generated a substantial answer!")
        else:
            print("\n⚠️ TEST WARNING: Answer too short.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_pipeline()
