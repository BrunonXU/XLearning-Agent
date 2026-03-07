"""
Provider 配置端点

GET  /api/provider/config  — 获取当前 provider 配置和可用列表
POST /api/provider/config  — 更新 provider 配置（热切换，不需要重启）
"""

import logging
import os

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend import database
from src.providers.openai_compatible import PROVIDER_PRESETS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/provider", tags=["provider"])


# 所有可用 Provider 及其模型列表
AVAILABLE_PROVIDERS = {
    "tongyi": {
        "label": "通义千问 (Tongyi)",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
        "default_model": "qwen-turbo",
        "env_key": "DASHSCOPE_API_KEY",
    },
    **{
        name: {
            "label": {
                "openai": "OpenAI",
                "deepseek": "DeepSeek",
                "zhipu": "智谱 (Zhipu)",
            }.get(name, name),
            "models": preset["models"],
            "default_model": preset["default_model"],
            "env_key": preset["env_key"],
        }
        for name, preset in PROVIDER_PRESETS.items()
    },
}


class ProviderConfigRequest(BaseModel):
    provider: str
    model: str
    apiKey: Optional[str] = None  # 可选，不传则用 .env 里的


@router.get("/config")
def get_provider_config():
    """返回当前 provider 配置和可用 provider 列表"""
    # 从 SQLite settings 表读取当前配置
    current = database.get_setting("llm_provider") or os.getenv("DEFAULT_PROVIDER", "tongyi")
    current_model = database.get_setting("llm_model") or os.getenv("DEFAULT_MODEL", "qwen-turbo")

    # 检查每个 provider 是否有 API key（.env 或 settings 表）
    providers_with_status = {}
    for name, info in AVAILABLE_PROVIDERS.items():
        env_key = info["env_key"]
        has_key = bool(
            database.get_setting(f"{name}_api_key")
            or os.getenv(env_key)
        )
        providers_with_status[name] = {
            **info,
            "hasApiKey": has_key,
        }

    return {
        "current": current,
        "currentModel": current_model,
        "providers": providers_with_status,
    }


@router.post("/config")
def update_provider_config(body: ProviderConfigRequest):
    """更新 provider 配置并热切换"""
    provider = body.provider.lower()

    if provider not in AVAILABLE_PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "available": list(AVAILABLE_PROVIDERS.keys())}

    # 验证模型是否在该 provider 的列表中
    valid_models = AVAILABLE_PROVIDERS[provider]["models"]
    if body.model not in valid_models:
        return {"error": f"Invalid model: {body.model}", "validModels": valid_models}

    # 保存 API key（如果提供了）
    if body.apiKey:
        database.upsert_setting(f"{provider}_api_key", body.apiKey)
        # 同时设置到环境变量，让当前进程立即生效
        env_key = AVAILABLE_PROVIDERS[provider]["env_key"]
        os.environ[env_key] = body.apiKey

    # 保存 provider 和 model 选择
    database.upsert_setting("llm_provider", provider)
    database.upsert_setting("llm_model", body.model)

    # 热切换：清除所有 session，下次请求时会用新 provider 创建
    from backend.session_context import _sessions
    _sessions.clear()
    logger.info(f"[provider] 切换到 {provider}/{body.model}，已清除所有 session")

    return {"ok": True, "provider": provider, "model": body.model}
