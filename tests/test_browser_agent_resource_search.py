"""
单元测试：智能浏览器 Agent 资源搜索
"""

import time
from unittest.mock import patch

from src.core.models import SearchResult
from src.specialists.search_cache import SearchCache


# ==================== SearchCache 测试 ====================


class TestSearchCache:
    """SearchCache 单元测试"""

    def _make_results(self, n: int = 2) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"Result {i}",
                url=f"https://example.com/{i}",
                platform="google",
                type="article",
            )
            for i in range(n)
        ]

    def test_set_and_get_within_ttl(self):
        """缓存命中返回正确结果"""
        cache = SearchCache(ttl=3600)
        results = self._make_results()
        cache.set("python", ["google", "github"], results)
        cached = cache.get("python", ["google", "github"])
        assert cached is not None
        assert len(cached) == 2
        assert cached[0].title == "Result 0"

    def test_get_returns_none_when_empty(self):
        """缓存未命中返回 None"""
        cache = SearchCache()
        assert cache.get("nonexistent", ["google"]) is None

    def test_cache_expired_returns_none(self):
        """缓存过期后返回 None"""
        cache = SearchCache(ttl=1)
        results = self._make_results()
        cache.set("python", ["google"], results)

        # Mock time to simulate expiry
        with patch("src.specialists.search_cache.time") as mock_time:
            # set was called with real time, so we need to simulate get after TTL
            mock_time.time.return_value = time.time() + 2
            assert cache.get("python", ["google"]) is None

    def test_default_ttl_is_3600(self):
        """默认 TTL 为 3600 秒"""
        cache = SearchCache()
        assert cache._ttl == 3600

    def test_platform_order_does_not_matter(self):
        """平台顺序不影响缓存键"""
        cache = SearchCache()
        results = self._make_results()
        cache.set("python", ["github", "google"], results)
        cached = cache.get("python", ["google", "github"])
        assert cached is not None
        assert len(cached) == 2

    def test_different_queries_different_cache(self):
        """不同查询使用不同缓存"""
        cache = SearchCache()
        results_a = self._make_results(1)
        results_b = self._make_results(3)
        cache.set("python", ["google"], results_a)
        cache.set("rust", ["google"], results_b)
        assert len(cache.get("python", ["google"])) == 1
        assert len(cache.get("rust", ["google"])) == 3

    def test_different_platforms_different_cache(self):
        """不同平台列表使用不同缓存"""
        cache = SearchCache()
        results_a = self._make_results(1)
        results_b = self._make_results(2)
        cache.set("python", ["google"], results_a)
        cache.set("python", ["github"], results_b)
        assert len(cache.get("python", ["google"])) == 1
        assert len(cache.get("python", ["github"])) == 2

    def test_make_key_deterministic(self):
        """相同输入生成相同的缓存键"""
        key1 = SearchCache._make_key("python", ["google", "github"])
        key2 = SearchCache._make_key("python", ["google", "github"])
        assert key1 == key2

    def test_make_key_sorted_platforms(self):
        """平台排序后生成相同的缓存键"""
        key1 = SearchCache._make_key("python", ["github", "google"])
        key2 = SearchCache._make_key("python", ["google", "github"])
        assert key1 == key2

    def test_expired_entry_is_cleaned_up(self):
        """过期条目在 get 时被清理"""
        cache = SearchCache(ttl=1)
        results = self._make_results()
        cache.set("python", ["google"], results)
        key = SearchCache._make_key("python", ["google"])

        with patch("src.specialists.search_cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            cache.get("python", ["google"])
            assert key not in cache._store


# ==================== ResourceCollector 测试 ====================

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.specialists.resource_collector import (
    ResourceCollector,
    _safe_int,
    _is_ad_comment,
    _extract_image_urls_from_json,
    COMMENT_FINGERPRINT_LEN,
    MAX_COMMENTS,
)
from src.specialists.browser_models import RawSearchResult, ResourceDetail
from src.specialists.platform_configs import (
    PlatformConfig,
    DetailSelectors,
    PLATFORM_CONFIGS,
)


class TestSafeInt:
    """_safe_int 辅助函数测试"""

    def test_int_value(self):
        assert _safe_int(42) == 42

    def test_string_int(self):
        assert _safe_int("123") == 123

    def test_none_returns_zero(self):
        assert _safe_int(None) == 0

    def test_empty_string_returns_zero(self):
        assert _safe_int("") == 0

    def test_chinese_wan(self):
        assert _safe_int("1.3万") == 13000

    def test_chinese_qian(self):
        assert _safe_int("2.5千") == 2500

    def test_comma_separated(self):
        assert _safe_int("1,234") == 1234

    def test_invalid_string(self):
        assert _safe_int("abc") == 0

    def test_zero(self):
        assert _safe_int(0) == 0


class TestIsAdComment:
    """广告评论过滤测试"""

    def test_normal_comment_not_ad(self):
        assert _is_ad_comment("这个教程真的很好用") is False

    def test_single_keyword_not_ad(self):
        assert _is_ad_comment("可以私信我问问") is False

    def test_two_keywords_is_ad(self):
        assert _is_ad_comment("私信我加我微信") is True

    def test_multiple_keywords_is_ad(self):
        assert _is_ad_comment("免费领优惠券，加我微信") is True

    def test_empty_string(self):
        assert _is_ad_comment("") is False


class TestExtractFromInterceptedJson:
    """extract_from_intercepted_json 测试"""

    def _make_config(self) -> PlatformConfig:
        return PLATFORM_CONFIGS["xiaohongshu"]

    def test_basic_extraction(self):
        config = self._make_config()
        items = [
            {
                "note_card": {
                    "note_id": "abc123",
                    "display_title": "Test Note",
                    "desc": "A description",
                    "interact_info": {
                        "liked_count": 100,
                        "collected_count": 50,
                        "comment_count": 10,
                    },
                    "user": {"nickname": "Author1"},
                },
                "xsec_token": "token123",
            }
        ]
        results = ResourceCollector.extract_from_intercepted_json(items, config)
        assert len(results) == 1
        assert results[0].title == "Test Note"
        assert "xsec_token=token123" in results[0].url
        assert results[0].engagement_metrics["likes"] == 100
        assert results[0].platform == "xiaohongshu"

    def test_dedup_by_note_id(self):
        config = self._make_config()
        items = [
            {
                "note_card": {
                    "note_id": "abc123",
                    "display_title": "First",
                    "interact_info": {},
                    "user": {},
                },
                "xsec_token": "",
            },
            {
                "note_card": {
                    "note_id": "abc123",
                    "display_title": "Duplicate",
                    "interact_info": {},
                    "user": {},
                },
                "xsec_token": "",
            },
        ]
        results = ResourceCollector.extract_from_intercepted_json(items, config)
        assert len(results) == 1

    def test_prefer_xsec_token(self):
        config = self._make_config()
        items = [
            {
                "note_card": {
                    "note_id": "abc123",
                    "display_title": "No Token",
                    "interact_info": {},
                    "user": {},
                },
                "xsec_token": "",
            },
            {
                "note_card": {
                    "note_id": "abc123",
                    "display_title": "With Token",
                    "interact_info": {},
                    "user": {},
                },
                "xsec_token": "tok999",
            },
        ]
        results = ResourceCollector.extract_from_intercepted_json(items, config)
        assert len(results) == 1
        assert "xsec_token=tok999" in results[0].url

    def test_empty_items(self):
        config = self._make_config()
        results = ResourceCollector.extract_from_intercepted_json([], config)
        assert results == []

    def test_missing_note_card(self):
        config = self._make_config()
        items = [{"something": "else"}]
        results = ResourceCollector.extract_from_intercepted_json(items, config)
        assert results == []

    def test_no_exception_on_bad_data(self):
        config = self._make_config()
        items = [None, {"note_card": None}, {"note_card": {"note_id": ""}}]
        results = ResourceCollector.extract_from_intercepted_json(items, config)
        assert isinstance(results, list)


class TestParseInterceptedComments:
    """parse_intercepted_comments 测试"""

    def test_basic_parsing(self):
        raw = [
            {
                "content": "Great tutorial!",
                "like_count": 50,
                "user_info": {"nickname": "User1"},
            },
            {
                "content": "Very helpful",
                "like_count": 30,
                "user_info": {"nickname": "User2"},
            },
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        assert len(result) == 2
        assert result[0]["likes"] == "50"  # sorted by likes desc
        assert result[0]["text"] == "Great tutorial!"

    def test_dedup_by_fingerprint(self):
        raw = [
            {"content": "Same comment here with more text", "like_count": 10, "user_info": {}},
            {"content": "Same comment here with more text but different ending", "like_count": 5, "user_info": {}},
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        assert len(result) == 1

    def test_ad_filtering(self):
        raw = [
            {"content": "私信我加我微信免费领", "like_count": 100, "user_info": {}},
            {"content": "Normal comment", "like_count": 5, "user_info": {}},
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        assert len(result) == 1
        assert result[0]["text"] == "Normal comment"

    def test_skip_short_comments(self):
        raw = [
            {"content": "ok", "like_count": 10, "user_info": {}},
            {"content": "", "like_count": 5, "user_info": {}},
            {"content": "This is a real comment", "like_count": 1, "user_info": {}},
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        assert len(result) == 1

    def test_max_comments_limit(self):
        raw = [
            {"content": f"Comment number {i} with enough text", "like_count": i, "user_info": {}}
            for i in range(20)
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        assert len(result) <= MAX_COMMENTS

    def test_sorted_by_likes_desc(self):
        raw = [
            {"content": "Low likes comment here", "like_count": 1, "user_info": {}},
            {"content": "High likes comment here", "like_count": 100, "user_info": {}},
            {"content": "Medium likes comment here", "like_count": 50, "user_info": {}},
        ]
        result = ResourceCollector.parse_intercepted_comments(raw)
        likes = [int(c["likes"]) for c in result]
        assert likes == sorted(likes, reverse=True)

    def test_empty_input(self):
        assert ResourceCollector.parse_intercepted_comments([]) == []


class TestExtractImageUrlsFromJson:
    """_extract_image_urls_from_json 辅助函数测试"""

    def test_note_card_image_list(self):
        data = {
            "note_card": {
                "image_list": [
                    {"url_default": "https://img.example.com/1.jpg"},
                    {"url": "https://img.example.com/2.jpg"},
                ]
            }
        }
        urls = _extract_image_urls_from_json(data)
        assert len(urls) == 2
        assert "https://img.example.com/1.jpg" in urls

    def test_nested_note_image_list(self):
        data = {
            "note": {
                "imageList": [
                    {"urlDefault": "https://img.example.com/a.jpg"},
                ]
            }
        }
        urls = _extract_image_urls_from_json(data)
        assert len(urls) == 1

    def test_empty_data(self):
        assert _extract_image_urls_from_json({}) == []

    def test_filters_non_http_urls(self):
        data = {
            "image_list": [
                {"url": "https://valid.com/img.jpg"},
                {"url": "data:image/png;base64,abc"},
                {"url": ""},
            ]
        }
        urls = _extract_image_urls_from_json(data)
        assert len(urls) == 1

    def test_max_9_images(self):
        data = {
            "image_list": [
                {"url": f"https://img.example.com/{i}.jpg"} for i in range(15)
            ]
        }
        urls = _extract_image_urls_from_json(data)
        assert len(urls) <= 9


class TestExtractSearchResultsAsync:
    """extract_search_results 异步测试"""

    @pytest.fixture
    def google_config(self):
        return PLATFORM_CONFIGS["google"]

    def test_extract_search_results_basic(self, google_config):
        """基本 CSS 选择器提取"""
        # Mock page with query_selector_all
        mock_item = AsyncMock()
        mock_title = AsyncMock()
        mock_title.inner_text = AsyncMock(return_value="Test Title")
        mock_link = AsyncMock()
        mock_link.get_attribute = AsyncMock(return_value="https://example.com")
        mock_desc = AsyncMock()
        mock_desc.inner_text = AsyncMock(return_value="A description")

        mock_item.query_selector = AsyncMock(side_effect=lambda sel: {
            google_config.title_selector: mock_title,
            google_config.link_selector: mock_link,
            google_config.description_selector: mock_desc,
        }.get(sel))

        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_item])

        results = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_search_results(mock_page, google_config)
        )
        assert len(results) == 1
        assert results[0].title == "Test Title"
        assert results[0].url == "https://example.com"
        assert results[0].platform == "google"

    def test_extract_search_results_empty_page(self, google_config):
        """空页面返回空列表"""
        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[])

        results = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_search_results(mock_page, google_config)
        )
        assert results == []

    def test_extract_search_results_exception_returns_empty(self, google_config):
        """异常时返回空列表"""
        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(side_effect=Exception("Page error"))

        results = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_search_results(mock_page, google_config)
        )
        assert results == []


