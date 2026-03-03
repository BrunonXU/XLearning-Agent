"""
SessionContext — 懒加载会话上下文

每个 plan_id 对应一个独立的 SessionContext，按需初始化 TutorAgent 等重型对象。
"""

import logging
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.tutor import TutorAgent
    from src.core.progress import ProgressTracker

logger = logging.getLogger(__name__)

_sessions: Dict[str, "SessionContext"] = {}


class SessionContext:
    """单个学习规划的会话上下文（懒加载）"""

    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self._tutor: Optional[TutorAgent] = None
        self._progress: Optional[ProgressTracker] = None

    @property
    def tutor(self) -> "TutorAgent":
        if self._tutor is None:
            logger.info(f"[SessionContext] Initializing TutorAgent for plan {self.plan_id}")
            from src.agents.tutor import TutorAgent
            self._tutor = TutorAgent()
        return self._tutor

    @property
    def progress(self) -> "ProgressTracker":
        if self._progress is None:
            logger.info(f"[SessionContext] Initializing ProgressTracker for plan {self.plan_id}")
            from src.core.progress import ProgressTracker
            self._progress = ProgressTracker(session_id=self.plan_id)
        return self._progress


def get_session(plan_id: str) -> SessionContext:
    """获取或创建 plan_id 对应的 SessionContext"""
    if plan_id not in _sessions:
        _sessions[plan_id] = SessionContext(plan_id)
    return _sessions[plan_id]


def clear_session(plan_id: str) -> None:
    """清除 plan_id 对应的 SessionContext（删除规划时调用）"""
    _sessions.pop(plan_id, None)
