"""
属性测试：资源聚合 + 动态学习路径

Feature: resource-aggregation-dynamic-learning
使用 hypothesis 进行 property-based testing
"""

import pytest
from typing import List
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from pydantic import ValidationError

from src.core.models import SearchResult, PlatformType, ResourceType


# ==================== 策略定义 ====================

VALID_PLATFORMS = [p.value for p in PlatformType]
VALID_TYPES = [t.value for t in ResourceType]


def search_result_strategy():
    """生成有效的 SearchResult 数据"""
    return st.builds(
        SearchResult,
        title=st.text(min_size=1, max_size=200),
        url=st.text(min_size=1, max_size=500),
        platform=st.sampled_from(VALID_PLATFORMS),
        type=st.sampled_from(VALID_TYPES),
        description=st.text(max_size=500),
    )


# ==================== Property 1: SearchResult round-trip ====================
# Feature: resource-aggregation-dynamic-learning, Property 1: SearchResult round-trip


class TestSearchResultRoundTrip:
    """
    Property 1: SearchResult 序列化 round-trip

    For any valid SearchResult, serializing to dict then deserializing
    should produce an equivalent SearchResult.

    **Validates: Requirements 6.1, 6.2**
    """

    @given(result=search_result_strategy())
    @settings(max_examples=100)
    def test_to_dict_from_dict_roundtrip(self, result: SearchResult):
        """序列化为 dict 再反序列化应产生等价对象"""
        serialized = result.to_dict()
        deserialized = SearchResult.from_dict(serialized)
        assert deserialized == result

    @given(result=search_result_strategy())
    @settings(max_examples=100)
    def test_to_dict_contains_all_fields(self, result: SearchResult):
        """to_dict() 应包含所有字段"""
        d = result.to_dict()
        assert "title" in d
        assert "url" in d
        assert "platform" in d
        assert "type" in d
        assert "description" in d
        assert d["title"] == result.title
        assert d["url"] == result.url
        assert d["platform"] == result.platform
        assert d["type"] == result.type
        assert d["description"] == result.description


# ==================== Property 8: 无效 JSON 错误处理 ====================
# Feature: resource-aggregation-dynamic-learning, Property 8: 无效 JSON 错误处理


