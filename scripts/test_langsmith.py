"""按照 LangSmith 官方文档最简方式测试 trace"""
import os
from dotenv import load_dotenv
load_dotenv()

import langsmith as ls

print("=== 环境变量 ===")
print(f"LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_API_KEY: {os.environ.get('LANGCHAIN_API_KEY', 'NOT SET')[:20]}...")
print(f"LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")

# 方式1: @traceable 装饰器
@ls.traceable(name="test_tool", run_type="tool")
def my_tool(question: str) -> str:
    return f"这是对 '{question}' 的回答"

@ls.traceable(name="test_chain", run_type="chain")
def my_chain(question: str) -> str:
    context = my_tool(question)
    return f"最终结果: {context}"

# 方式2: trace 上下文管理器
def test_with_context_manager():
    with ls.trace("test_context_manager", "chain", inputs={"q": "hello"}) as rt:
        result = "context manager 测试成功"
        rt.end(outputs={"result": result})
    return result

print("\n=== 执行测试 ===")
r1 = my_chain("langsmith连接测试")
print(f"@traceable 结果: {r1}")

r2 = test_with_context_manager()
print(f"context manager 结果: {r2}")

# 关键：flush 确保 trace 发送完毕
print("\n=== Flush traces ===")
client = ls.Client()
client.flush()
print("Flush 完成，去 LangSmith 查看 XLearning 项目")
