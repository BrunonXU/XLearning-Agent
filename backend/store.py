"""
简单内存存储，供各路由共享会话数据。
生产环境可替换为 Redis 或数据库。
"""

from typing import Dict, Any

_store: Dict[str, Dict[str, Any]] = {}


def get_session_store(plan_id: str) -> Dict[str, Any]:
    if plan_id not in _store:
        _store[plan_id] = {"messages": [], "materials": []}
    return _store[plan_id]
