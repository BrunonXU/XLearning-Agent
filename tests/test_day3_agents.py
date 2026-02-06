"""
Day 3 综合验证脚本

测试所有 Day 3 完成的功能：
1. PlannerAgent - 生成学习计划
2. ValidatorAgent - 生成测验
3. Orchestrator - 调度逻辑

运行方式：
    python tests/test_day3_agents.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def main():
    print("=" * 60)
    print("🧪 Day 3 Agent 综合验证")
    print("=" * 60)
    
    results = []
    
    # 1. PlannerAgent 测试
    print("\n[1/4] PlannerAgent 测试...")
    try:
        from src.agents import PlannerAgent
        
        planner = PlannerAgent()
        
        # 测试领域描述输入
        plan = planner.run("LangChain 框架学习", goal="能熟练使用 LangChain 开发应用")
        
        assert plan.domain
        assert len(plan.phases) > 0
        assert plan.raw_markdown  # 验证 raw_markdown 被填充
        
        print(f"   ✅ PlannerAgent 成功")
        print(f"      领域: {plan.domain}")
        print(f"      阶段数: {len(plan.phases)}")
        results.append(("PlannerAgent", True))
    except Exception as e:
        print(f"   ❌ PlannerAgent 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PlannerAgent", False))
    
    # 2. ValidatorAgent 测试
    print("\n[2/4] ValidatorAgent 测试...")
    try:
        from src.agents import ValidatorAgent
        
        validator = ValidatorAgent()
        
        # 测试生成测验
        quiz = validator.generate_quiz(
            topic="Python 基础",
            content="Python 是一种高级编程语言，支持面向对象编程。列表(list)是可变序列。",
            num_questions=3,
            difficulty=0.3,
        )
        
        assert quiz.topic == "Python 基础"
        assert len(quiz.questions) > 0
        
        print(f"   ✅ ValidatorAgent.generate_quiz 成功")
        print(f"      主题: {quiz.topic}")
        print(f"      题目数: {len(quiz.questions)}")
        
        # 测试评估答案
        answers = ["A", "B", "A"]
        result = validator.evaluate_answers(quiz, answers[:len(quiz.questions)])
        
        print(f"   ✅ ValidatorAgent.evaluate_answers 成功")
        print(f"      准确率: {result.accuracy:.1%}")
        
        results.append(("ValidatorAgent", True))
    except Exception as e:
        print(f"   ❌ ValidatorAgent 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ValidatorAgent", False))
    
    # 3. Orchestrator 测试
    print("\n[3/4] Orchestrator 测试...")
    try:
        from src.agents import Orchestrator, OrchestratorMode
        
        orch = Orchestrator(mode=OrchestratorMode.STANDALONE)
        orch.set_domain("Python学习")
        
        # 测试意图识别
        assert orch._detect_intent("我想制定一个学习计划") == "create_plan"
        assert orch._detect_intent("开始测验") == "start_quiz"
        assert orch._detect_intent("什么是列表？") == "ask_question"
        
        print(f"   ✅ Orchestrator 意图识别正确")
        
        # 测试问答 (简单测试)
        response = orch._handle_ask_question("什么是 Python?")
        assert len(response) > 10
        
        print(f"   ✅ Orchestrator.run 成功")
        print(f"      回答片段: {response[:50]}...")
        
        results.append(("Orchestrator", True))
    except Exception as e:
        print(f"   ❌ Orchestrator 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Orchestrator", False))
    
    # 4. 端到端流程测试
    print("\n[4/4] 端到端流程测试...")
    try:
        from src.agents import Orchestrator, OrchestratorMode
        
        orch = Orchestrator(mode=OrchestratorMode.STANDALONE)
        
        # 模拟完整流程：创建计划 → 问答 → 测验
        plan_response = orch.run("我想学习 Transformer 架构")
        assert "计划" in plan_response or "阶段" in plan_response or "Transformer" in plan_response
        
        print(f"   ✅ 端到端流程成功")
        
        results.append(("端到端流程", True))
    except Exception as e:
        print(f"   ❌ 端到端流程失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("端到端流程", False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 Day 3 所有功能验证通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
