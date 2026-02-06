"""
Day 2 综合验证脚本

测试所有 Day 2 完成的功能：
1. Provider 调用
2. RAG 端到端
3. PDFAnalyzer → RAG 连接
4. TutorAgent RAG 集成

运行方式：
    python tests/test_day2_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def main():
    print("=" * 60)
    print("🧪 Day 2 综合验证")
    print("=" * 60)
    
    results = []
    
    # 1. Provider 测试
    print("\n[1/4] Provider 调用测试...")
    try:
        from src.providers import ProviderFactory
        llm = ProviderFactory.create_llm()
        response = llm.simple_chat("你好，回复'OK'即可")
        assert response and len(response) > 0
        print(f"   ✅ Provider 调用成功: {response[:30]}...")
        results.append(("Provider", True))
    except Exception as e:
        print(f"   ❌ Provider 调用失败: {e}")
        results.append(("Provider", False))
    
    # 2. RAG 测试
    print("\n[2/4] RAG Engine 测试...")
    try:
        from src.rag import RAGEngine
        rag = RAGEngine(collection_name="day2_test")
        rag.clear()
        
        # 添加测试文档
        rag.add_document(
            "LangChain 是一个用于构建 LLM 应用的框架，支持 Prompt 管理和 Chain 编排。",
            {"source": "langchain_intro.md"}
        )
        
        # 检索测试
        results_list = rag.retrieve("什么是 LangChain", k=1)
        assert len(results_list) > 0
        print(f"   ✅ RAG 检索成功: {results_list[0].content[:40]}...")
        
        # 问答测试
        answer = rag.query_with_context("LangChain 能做什么？")
        assert len(answer) > 10
        print(f"   ✅ RAG 问答成功: {answer[:50]}...")
        
        rag.clear()
        results.append(("RAG Engine", True))
    except Exception as e:
        print(f"   ❌ RAG 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("RAG Engine", False))
    
    # 3. PDFAnalyzer 测试（不需要实际 PDF 文件）
    print("\n[3/4] PDFAnalyzer 测试...")
    try:
        from src.specialists.pdf_analyzer import PDFAnalyzer, PDFContent
        
        analyzer = PDFAnalyzer()
        
        # 模拟 PDF 内容
        fake_content = PDFContent(
            title="Test Paper",
            content="This is a test paper about machine learning.",
            total_pages=5
        )
        
        # 测试 to_learning_context
        context = analyzer.to_learning_context(fake_content)
        assert "Test Paper" in context
        print(f"   ✅ to_learning_context 成功")
        
        # 测试 import_to_rag
        from src.rag import RAGEngine
        rag = RAGEngine(collection_name="pdf_test")
        rag.clear()
        
        ids = analyzer.import_to_rag(fake_content, rag)
        assert len(ids) > 0
        print(f"   ✅ import_to_rag 成功: {len(ids)} chunks")
        
        rag.clear()
        results.append(("PDFAnalyzer", True))
    except Exception as e:
        print(f"   ❌ PDFAnalyzer 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PDFAnalyzer", False))
    
    # 4. TutorAgent 测试
    print("\n[4/4] TutorAgent RAG 集成测试...")
    try:
        from src.agents import TutorAgent
        from src.rag import RAGEngine
        
        # 准备 RAG 知识库
        rag = RAGEngine(collection_name="tutor_test")
        rag.clear()
        rag.add_document(
            "Python 的 list 是一种有序可变的集合，支持索引和切片操作。",
            {"source": "python_basic.md"}
        )
        
        # 创建 TutorAgent 并测试
        tutor = TutorAgent()
        tutor.set_rag_engine(rag)
        
        answer = tutor.answer("什么是 Python 的 list？")
        assert len(answer) > 10
        print(f"   ✅ TutorAgent.answer() 成功:")
        print(f"      {answer[:80]}...")
        
        rag.clear()
        results.append(("TutorAgent", True))
    except Exception as e:
        print(f"   ❌ TutorAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TutorAgent", False))
    
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
        print("\n🎉 Day 2 所有功能验证通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
