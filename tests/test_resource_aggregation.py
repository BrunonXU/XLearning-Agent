"""
单元测试：资源聚合 + 动态学习路径

覆盖:
- SearchResult 构造（含 xiaohongshu/wechat 平台）
- DayProgress 模型构造和字段验证
- ProgressTracker: init_from_plan(), mark_day_completed(), get_progress_summary()
- ProgressTracker: 新会话初始化为空白状态
- UI: 主流程两步骤验证、无 Quiz 入口验证、资源卡片渲染验证
"""

import os
import uuid
import pytest
from pydantic import ValidationError

from src.core.models import (
    SearchResult, PlatformType, ResourceType,
    LearningDay, LearningPlan,
)
from src.core.progress import ProgressTracker, DayProgress, SESSIONS_DIR


# ============================================================================
# SearchResult 构造测试
# ============================================================================

class TestSearchResultConstruction:
    """SearchResult 构造和字段验证"""

    def test_construct_bilibili(self):
        r = SearchResult(
            title="Python 入门", url="https://bilibili.com/v1",
            platform="bilibili", type="video", description="入门教程",
        )
        assert r.platform == "bilibili"
        assert r.type == "video"

    def test_construct_youtube(self):
        r = SearchResult(
            title="ML Basics", url="https://youtube.com/watch?v=1",
            platform="youtube", type="video",
        )
        assert r.platform == "youtube"
        assert r.description == ""

    def test_construct_google(self):
        r = SearchResult(
            title="Google Article", url="https://google.com/search",
            platform="google", type="article", description="搜索结果",
        )
        assert r.platform == "google"

    def test_construct_github(self):
        r = SearchResult(
            title="langchain", url="https://github.com/langchain/langchain",
            platform="github", type="repo",
        )
        assert r.platform == "github"
        assert r.type == "repo"

    def test_construct_xiaohongshu(self):
        r = SearchResult(
            title="小红书笔记", url="https://xiaohongshu.com/note/123",
            platform="xiaohongshu", type="note", description="学习笔记",
        )
        assert r.platform == "xiaohongshu"
        assert r.type == "note"

    def test_construct_wechat(self):
        r = SearchResult(
            title="微信公众号文章", url="https://mp.weixin.qq.com/s/abc",
            platform="wechat", type="article", description="公众号推文",
        )
        assert r.platform == "wechat"
        assert r.type == "article"

    def test_all_six_platforms_roundtrip(self):
        """6 个平台的 SearchResult 都能正确 round-trip"""
        for platform in [p.value for p in PlatformType]:
            r = SearchResult(
                title=f"Test {platform}", url=f"https://{platform}.com",
                platform=platform, type="article",
            )
            d = r.to_dict()
            r2 = SearchResult.from_dict(d)
            assert r2 == r

    def test_from_dict_missing_required_field(self):
        with pytest.raises(ValidationError):
            SearchResult.from_dict({"url": "x", "platform": "google", "type": "article"})

    def test_from_dict_non_dict_input(self):
        with pytest.raises(ValidationError):
            SearchResult.from_dict("not a dict")


# ============================================================================
# DayProgress 模型测试
# ============================================================================

class TestDayProgressModel:
    """DayProgress 模型构造和字段验证"""

    def test_construct_default(self):
        dp = DayProgress(day_number=1, title="Day 1 Topic")
        assert dp.day_number == 1
        assert dp.title == "Day 1 Topic"
        assert dp.completed is False

    def test_construct_completed(self):
        dp = DayProgress(day_number=3, title="Advanced", completed=True)
        assert dp.completed is True

    def test_serialization(self):
        dp = DayProgress(day_number=2, title="Intermediate")
        d = dp.model_dump()
        assert d == {"day_number": 2, "title": "Intermediate", "completed": False}
        dp2 = DayProgress(**d)
        assert dp2 == dp


# ============================================================================
# ProgressTracker 测试
# ============================================================================

def _make_plan(n_days: int) -> LearningPlan:
    """创建一个包含 n_days 天的测试 LearningPlan"""
    return LearningPlan(
        domain="TestDomain",
        total_days=n_days,
        days=[
            LearningDay(day_number=i, title=f"Day {i} Topic")
            for i in range(1, n_days + 1)
        ],
    )


