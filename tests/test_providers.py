"""
Provider 测试

测试 LLM 和 Embedding Provider
"""

import pytest
import os
from unittest.mock import Mock, patch


class TestProviderFactory:
    """测试 Provider 工厂"""
    
    def test_list_llm_providers(self):
        """测试列出可用的 LLM Provider"""
        from src.providers import ProviderFactory
        
        providers = ProviderFactory.list_llm_providers()
        assert "tongyi" in providers
        assert "qwen" in providers
    
    def test_list_embedding_providers(self):
        """测试列出可用的 Embedding Provider"""
        from src.providers import ProviderFactory
        
        providers = ProviderFactory.list_embedding_providers()
        assert "tongyi" in providers
        assert "dashscope" in providers


class TestTongyiProvider:
    """测试 Tongyi Provider"""
    
    @pytest.mark.skipif(
        not os.getenv("DASHSCOPE_API_KEY"),
        reason="DASHSCOPE_API_KEY not set"
    )
    def test_simple_chat(self):
        """测试简单对话"""
        from src.providers import TongyiProvider
        
        provider = TongyiProvider()
        response = provider.simple_chat("你好，请用一句话介绍自己")
        
        assert response is not None
        assert len(response) > 0
    
    def test_missing_api_key(self):
        """测试缺少 API Key 的情况"""
        from src.providers import TongyiProvider
        
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": ""}):
            with pytest.raises(ValueError):
                TongyiProvider(api_key=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