class TestExtractDetailFromInitialState:
    """extract_detail_from_initial_state 异步测试"""

    def test_returns_empty_on_exception(self):
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("JS error"))

        result = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_detail_from_initial_state(mock_page)
        )
        assert result == ""

    def test_returns_content_from_evaluate(self):
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="这是正文内容")

        result = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_detail_from_initial_state(mock_page)
        )
        assert result == "这是正文内容"

    def test_returns_empty_when_no_content(self):
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="")

        result = asyncio.get_event_loop().run_until_complete(
            ResourceCollector.extract_detail_from_initial_state(mock_page)
        )
        assert result == ""


# ==================== QualityScorer 测试 ====================

import asyncio
from unittest.mock import MagicMock

from src.specialists.quality_scorer import QualityScorer, _safe_num
from src.specialists.browser_models import RawSearchResult, ScoredResult


def _make_raw_result(**overrides) -> RawSearchResult:
    """创建测试用 RawSearchResult"""
    defaults = dict(
        title="GRE 备考攻略",
        url="https://example.com/note/123",
        platform="xiaohongshu",
        resource_type="note",
        description="三周速通 GRE 330",
        engagement_metrics={
            "likes": 13265,
            "collected": 21345,
            "comments_count": 224,
            "share_count": 100,
            "author": "学霸小姐姐",
        },
        comments=["今早327拿下了", "感谢分享"],
        content_snippet="GRE 备考分为三个阶段...",
        top_comments=[
            {"text": "今早327拿下了 感谢姐", "likes": 168},
            {"text": "请问用什么资料", "likes": 41},
        ],
    )
    defaults.update(overrides)
    return RawSearchResult(**defaults)