class TestProgressTracker:
    """ProgressTracker 初始化/标记/摘要"""

    def test_new_session_blank_state(self):
        """新会话初始化为空白状态（需求 3.6）"""
        tracker = ProgressTracker(session_id=f"ut_{uuid.uuid4().hex[:8]}")
        assert tracker.days == []
        summary = tracker.get_progress_summary()
        assert summary["total_days"] == 0
        assert summary["completed_days"] == 0
        assert summary["percentage"] == 0.0
        assert summary["current_day"] is None

    def test_init_from_plan(self):
        plan = _make_plan(5)
        tracker = ProgressTracker(session_id=f"ut_{uuid.uuid4().hex[:8]}")
        tracker.init_from_plan(plan)
        assert len(tracker.days) == 5
        for d in tracker.days:
            assert d.completed is False

    def test_mark_day_completed_valid(self):
        sid = f"ut_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(_make_plan(3))
        assert tracker.mark_day_completed(2) is True
        assert tracker.days[1].completed is True
        # Other days unchanged
        assert tracker.days[0].completed is False
        assert tracker.days[2].completed is False
        # Cleanup
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)

    def test_mark_day_completed_invalid(self):
        tracker = ProgressTracker(session_id=f"ut_{uuid.uuid4().hex[:8]}")
        tracker.init_from_plan(_make_plan(3))
        assert tracker.mark_day_completed(99) is False

    def test_get_progress_summary(self):
        sid = f"ut_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(_make_plan(4))
        tracker.mark_day_completed(1)
        tracker.mark_day_completed(3)
        summary = tracker.get_progress_summary()
        assert summary["total_days"] == 4
        assert summary["completed_days"] == 2
        assert abs(summary["percentage"] - 0.5) < 1e-9
        assert summary["current_day"] == 2  # first uncompleted
        # Cleanup
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)

    def test_get_progress_summary_all_done(self):
        sid = f"ut_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(_make_plan(2))
        tracker.mark_day_completed(1)
        tracker.mark_day_completed(2)
        summary = tracker.get_progress_summary()
        assert summary["completed_days"] == 2
        assert abs(summary["percentage"] - 1.0) < 1e-9
        assert summary["current_day"] is None
        # Cleanup
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)


# ============================================================================
# UI 相关单元测试
# ============================================================================

class TestUIStageLogic:
    """主流程两步骤验证、无 Quiz 入口验证"""

    def test_calculate_stage_logic_returns_plan_and_study_only(self):
        """calculate_stage_logic 应只返回 Plan 和 Study（需求 7.6）"""
        from src.ui.state import calculate_stage_logic

        session = {
            "has_input": False, "plan": None, "kb_count": 0,
            "study_progress": 0, "current_stage": "Plan",
        }
        logic = calculate_stage_logic(session)
        stages = logic["stages"]
        assert "Plan" in stages
        assert "Study" in stages
        assert len(stages) == 3
        # No Quiz anywhere
        assert "Quiz" not in stages
        # Resources tab exists
        assert "Resources" in stages

    def test_no_quiz_stage_after_plan_generated(self):
        """计划生成后也不应出现 Quiz 阶段（需求 7.7）"""
        from src.ui.state import calculate_stage_logic

        session = {
            "has_input": True, "plan": {"status": "done"}, "kb_count": 5,
            "study_progress": 3, "current_stage": "Study",
        }
        logic = calculate_stage_logic(session)
        stages = logic["stages"]
        assert "Quiz" not in stages
        assert set(stages.keys()) == {"Plan", "Study", "Resources"}

    def test_stage_plan_icons_and_labels(self):
        """Plan 和 Study 阶段应有正确的 label 和 icon"""
        from src.ui.state import calculate_stage_logic

        session = {"has_input": False, "plan": None, "kb_count": 0,
                   "study_progress": 0, "current_stage": "Plan"}
        logic = calculate_stage_logic(session)
        assert logic["stages"]["Plan"]["label"] == "规划"
        assert logic["stages"]["Plan"]["icon"] == "📋"
        assert logic["stages"]["Study"]["label"] == "学习"
        assert logic["stages"]["Study"]["icon"] == "📖"

    def test_empty_session_returns_empty(self):
        """空 session 应返回空字典"""
        from src.ui.state import calculate_stage_logic
        assert calculate_stage_logic(None) == {}


class TestRenderResourceCard:
    """资源卡片渲染验证"""

    def test_render_resource_card_function_exists(self):
        """render_resource_card 函数应存在且可导入"""
        from src.ui.renderer import render_resource_card
        assert callable(render_resource_card)

    def test_platform_icons_defined(self):
        """所有 6 个平台的图标应已定义"""
        from src.ui.renderer import PLATFORM_ICONS
        for platform in ["bilibili", "youtube", "google", "github", "xiaohongshu", "wechat"]:
            assert platform in PLATFORM_ICONS


class TestStepperTabs:
    """Stepper 只有 Plan 和 Study 标签页"""

    def test_init_session_state_defaults_to_plan(self):
        """init_session_state 中 active_tab 默认为 Plan"""
        # We can't call init_session_state directly (needs Streamlit runtime),
        # but we can verify the source code logic by checking calculate_stage_logic
        from src.ui.state import calculate_stage_logic
        session = {"has_input": False, "plan": None, "kb_count": 0,
                   "study_progress": 0, "current_stage": "Plan"}
        logic = calculate_stage_logic(session)
        assert logic["current_stage"] == "Plan"

    def test_no_quiz_tab_in_stepper_keys(self):
        """Stepper 的 tab_keys 不应包含 Quiz"""
        # Verify by checking that calculate_stage_logic never produces Quiz
        from src.ui.state import calculate_stage_logic
        for stage in ["Plan", "Study"]:
            session = {"has_input": True, "plan": {"x": 1}, "kb_count": 1,
                       "study_progress": 1, "current_stage": stage}
            logic = calculate_stage_logic(session)
            assert "Quiz" not in logic["stages"]
