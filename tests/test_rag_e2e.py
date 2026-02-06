"""
RAG 端到端测试脚本

验证 Day 2 核心功能：导入文档 → 检索 → RAG 问答

运行方式：
    python tests/test_rag_e2e.py
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_rag_pipeline():
    """测试完整的 RAG Pipeline"""
    print("=" * 60)
    print("🧪 RAG 端到端测试")
    print("=" * 60)
    
    # 1. 初始化 RAG Engine
    print("\n[1/5] 初始化 RAG Engine...")
    try:
        from src.rag import RAGEngine
        rag = RAGEngine(collection_name="test_collection")
        print(f"   ✅ RAG Engine 初始化成功")
        print(f"   📁 持久化目录: {rag.persist_directory}")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False
    
    # 2. 清空并添加测试文档
    print("\n[2/5] 添加测试文档...")
    try:
        rag.clear()
        
        # 添加一些关于 Transformer 的知识
        docs = [
            {
                "content": """
Transformer 是一种基于自注意力机制的神经网络架构，由 Google 在 2017 年的论文
"Attention is All You Need" 中提出。

Transformer 的核心创新是 Self-Attention 机制，它允许模型在处理序列时，
同时关注序列中的所有位置，而不是像 RNN 那样顺序处理。

Self-Attention 的计算公式是：Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V

其中 Q、K、V 分别是 Query、Key、Value 矩阵，d_k 是 Key 的维度。
                """,
                "metadata": {"source": "transformer_intro.md", "type": "notes"}
            },
            {
                "content": """
Multi-Head Attention 是 Transformer 的另一个重要组件。
它将输入分成多个 "头"，每个头独立计算注意力，然后将结果拼接起来。

这样做的好处是可以让模型同时关注不同位置的不同表示子空间。
论文中使用了 8 个头，每个头的维度是 64。

Multi-Head Attention 的公式是：
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
其中 head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
                """,
                "metadata": {"source": "multihead_attention.md", "type": "notes"}
            },
            {
                "content": """
Position Encoding（位置编码）是 Transformer 用来表示序列位置信息的方法。
由于 Self-Attention 机制本身不包含位置信息，所以需要额外添加位置编码。

论文中使用了正弦和余弦函数来生成位置编码：
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

这种编码方式的好处是可以处理任意长度的序列。
                """,
                "metadata": {"source": "position_encoding.md", "type": "notes"}
            },
        ]
        
        for doc in docs:
            rag.add_document(doc["content"], doc["metadata"])
        
        doc_count = rag.count()
        print(f"   ✅ 添加了 {len(docs)} 个文档，共 {doc_count} 个 chunks")
    except Exception as e:
        print(f"   ❌ 添加文档失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试检索
    print("\n[3/5] 测试向量检索...")
    try:
        query = "什么是 Self-Attention?"
        results = rag.retrieve(query, k=2)
        
        print(f"   查询: \"{query}\"")
        print(f"   ✅ 检索到 {len(results)} 个结果")
        
        for i, r in enumerate(results, 1):
            print(f"   [{i}] 来源: {r.metadata.get('source', '未知')}, 分数: {r.score:.4f}")
            print(f"       内容片段: {r.content[:80]}...")
    except Exception as e:
        print(f"   ❌ 检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试 RAG 问答
    print("\n[4/5] 测试 RAG 问答...")
    try:
        query = "请解释一下 Multi-Head Attention 的作用是什么？"
        print(f"   问题: \"{query}\"")
        print("   正在调用 LLM（可能需要几秒）...")
        
        answer = rag.query_with_context(query, k=3)
        
        print(f"   ✅ 获得回答:")
        print("   " + "-" * 50)
        # 打印回答，限制长度
        for line in answer[:500].split('\n'):
            print(f"   {line}")
        if len(answer) > 500:
            print("   ...")
        print("   " + "-" * 50)
    except Exception as e:
        print(f"   ❌ RAG 问答失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 清理测试数据
    print("\n[5/5] 清理测试数据...")
    try:
        rag.clear()
        print(f"   ✅ 测试数据已清理")
    except Exception as e:
        print(f"   ⚠️ 清理失败（可忽略）: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 RAG 端到端测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_rag_pipeline()
    sys.exit(0 if success else 1)
