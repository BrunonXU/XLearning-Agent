"""
Agent 基类

定义所有 Agent 的通用接口和行为
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.providers import LLMProvider, ProviderFactory
from src.core import Config


class BaseAgent(ABC):
    """
    Agent 抽象基类
    
    所有功能 Agent 必须继承此类
    """
    
    # Agent 名称，子类必须定义
    name: str = "BaseAgent"
    
    # Agent 描述
    description: str = ""
    
    # 系统提示词
    system_prompt: str = ""
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        config: Optional[Config] = None,
    ):
        """
        初始化 Agent
        
        Args:
            llm_provider: LLM Provider，默认使用工厂创建
            config: 配置对象
        """
        self.config = config or Config.get()
        self.llm = llm_provider or ProviderFactory.create_llm()
    
    @abstractmethod
    def run(self, input_data: Any, **kwargs) -> Any:
        """
        运行 Agent
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Agent 输出
        """
        pass
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（默认使用类属性）
            
        Returns:
            LLM 响应
        """
        sp = system_prompt or self.system_prompt
        return self.llm.simple_chat(prompt, system_prompt=sp)
    
    def __repr__(self):
        return f"{self.name}(llm={self.llm.model_name})"