class TestSearchResultInvalidInput:
    """
    Property 8: SearchResult 无效 JSON 错误处理

    For any invalid input, SearchResult.from_dict() should raise
    ValidationError, not KeyError/TypeError.

    **Validates: Requirements 6.4**
    """

    @given(
        data=st.fixed_dictionaries({
            # Missing 'title' - required field
            "url": st.text(min_size=1),
            "platform": st.sampled_from(VALID_PLATFORMS),
            "type": st.sampled_from(VALID_TYPES),
        })
    )
    @settings(max_examples=100)
    def test_missing_title_raises_validation_error(self, data: dict):
        """缺少 title 字段应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            SearchResult.from_dict(data)

    @given(
        data=st.fixed_dictionaries({
            "title": st.text(min_size=1),
            # Missing 'url' - required field
            "platform": st.sampled_from(VALID_PLATFORMS),
            "type": st.sampled_from(VALID_TYPES),
        })
    )
    @settings(max_examples=100)
    def test_missing_url_raises_validation_error(self, data: dict):
        """缺少 url 字段应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            SearchResult.from_dict(data)

    @given(
        data=st.fixed_dictionaries({
            "title": st.text(min_size=1),
            "url": st.text(min_size=1),
            # Missing 'platform' - required field
            "type": st.sampled_from(VALID_TYPES),
        })
    )
    @settings(max_examples=100)
    def test_missing_platform_raises_validation_error(self, data: dict):
        """缺少 platform 字段应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            SearchResult.from_dict(data)

    @given(
        data=st.fixed_dictionaries({
            "title": st.text(min_size=1),
            "url": st.text(min_size=1),
            "platform": st.sampled_from(VALID_PLATFORMS),
            # Missing 'type' - required field
        })
    )
    @settings(max_examples=100)
    def test_missing_type_raises_validation_error(self, data: dict):
        """缺少 type 字段应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            SearchResult.from_dict(data)

    @given(data=st.integers() | st.text() | st.lists(st.integers()) | st.none())
    @settings(max_examples=100)
    def test_non_dict_input_raises_validation_error(self, data):
        """非字典输入应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            SearchResult.from_dict(data)

    @given(
        data=st.fixed_dictionaries({
            "title": st.integers(),  # Wrong type: should be str
            "url": st.text(min_size=1),
            "platform": st.sampled_from(VALID_PLATFORMS),
            "type": st.sampled_from(VALID_TYPES),
        })
    )
    @settings(max_examples=100)
    def test_wrong_type_field_coercion_or_error(self, data: dict):
        """字段类型错误时，Pydantic 会尝试强制转换或抛出 ValidationError"""
        # Pydantic v2 will coerce int to str, so this should not raise KeyError/TypeError
        # It either succeeds (coercion) or raises ValidationError
        try:
            result = SearchResult.from_dict(data)
            # If coercion succeeds, title should be a string
            assert isinstance(result.title, str)
        except ValidationError:
            pass  # ValidationError is acceptable


# ==================== Property 2: 平台故障容错 ====================
# Feature: resource-aggregation-dynamic-learning, Property 2: 平台故障容错


def _make_failing_method(platform_name: str):
    """创建一个会抛出异常的搜索方法"""
    def _failing(query: str) -> list:
        raise Exception(f"{platform_name} simulated failure")
    return _failing


def _make_working_method(platform_name: str):
    """创建一个返回固定结果的搜索方法"""
    def _working(query: str) -> list:
        return [
            SearchResult(
                title=f"Test from {platform_name}",
                url=f"https://example.com/{platform_name}",
                platform=platform_name,
                type="article",
                description=f"Test result from {platform_name}",
            )
        ]
    return _working


class TestPlatformFaultTolerance:
    """
    Property 2: ResourceSearcher 平台故障容错

    For any search query and any subset of platform failures (1-5 platforms failing),
    ResourceSearcher should still return results from non-failing platforms
    without throwing exceptions.

    **Validates: Requirements 1.4**
    """

    @given(
        query=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        failing_platforms=st.lists(
            st.sampled_from(["bilibili", "youtube", "google", "github", "xiaohongshu", "wechat"]),
            min_size=1,
            max_size=5,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_failing_platforms_do_not_raise(self, query: str, failing_platforms: list):
        """任意平台子集失败时，search() 不应抛出异常"""
        from src.specialists.resource_searcher import ResourceSearcher

        searcher = ResourceSearcher()

        # 让失败平台抛出异常，工作平台返回固定结果
        all_platforms = set(ResourceSearcher.PLATFORMS)
        working_platforms = all_platforms - set(failing_platforms)

        for platform in failing_platforms:
            searcher._platform_methods[platform] = _make_failing_method(platform)
        for platform in working_platforms:
            searcher._platform_methods[platform] = _make_working_method(platform)

        # search() 不应抛出异常
        results = searcher.search(query)
        assert isinstance(results, list)

    @given(
        query=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        failing_platforms=st.lists(
            st.sampled_from(["bilibili", "youtube", "google", "github", "xiaohongshu", "wechat"]),
            min_size=1,
            max_size=5,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_non_failing_platforms_still_return_results(self, query: str, failing_platforms: list):
        """非故障平台应仍然返回结果"""
        from src.specialists.resource_searcher import ResourceSearcher

        searcher = ResourceSearcher()
        all_platforms = set(ResourceSearcher.PLATFORMS)
        working_platforms = all_platforms - set(failing_platforms)

        # 让失败平台抛出异常
        for platform in failing_platforms:
            searcher._platform_methods[platform] = _make_failing_method(platform)

        # 让工作平台返回可预测的结果
        for platform in working_platforms:
            searcher._platform_methods[platform] = _make_working_method(platform)

        results = searcher.search(query)
        assert isinstance(results, list)

        # 结果应只来自工作平台
        result_platforms = {r.platform for r in results}
        assert result_platforms.issubset(working_platforms)
        # 每个工作平台应贡献结果
        assert result_platforms == working_platforms


# ==================== Strategies for ProgressTracker tests ====================

import os
import uuid

from src.core.models import LearningPlan, LearningDay
from src.core.progress import ProgressTracker, DayProgress, SESSIONS_DIR


def learning_plan_strategy():
    """生成有效的 LearningPlan（按天组织）"""
    return st.integers(min_value=1, max_value=20).flatmap(
        lambda n: st.builds(
            LearningPlan,
            domain=st.just("TestDomain"),
            total_days=st.just(n),
            days=st.just([
                LearningDay(day_number=i, title=f"Day {i} Topic")
                for i in range(1, n + 1)
            ]),
        )
    )


def mark_operations_strategy(max_day: int):
    """生成 mark_day_completed 操作序列（可包含重复和无效 day_number）"""
    return st.lists(
        st.integers(min_value=0, max_value=max_day + 5),
        min_size=0,
        max_size=30,
    )


# ==================== Property 4: 每日完成状态一致性 ====================
# Feature: resource-aggregation-dynamic-learning, Property 4: 每日完成状态一致性


class TestDayCompletionConsistency:
    """
    Property 4: ProgressTracker 每日完成状态一致性

    For any initialized ProgressTracker and any sequence of mark_day_completed
    operations, the tracker state should accurately reflect all marked completions,
    and unmarked days should remain uncompleted.

    **Validates: Requirements 3.1, 3.2**
    """

    @given(
        plan=learning_plan_strategy(),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_marked_days_are_completed(self, plan: LearningPlan, data):
        """标记的天应为 completed=True，未标记的天应为 completed=False"""
        sid = f"prop4_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(plan)

        max_day = plan.total_days
        operations = data.draw(mark_operations_strategy(max_day))

        valid_day_numbers = {d.day_number for d in plan.days}
        marked_days = set()

        for day_num in operations:
            result = tracker.mark_day_completed(day_num)
            if day_num in valid_day_numbers:
                assert result is True
                marked_days.add(day_num)
            else:
                assert result is False

        # Verify state consistency
        for day in tracker.days:
            if day.day_number in marked_days:
                assert day.completed is True, (
                    f"Day {day.day_number} was marked but completed={day.completed}"
                )
            else:
                assert day.completed is False, (
                    f"Day {day.day_number} was NOT marked but completed={day.completed}"
                )

        # Cleanup session file
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)

    @given(plan=learning_plan_strategy())
    @settings(max_examples=100)
    def test_init_all_uncompleted(self, plan: LearningPlan):
        """初始化后所有天应为 completed=False"""
        tracker = ProgressTracker(session_id=f"prop4_init_{uuid.uuid4().hex[:8]}")
        tracker.init_from_plan(plan)

        for day in tracker.days:
            assert day.completed is False
        assert len(tracker.days) == len(plan.days)


# ==================== Property 5: 线性进度摘要正确性 ====================
# Feature: resource-aggregation-dynamic-learning, Property 5: 线性进度摘要正确性


class TestProgressSummaryCorrectness:
    """
    Property 5: 进度摘要计算正确性（线性进度条）

    For any ProgressTracker state, get_progress_summary() should return:
    - completed_days == count of completed=True days
    - percentage == completed_days / total_days (0.0 if empty)
    - current_day == first uncompleted day's day_number (None if all done)

    **Validates: Requirements 3.3, 3.4**
    """

    @given(
        plan=learning_plan_strategy(),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_summary_matches_state(self, plan: LearningPlan, data):
        """摘要应准确反映 tracker 内部状态"""
        sid = f"prop5_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(plan)

        valid_days = {d.day_number for d in plan.days}
        ops = data.draw(st.lists(
            st.sampled_from(sorted(valid_days)),
            min_size=0,
            max_size=len(valid_days),
            unique=True,
        ))

        for day_num in ops:
            tracker.mark_day_completed(day_num)

        summary = tracker.get_progress_summary()

        # completed_days == count of completed=True
        actual_completed = sum(1 for d in tracker.days if d.completed)
        assert summary["completed_days"] == actual_completed

        # total_days
        assert summary["total_days"] == len(plan.days)

        # percentage
        expected_pct = actual_completed / len(plan.days) if len(plan.days) > 0 else 0.0
        assert abs(summary["percentage"] - expected_pct) < 1e-9

        # current_day == first uncompleted day
        expected_current = next(
            (d.day_number for d in tracker.days if not d.completed), None
        )
        assert summary["current_day"] == expected_current

        # Cleanup
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)

    @given(data=st.data())
    @settings(max_examples=50)
    def test_empty_tracker_summary(self, data):
        """空 tracker 的摘要应为零值"""
        tracker = ProgressTracker(session_id=f"prop5_empty_{uuid.uuid4().hex[:8]}")
        summary = tracker.get_progress_summary()

        assert summary["total_days"] == 0
        assert summary["completed_days"] == 0
        assert summary["percentage"] == 0.0
        assert summary["current_day"] is None


# ==================== Property 6: 持久化 round-trip ====================
# Feature: resource-aggregation-dynamic-learning, Property 6: 持久化 round-trip


class TestPersistenceRoundTrip:
    """
    Property 6: ProgressTracker 持久化 round-trip

    For any ProgressTracker state, save() then load() should produce
    equivalent progress state.

    **Validates: Requirements 3.5**
    """

    @given(
        plan=learning_plan_strategy(),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_save_load_roundtrip(self, plan: LearningPlan, data):
        """save() 后 load() 应恢复等价状态"""
        sid = f"prop6_{uuid.uuid4().hex[:8]}"
        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(plan)

        valid_days = {d.day_number for d in plan.days}
        ops = data.draw(st.lists(
            st.sampled_from(sorted(valid_days)),
            min_size=0,
            max_size=len(valid_days),
            unique=True,
        ))

        for day_num in ops:
            tracker.mark_day_completed(day_num)

        tracker.save()

        # Load into a fresh tracker
        tracker2 = ProgressTracker(session_id=sid)
        tracker2.load()

        # Compare states
        assert len(tracker2.days) == len(tracker.days)
        for d1, d2 in zip(tracker.days, tracker2.days):
            assert d1.day_number == d2.day_number
            assert d1.title == d2.title
            assert d1.completed == d2.completed

        # Cleanup
        path = SESSIONS_DIR / f"{sid}.json"
        if path.exists():
            os.remove(path)

    @given(plan=learning_plan_strategy())
    @settings(max_examples=50)
    def test_save_preserves_existing_session_data(self, plan: LearningPlan):
        """save() 不应覆盖 session 文件中的其他数据"""
        import json

        sid = f"prop6_preserve_{uuid.uuid4().hex[:8]}"
        path = SESSIONS_DIR / f"{sid}.json"

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        # Write some pre-existing session data
        existing = {"current_stage": "Plan", "has_input": True}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f)

        tracker = ProgressTracker(session_id=sid)
        tracker.init_from_plan(plan)
        tracker.save()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Existing keys should still be present
        assert data["current_stage"] == "Plan"
        assert data["has_input"] is True
        # Progress key should exist
        assert "progress" in data

        # Cleanup
        if path.exists():
            os.remove(path)


# ==================== Property 3: 学习计划资源多平台覆盖 ====================
# Feature: resource-aggregation-dynamic-learning, Property 3: 学习计划资源多平台覆盖

from unittest.mock import patch, MagicMock


def _mock_resource_searcher_results(query: str) -> List[SearchResult]:
    """
    模拟 ResourceSearcher.search() 返回多平台结果。
    每次调用返回至少 2 个来自不同平台的 SearchResult。
    """
    return [
        SearchResult(
            title=f"Bilibili: {query}",
            url=f"https://www.bilibili.com/video/{query.replace(' ', '_')}",
            platform="bilibili",
            type="video",
            description=f"Bilibili video about {query}",
        ),
        SearchResult(
            title=f"YouTube: {query}",
            url=f"https://www.youtube.com/watch?v={query.replace(' ', '_')}",
            platform="youtube",
            type="video",
            description=f"YouTube video about {query}",
        ),
        SearchResult(
            title=f"Google: {query}",
            url=f"https://www.google.com/search?q={query.replace(' ', '_')}",
            platform="google",
            type="article",
            description=f"Google article about {query}",
        ),
    ]


def learning_day_strategy():
    """生成随机的 LearningDay 列表（1-7 天）"""
    return st.integers(min_value=1, max_value=7).flatmap(
        lambda n: st.lists(
            st.builds(
                LearningDay,
                day_number=st.just(0),  # placeholder, will be overridden
                title=st.text(
                    alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
                    min_size=3,
                    max_size=50,
                ).filter(lambda x: x.strip()),
                topics=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=5),
                resources=st.just([]),
            ),
            min_size=n,
            max_size=n,
        ).map(lambda days: [
            LearningDay(day_number=i + 1, title=d.title, topics=d.topics, resources=[])
            for i, d in enumerate(days)
        ])
    )


class TestMultiPlatformResourceCoverage:
    """
    Property 3: 学习计划资源多平台覆盖

    For any LearningPlan generated by Planner (when ResourceSearcher returns
    normal results), each LearningDay should have at least 2 SearchResults
    from different platforms.

    **Validates: Requirements 2.2, 1.2**
    """

    @given(
        domain=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
            min_size=2,
            max_size=30,
        ).filter(lambda x: x.strip()),
        days=learning_day_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_each_day_has_multi_platform_resources(self, domain: str, days):
        """当 ResourceSearcher 正常返回时，每天应至少有 2 个不同平台的资源"""
        from src.agents.planner import PlannerAgent

        plan = LearningPlan(
            domain=domain,
            total_days=len(days),
            days=days,
        )

        # Mock LLM provider so PlannerAgent can be instantiated
        mock_llm = MagicMock()
        planner = PlannerAgent(llm_provider=mock_llm)

        # Mock ResourceSearcher.search to return multi-platform results
        with patch(
            "src.agents.planner.ResourceSearcher"
        ) as MockSearcherClass:
            mock_searcher_instance = MagicMock()
            mock_searcher_instance.search.side_effect = _mock_resource_searcher_results
            MockSearcherClass.return_value = mock_searcher_instance

            result_plan = planner._search_resources_for_plan(plan)

        # Verify: each day should have at least 2 SearchResults from different platforms
        for day in result_plan.days:
            search_results = [r for r in day.resources if isinstance(r, SearchResult)]
            assert len(search_results) >= 2, (
                f"Day {day.day_number} has {len(search_results)} SearchResults, expected >= 2"
            )
            platforms = {r.platform for r in search_results}
            assert len(platforms) >= 2, (
                f"Day {day.day_number} has resources from {len(platforms)} platform(s), expected >= 2"
            )

    @given(
        domain=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
            min_size=2,
            max_size=30,
        ).filter(lambda x: x.strip()),
        days=learning_day_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_degradation_when_search_fails(self, domain: str, days):
        """当 ResourceSearcher 搜索失败时，每天应标注"暂无推荐资源"而非抛出异常"""
        from src.agents.planner import PlannerAgent

        plan = LearningPlan(
            domain=domain,
            total_days=len(days),
            days=days,
        )

        mock_llm = MagicMock()
        planner = PlannerAgent(llm_provider=mock_llm)

        # Mock ResourceSearcher.search to raise an exception
        with patch(
            "src.agents.planner.ResourceSearcher"
        ) as MockSearcherClass:
            mock_searcher_instance = MagicMock()
            mock_searcher_instance.search.side_effect = Exception("Network error")
            MockSearcherClass.return_value = mock_searcher_instance

            result_plan = planner._search_resources_for_plan(plan)

        # Verify: each day should have "暂无推荐资源" fallback
        for day in result_plan.days:
            assert "暂无推荐资源" in day.resources, (
                f"Day {day.day_number} missing fallback '暂无推荐资源' when search fails"
            )


# ==================== Property 10: Tutor 回复参考来源完整性 ====================
# Feature: resource-aggregation-dynamic-learning, Property 10: Tutor 回复参考来源完整性


def source_strategy():
    """生成随机的来源列表（可为空，可包含 pdf/search/rag 类型）"""
    pdf_source = st.fixed_dictionaries({
        "type": st.just("pdf"),
        "filename": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        "section": st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    })
    search_source = st.fixed_dictionaries({
        "type": st.just("search"),
        "platforms": st.lists(
            st.sampled_from(VALID_PLATFORMS),
            min_size=1,
            max_size=4,
            unique=True,
        ),
        "query": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    })
    rag_source = st.fixed_dictionaries({
        "type": st.just("rag"),
        "source": st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    })
    return st.lists(
        st.one_of(pdf_source, search_source, rag_source),
        min_size=0,
        max_size=5,
    )


class TestTutorReferenceCompleteness:
    """
    Property 10: Tutor 回复参考来源完整性

    For any Tutor response, the response text should end with a 「📎 参考来源」
    section. When external sources are referenced, the section should list
    specific sources; when no external sources are used, it should note
    "基于 AI 通用知识".

    **Validates: Requirements 5.1, 5.5**
    """

    @given(sources=source_strategy())
    @settings(max_examples=100, deadline=None)
    def test_reference_section_always_present(self, sources: list):
        """_build_reference_section 应始终返回包含「📎 参考来源」的文本"""
        from src.agents.tutor import TutorAgent

        mock_llm = MagicMock()
        tutor = TutorAgent(llm_provider=mock_llm)

        section = tutor._build_reference_section(sources)
        assert "📎 参考来源" in section

    @given(sources=source_strategy().filter(lambda s: len(s) == 0))
    @settings(max_examples=100, deadline=None)
    def test_empty_sources_shows_ai_knowledge(self, sources: list):
        """当来源为空时，应标注「基于 AI 通用知识」"""
        from src.agents.tutor import TutorAgent

        mock_llm = MagicMock()
        tutor = TutorAgent(llm_provider=mock_llm)

        section = tutor._build_reference_section(sources)
        assert "📎 参考来源" in section
        assert "基于 AI 通用知识" in section

    @given(sources=source_strategy().filter(lambda s: len(s) > 0))
    @settings(max_examples=100, deadline=None)
    def test_non_empty_sources_lists_details(self, sources: list):
        """当有外部来源时，应列出具体来源而非「基于 AI 通用知识」"""
        from src.agents.tutor import TutorAgent

        mock_llm = MagicMock()
        tutor = TutorAgent(llm_provider=mock_llm)

        section = tutor._build_reference_section(sources)
        assert "📎 参考来源" in section
        assert "基于 AI 通用知识" not in section

        # 验证每种来源类型都被正确列出
        for src in sources:
            if src["type"] == "pdf":
                assert f"PDF: {src['filename']}" in section
                assert src["section"] in section
            elif src["type"] == "search":
                assert "搜索:" in section
                assert src["query"] in section
                for platform in src["platforms"]:
                    assert platform in section
            elif src["type"] == "rag":
                assert f"RAG: 检索片段来自 {src['source']}" in section

    @given(
        sources=source_strategy(),
        llm_response=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, deadline=None)
    def test_handle_free_mode_appends_reference(self, sources: list, llm_response: str):
        """_handle_free_mode 的回复末尾应包含「📎 参考来源」区块"""
        from src.agents.tutor import TutorAgent

        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = llm_response
        tutor = TutorAgent(llm_provider=mock_llm)

        # Pre-populate sources to simulate tracking
        tutor._current_sources = list(sources)

        # Call _handle_free_mode (no RAG, no history)
        response = tutor._handle_free_mode("你好", history=None, use_rag=False)

        assert "📎 参考来源" in response
        # The response should start with the LLM response
        assert response.startswith(llm_response)


# ==================== Property 9: Orchestrator 意图路由优先级（无 Quiz）====================
# Feature: resource-aggregation-dynamic-learning, Property 9: 意图路由优先级（无 Quiz）


# --- 关键词常量 ---
CREATE_PLAN_KEYWORDS = [
    "生成计划", "学习计划", "plan for", "roadmap", "学习规划", "生成大纲",
    "做一个规划", "做个规划", "帮我规划", "规划一下", "给我规划",
    "做一个计划", "做个计划", "给我做一个", "给我做个",
]

SEARCH_RESOURCE_KEYWORDS = [
    "搜索资源", "找资源", "推荐资源", "search resource",
    "搜索更多资源", "找学习资源", "推荐学习资源",
    "有什么资源", "资源推荐",
]

QUIZ_KEYWORDS = ["测验", "quiz", "测试", "考试", "出题", "题目"]


def _make_orchestrator():
    """创建一个用于测试意图检测的 Orchestrator 实例（不需要真实 LLM）"""
    from src.agents.orchestrator import Orchestrator, OrchestratorMode

    orch = Orchestrator.__new__(Orchestrator)
    orch.mode = OrchestratorMode.STANDALONE
    orch._intent_cache = {}
    orch._last_intent_meta = {"source": "init", "intent": "ask_question"}
    return orch


class TestIntentRoutingPriority:
    """
    Property 9: Orchestrator 意图路由优先级（无 Quiz）

    For any user input that matches multiple intent keywords, Orchestrator
    should return the highest priority intent according to:
    create_plan > ask_question > search_resource.
    No start_quiz intent should exist.

    **Validates: Requirements 7.6**
    """

    @given(
        plan_kw=st.sampled_from(CREATE_PLAN_KEYWORDS),
        resource_kw=st.sampled_from(SEARCH_RESOURCE_KEYWORDS),
        filler=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    )
    @settings(max_examples=100, deadline=None)
    def test_create_plan_beats_search_resource(self, plan_kw: str, resource_kw: str, filler: str):
        """当输入同时包含 create_plan 和 search_resource 关键词时，应返回 create_plan"""
        orch = _make_orchestrator()
        user_input = f"{filler} {plan_kw} {resource_kw} {filler}"
        intent = orch._detect_intent_by_keywords(user_input)
        assert intent == "create_plan", (
            f"Expected create_plan but got {intent} for input: {user_input!r}"
        )

    @given(
        resource_kw=st.sampled_from(SEARCH_RESOURCE_KEYWORDS),
        filler=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    )
    @settings(max_examples=100, deadline=None)
    def test_search_resource_detected_alone(self, resource_kw: str, filler: str):
        """当输入仅包含 search_resource 关键词时，应返回 search_resource"""
        orch = _make_orchestrator()
        # Ensure no plan keywords are present
        user_input = f"{filler} {resource_kw} {filler}"
        has_plan_kw = any(kw in user_input.lower() for kw in CREATE_PLAN_KEYWORDS)
        has_analyze = "分析" in user_input.lower()
        assume(not has_plan_kw and not has_analyze)

        intent = orch._detect_intent_by_keywords(user_input)
        assert intent == "search_resource", (
            f"Expected search_resource but got {intent} for input: {user_input!r}"
        )

    @given(
        quiz_kw=st.sampled_from(QUIZ_KEYWORDS),
        filler=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    )
    @settings(max_examples=100, deadline=None)
    def test_no_start_quiz_intent(self, quiz_kw: str, filler: str):
        """任何包含 quiz 关键词的输入都不应返回 start_quiz"""
        orch = _make_orchestrator()
        user_input = f"{filler} {quiz_kw} {filler}"
        intent = orch._detect_intent_by_keywords(user_input)
        assert intent != "start_quiz", (
            f"start_quiz intent should not exist, but got it for input: {user_input!r}"
        )

    @given(
        plan_kw=st.sampled_from(CREATE_PLAN_KEYWORDS),
        filler=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    )
    @settings(max_examples=100, deadline=None)
    def test_create_plan_is_highest_priority(self, plan_kw: str, filler: str):
        """create_plan 关键词应始终返回 create_plan（最高优先级）"""
        orch = _make_orchestrator()
        user_input = f"{filler} {plan_kw} {filler}"
        # Exclude edge cases where "分析" appears in filler
        has_analyze = "分析" in user_input.lower()
        assume(not has_analyze)

        intent = orch._detect_intent_by_keywords(user_input)
        assert intent == "create_plan", (
            f"Expected create_plan but got {intent} for input: {user_input!r}"
        )


# ==================== Property 7: LearningDay resources 向后兼容 ====================
# Feature: resource-aggregation-dynamic-learning, Property 7: LearningDay resources 向后兼容


def mixed_resources_strategy():
    """生成混合 str/SearchResult 的 resources 列表"""
    str_resource = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    search_result_resource = st.builds(
        SearchResult,
        title=st.text(min_size=1, max_size=100),
        url=st.text(min_size=1, max_size=200),
        platform=st.sampled_from(VALID_PLATFORMS),
        type=st.sampled_from(VALID_TYPES),
        description=st.text(max_size=200),
    )
    return st.lists(
        st.one_of(str_resource, search_result_resource),
        min_size=0,
        max_size=10,
    )


class TestLearningDayBackwardCompatibility:
    """
    Property 7: LearningDay resources 向后兼容

    For any LearningDay, its resources field should accept:
    - Pure string list (old format)
    - SearchResult list (new format)
    - Mixed list of both

    Serialization/deserialization should preserve data for all formats.

    **Validates: Requirements 6.3**
    """

    @given(
        resources=st.lists(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_pure_string_resources(self, resources: list):
        """LearningDay 应接受纯字符串列表（旧格式）"""
        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )
        assert len(day.resources) == len(resources)
        for r in day.resources:
            assert isinstance(r, str)

    @given(
        resources=st.lists(
            st.builds(
                SearchResult,
                title=st.text(min_size=1, max_size=100),
                url=st.text(min_size=1, max_size=200),
                platform=st.sampled_from(VALID_PLATFORMS),
                type=st.sampled_from(VALID_TYPES),
                description=st.text(max_size=200),
            ),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_search_result_resources(self, resources: list):
        """LearningDay 应接受 SearchResult 列表（新格式）"""
        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )
        assert len(day.resources) == len(resources)
        for r in day.resources:
            assert isinstance(r, SearchResult)

    @given(resources=mixed_resources_strategy())
    @settings(max_examples=100)
    def test_mixed_resources(self, resources: list):
        """LearningDay 应接受混合列表（str + SearchResult）"""
        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )
        assert len(day.resources) == len(resources)
        for original, stored in zip(resources, day.resources):
            if isinstance(original, str):
                assert isinstance(stored, str)
                assert stored == original
            else:
                assert isinstance(stored, SearchResult)
                assert stored == original

    @given(resources=mixed_resources_strategy())
    @settings(max_examples=100)
    def test_serialization_roundtrip(self, resources: list):
        """序列化/反序列化应保留所有格式的数据"""
        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )

        # Serialize to dict
        serialized = day.model_dump()

        # Deserialize back
        deserialized = LearningDay.model_validate(serialized)

        assert deserialized.day_number == day.day_number
        assert deserialized.title == day.title
        assert deserialized.topics == day.topics
        assert len(deserialized.resources) == len(day.resources)

        for original, restored in zip(day.resources, deserialized.resources):
            if isinstance(original, str):
                assert isinstance(restored, str)
                assert restored == original
            elif isinstance(original, SearchResult):
                assert isinstance(restored, SearchResult)
                assert restored.title == original.title
                assert restored.url == original.url
                assert restored.platform == original.platform
                assert restored.type == original.type
                assert restored.description == original.description

    @given(
        resources=st.lists(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_string_resources_json_roundtrip(self, resources: list):
        """纯字符串资源的 JSON round-trip 应保持数据不变"""
        import json

        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )

        json_str = json.dumps(day.model_dump(), ensure_ascii=False)
        restored_data = json.loads(json_str)
        restored_day = LearningDay.model_validate(restored_data)

        assert restored_day.resources == day.resources

    @given(
        resources=st.lists(
            st.builds(
                SearchResult,
                title=st.text(min_size=1, max_size=100),
                url=st.text(min_size=1, max_size=200),
                platform=st.sampled_from(VALID_PLATFORMS),
                type=st.sampled_from(VALID_TYPES),
                description=st.text(max_size=200),
            ),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_search_result_resources_json_roundtrip(self, resources: list):
        """SearchResult 资源的 JSON round-trip 应保持数据不变"""
        import json

        day = LearningDay(
            day_number=1,
            title="Test Day",
            topics=["topic1"],
            resources=resources,
        )

        json_str = json.dumps(day.model_dump(), ensure_ascii=False)
        restored_data = json.loads(json_str)
        restored_day = LearningDay.model_validate(restored_data)

        assert len(restored_day.resources) == len(day.resources)
        for original, restored in zip(day.resources, restored_day.resources):
            assert isinstance(restored, SearchResult)
            assert restored.title == original.title
            assert restored.url == original.url
            assert restored.platform == original.platform
