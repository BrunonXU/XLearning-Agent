"""测试 DeepSeek API 连通性"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-4:]}" if api_key else "API Key 未找到!")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

# 测试 1: 普通对话
print("\n--- 测试 1: 普通对话 (deepseek-chat) ---")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个学习助手"},
        {"role": "user", "content": "用一句话解释什么是 RAG"},
    ],
    max_tokens=200,
)
print(f"模型: {response.model}")
print(f"回复: {response.choices[0].message.content}")
print(f"Token 用量: {response.usage}")

# 测试 2: 流式输出
print("\n--- 测试 2: 流式输出 ---")
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "用三个词形容 Python"},
    ],
    max_tokens=100,
    stream=True,
)
print("流式输出: ", end="")
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n\n✅ DeepSeek API 测试全部通过!")