class TestQualityScorerHeuristic:
    """测试启发式评分（无 LLM）"""

    def test_score_batch_returns_scored_results(self):
        scorer = QualityScorer(llm_provider=None)
        results = [_make_raw_result(), _make_raw_result(title="另一个资源")]
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch(results)
        )
        assert len(scored) == 2
        for s in scored:
            assert isinstance(s, ScoredResult)
            assert 0.0 <= s.quality_score <= 1.0
            assert s.recommendation_reason != ""

    def test_heuristic_high_engagement_gets_higher_score(self):
        scorer = QualityScorer(llm_provider=None)
        high = _make_raw_result(
            engagement_metrics={"likes": 10000, "collected": 20000, "comments_count": 500}
        )
        low = _make_raw_result(
            engagement_metrics={"likes": 5, "collected": 2, "comments_count": 0}
        )
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([high, low])
        )
        assert scored[0].quality_score > scored[1].quality_score

    def test_heuristic_empty_metrics_returns_valid_score(self):
        scorer = QualityScorer(llm_provider=None)
        result = _make_raw_result(
            engagement_metrics={},
            comments=[],
            top_comments=[],
            content_snippet="",
            description="",
        )
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([result])
        )
        assert scored[0].quality_score == 0.0
        assert "缺失维度" in scored[0].recommendation_reason

    def test_heuristic_bonus_for_comments(self):
        scorer = QualityScorer(llm_provider=None)
        with_comments = _make_raw_result(
            engagement_metrics={"likes": 100, "collected": 50, "comments_count": 10},
            top_comments=[{"text": "好评", "likes": 5}],
            content_snippet="",
            description="",
        )
        without_comments = _make_raw_result(
            engagement_metrics={"likes": 100, "collected": 50, "comments_count": 10},
            comments=[],
            top_comments=[],
            content_snippet="",
            description="",
        )
        s1 = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([with_comments])
        )
        s2 = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([without_comments])
        )
        assert s1[0].quality_score > s2[0].quality_score

    def test_score_never_exceeds_1(self):
        scorer = QualityScorer(llm_provider=None)
        result = _make_raw_result(
            engagement_metrics={"likes": 999999, "collected": 999999, "comments_count": 999999},
        )
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([result])
        )
        assert scored[0].quality_score <= 1.0


