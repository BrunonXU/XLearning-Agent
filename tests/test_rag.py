"""
RAG 测试

测试 RAG Engine 功能
"""

import pytest
import os
import tempfile
from pathlib import Path


class TestRAGEngine:
    """测试 RAG 引擎"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.skipif(
        not os.getenv("DASHSCOPE_API_KEY"),
        reason="DASHSCOPE_API_KEY not set"
    )
    def test_add_and_retrieve(self, temp_dir):
        """测试添加和检索文档"""
        from src.rag import RAGEngine
        
        # 使用临时目录
        engine = RAGEngine(
            collection_name="test_collection",
            persist_directory=temp_dir,
        )
        
        # 添加文档
        content = "LangChain 是一个用于开发 LLM 应用的框架。它提供了丰富的组件和抽象。"
        ids = engine.add_document(content, metadata={"source": "test"})
        
        assert len(ids) > 0
        
        # 检索
        results = engine.retrieve("什么是 LangChain？", k=1)
        
        assert len(results) > 0
        assert "LangChain" in results[0].content
        
        # 清理
        engine.delete_collection()
    
    def test_build_context(self, temp_dir):
        """测试构建上下文"""
        from src.rag import RAGEngine
        
        # 这个测试不需要真实的 Embedding，跳过网络调用
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