class TestQualityScorerLLM:
    """测试 LLM 评分路径"""

    def test_llm_success_parses_json(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = '{"score": 0.85, "reason": "内容深度好，评论质量高"}'
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 0.85
        assert scored[0].recommendation_reason == "内容深度好，评论质量高"

    def test_llm_returns_json_in_code_block(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = '```json\n{"score": 0.72, "reason": "不错的资源"}\n```'
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 0.72

    def test_llm_failure_returns_defaults(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.side_effect = Exception("API timeout")
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 0.0
        assert scored[0].recommendation_reason == ""

    def test_llm_bad_format_returns_defaults(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = "这不是 JSON 格式的回复"
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 0.0
        assert scored[0].recommendation_reason == ""

    def test_llm_score_clamped_to_range(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = '{"score": 1.5, "reason": "超高分"}'
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 1.0

    def test_llm_negative_score_clamped(self):
        mock_llm = MagicMock()
        mock_llm.simple_chat.return_value = '{"score": -0.5, "reason": "低质量"}'
        scorer = QualityScorer(llm_provider=mock_llm)
        scored = asyncio.get_event_loop().run_until_complete(
            scorer.score_batch([_make_raw_result()])
        )
        assert scored[0].quality_score == 0.0


class TestBuildScoringPrompt:
    """测试 prompt 构建"""

    def test_prompt_contains_title_and_platform(self):
        scorer = QualityScorer()
        prompt = scorer._build_scoring_prompt(_make_raw_result())
        assert "GRE 备考攻略" in prompt
        assert "xiaohongshu" in prompt

    def test_prompt_contains_engagement_metrics(self):
        scorer = QualityScorer()
        prompt = scorer._build_scoring_prompt(_make_raw_result())
        assert "13265" in prompt
        assert "21345" in prompt

    def test_prompt_notes_missing_dimensions(self):
        scorer = QualityScorer()
        result = _make_raw_result(
            engagement_metrics={},
            comments=[],
            top_comments=[],
            content_snippet="",
            description="",
        )
        prompt = scorer._build_scoring_prompt(result)
        assert "缺失" in prompt or "数据缺失" in prompt

    def test_prompt_includes_top_comments(self):
        scorer = QualityScorer()
        prompt = scorer._build_scoring_prompt(_make_raw_result())
        assert "168赞" in prompt
        assert "今早327拿下了" in prompt


class TestParseScoreResponse:
    """测试 LLM 响应解析"""

    def test_parse_valid_json(self):
        scorer = QualityScorer()
        score, reason = scorer._parse_score_response(
            '{"score": 0.8, "reason": "好资源"}'
        )
        assert score == 0.8
        assert reason == "好资源"

    def test_parse_json_in_code_block(self):
        scorer = QualityScorer()
        score, reason = scorer._parse_score_response(
            '```json\n{"score": 0.6, "reason": "一般"}\n```'
        )
        assert score == 0.6

    def test_parse_invalid_returns_defaults(self):
        scorer = QualityScorer()
        score, reason = scorer._parse_score_response("not json at all")
        assert score == 0.0
        assert reason == ""

    def test_parse_clamps_score(self):
        scorer = QualityScorer()
        score, _ = scorer._parse_score_response('{"score": 2.0, "reason": "x"}')
        assert score == 1.0
        score2, _ = scorer._parse_score_response('{"score": -1.0, "reason": "x"}')
        assert score2 == 0.0


class TestSafeNum:
    """测试 _safe_num 辅助函数"""

    def test_int(self):
        assert _safe_num(42) == 42.0

    def test_float(self):
        assert _safe_num(3.14) == 3.14

    def test_string_number(self):
        assert _safe_num("100") == 100.0

    def test_none(self):
        assert _safe_num(None) == 0.0

    def test_invalid_string(self):
        assert _safe_num("abc") == 0.0


# ==================== SearchOrchestrator 测试 ====================

from src.specialists.search_orchestrator import (
    SearchOrchestrator,
    _xhs_composite_score,
    _is_ad_title,
    _to_num,
)
from src.specialists.browser_models import RawSearchResult, ScoredResult


class TestXhsCompositeScore:
    """小红书综合排序分测试"""

    def test_formula(self):
        r = RawSearchResult(
            title="Test",
            url="https://example.com",
            platform="xiaohongshu",
            resource_type="note",
            engagement_metrics={"comments_count": 10, "collected": 20, "likes": 30},
        )
        # 10*5 + 20*2 + 30*1 = 50 + 40 + 30 = 120
        assert _xhs_composite_score(r) == 120.0

    def test_empty_metrics(self):
        r = RawSearchResult(
            title="Test",
            url="https://example.com",
            platform="xiaohongshu",
            resource_type="note",
        )
        assert _xhs_composite_score(r) == 0.0

    def test_comments_weighted_highest(self):
        high_comments = RawSearchResult(
            title="A",
            url="u",
            platform="xiaohongshu",
            resource_type="note",
            engagement_metrics={"comments_count": 100, "collected": 0, "likes": 0},
        )
        high_likes = RawSearchResult(
            title="B",
            url="u",
            platform="xiaohongshu",
            resource_type="note",
            engagement_metrics={"comments_count": 0, "collected": 0, "likes": 100},
        )
        assert _xhs_composite_score(high_comments) > _xhs_composite_score(high_likes)


class TestIsAdTitle:
    """广告标题检测测试"""

    def test_normal_title(self):
        assert _is_ad_title("GRE 备考攻略") is False

    def test_ad_title(self):
        assert _is_ad_title("限时免费试听课程") is True

    def test_ad_keyword_报班(self):
        assert _is_ad_title("报班学习效果好") is True


class TestToNum:
    """_to_num 辅助函数测试"""

    def test_int(self):
        assert _to_num(42) == 42.0

    def test_none(self):
        assert _to_num(None) == 0.0

    def test_string(self):
        assert _to_num("100") == 100.0

    def test_invalid(self):
        assert _to_num("abc") == 0.0


class TestSearchOrchestratorToSearchResult:
    """_to_search_result 转换测试"""

    def test_basic_conversion(self):
        raw = RawSearchResult(
            title="Test Note",
            url="https://example.com/note/1",
            platform="xiaohongshu",
            resource_type="note",
            description="A test note",
            engagement_metrics={"likes": 100},
            top_comments=[{"text": "Great!", "likes": 50}],
        )
        scored = ScoredResult(
            raw=raw,
            quality_score=0.85,
            recommendation_reason="高质量内容",
        )
        result = SearchOrchestrator._to_search_result(scored)
        assert result.title == "Test Note"
        assert result.platform == "xiaohongshu"
        assert result.type == "note"
        assert result.quality_score == 0.85
        assert result.recommendation_reason == "高质量内容"
        assert result.engagement_metrics == {"likes": 100}
        assert "Great!" in result.comments_preview

    def test_conversion_with_content_snippet_as_description(self):
        raw = RawSearchResult(
            title="Note",
            url="https://example.com",
            platform="xiaohongshu",
            resource_type="note",
            description="",
            content_snippet="This is the content snippet from the detail page",
        )
        scored = ScoredResult(raw=raw, quality_score=0.5, recommendation_reason="ok")
        result = SearchOrchestrator._to_search_result(scored)
        assert "content snippet" in result.description

    def test_conversion_with_comments_fallback(self):
        raw = RawSearchResult(
            title="Note",
            url="https://example.com",
            platform="xiaohongshu",
            resource_type="note",
            comments=["Comment 1", "Comment 2"],
        )
        scored = ScoredResult(raw=raw, quality_score=0.3, recommendation_reason="")
        result = SearchOrchestrator._to_search_result(scored)
        assert len(result.comments_preview) == 2


class TestSearchOrchestratorAsync:
    """SearchOrchestrator 异步测试"""

    def test_search_all_platforms_cache_hit(self):
        """缓存命中时直接返回"""
        orch = SearchOrchestrator()
        # 预填充缓存
        cached_results = [
            SearchResult(
                title="Cached",
                url="https://example.com",
                platform="google",
                type="article",
                quality_score=0.9,
            )
        ]
        orch._cache.set("test query", ["google"], cached_results)

        results = asyncio.get_event_loop().run_until_complete(
            orch.search_all_platforms("test query", ["google"], top_k=10)
        )
        assert len(results) == 1
        assert results[0].title == "Cached"

    def test_search_all_platforms_invalid_platforms(self):
        """无效平台返回空列表"""
        orch = SearchOrchestrator()
        results = asyncio.get_event_loop().run_until_complete(
            orch.search_all_platforms("test", ["nonexistent_platform"], top_k=10)
        )
        assert results == []

    def test_expand_keywords_mvp(self):
        """MVP 阶段 expand_keywords 返回原始关键词"""
        orch = SearchOrchestrator()
        assert orch.expand_keywords("langchain") == ["langchain"]

    def test_search_all_platforms_respects_top_k(self):
        """缓存命中时 top_k 截断"""
        orch = SearchOrchestrator()
        cached_results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://example.com/{i}",
                platform="google",
                type="article",
                quality_score=1.0 - i * 0.1,
            )
            for i in range(10)
        ]
        orch._cache.set("test", ["google"], cached_results)

        results = asyncio.get_event_loop().run_until_complete(
            orch.search_all_platforms("test", ["google"], top_k=3)
        )
        assert len(results) == 3


# ==================== ResourceSearcher 测试 ====================

from src.specialists.resource_searcher import ResourceSearcher


class TestResourceSearcher:
    """ResourceSearcher 接口测试"""

    def test_has_search_method(self):
        """search 方法存在且可调用"""
        searcher = ResourceSearcher()
        assert hasattr(searcher, "search")
        assert callable(searcher.search)

    def test_platforms_list(self):
        """默认平台列表包含 6 个平台"""
        assert len(ResourceSearcher.PLATFORMS) == 6
        assert "xiaohongshu" in ResourceSearcher.PLATFORMS

    def test_empty_query_returns_empty(self):
        """空查询返回空列表"""
        searcher = ResourceSearcher()
        assert searcher.search("") == []
        assert searcher.search("   ") == []

    def test_default_top_k(self):
        """默认 top_k 为 10"""
        assert ResourceSearcher.DEFAULT_TOP_K == 10
