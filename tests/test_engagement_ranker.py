"""
EngagementRanker 单元测试

测试互动数据初筛排序器的核心逻辑：
- 评论/点赞比例排序
- 标题关键词加权
- 广告关键词降权
- 输出数量约束
- 边界情况
"""

import pytest
from src.specialists.browser_models import RawSearchResult
from src.specialists.engagement_ranker import EngagementRanker


def _make_result(
    title: str = "测试文章",
    likes: int = 100,
    comments_count: int = 10,
    platform: str = "xiaohongshu",
) -> RawSearchResult:
    return RawSearchResult(
        title=title,
        url=f"https://example.com/{title}",
        platform=platform,
        resource_type="article",
        engagement_metrics={"likes": likes, "comments_count": comments_count},
    )


class TestEngagementScore:
    """测试 _engagement_score 计算逻辑"""

    def setup_method(self):
        self.ranker = EngagementRanker()

    def test_basic_ratio(self):
        """评论/点赞比例越高，分数越高"""
        high = _make_result(likes=100, comments_count=50)  # ratio = 0.5
        low = _make_result(likes=100, comments_count=10)   # ratio = 0.1
        assert self.ranker._engagement_score(high) > self.ranker._engagement_score(low)

    def test_zero_likes_no_division_error(self):
        """点赞为 0 时不应除零错误"""
        r = _make_result(likes=0, comments_count=5)
        score = self.ranker._engagement_score(r)
        assert score == 5.0  # 5 / max(0, 1) * 1.0 * 1.0

    def test_boost_keyword_increases_score(self):
        """标题包含加权关键词应提高分数"""
        normal = _make_result(title="普通文章", likes=100, comments_count=10)
        boosted = _make_result(title="面经分享", likes=100, comments_count=10)
        assert self.ranker._engagement_score(boosted) > self.ranker._engagement_score(normal)

    def test_boost_factor_is_1_3(self):
        """加权因子应为 1.3"""
        normal = _make_result(title="普通文章", likes=100, comments_count=10)
        boosted = _make_result(title="面经分享", likes=100, comments_count=10)
        ratio = self.ranker._engagement_score(boosted) / self.ranker._engagement_score(normal)
        assert abs(ratio - 1.3) < 0.001

    def test_ad_keyword_decreases_score(self):
        """标题包含广告关键词应降低分数"""
        normal = _make_result(title="普通文章", likes=100, comments_count=10)
        ad = _make_result(title="免费试听课程", likes=100, comments_count=10)
        assert self.ranker._engagement_score(ad) < self.ranker._engagement_score(normal)

    def test_ad_penalty_is_0_3(self):
        """广告降权因子应为 0.3"""
        normal = _make_result(title="普通文章", likes=100, comments_count=10)
        ad = _make_result(title="免费试听课程", likes=100, comments_count=10)
        ratio = self.ranker._engagement_score(ad) / self.ranker._engagement_score(normal)
        assert abs(ratio - 0.3) < 0.001


class TestRank:
    """测试 rank 方法"""

    def setup_method(self):
        self.ranker = EngagementRanker()

    def test_empty_input(self):
        """空输入返回空列表"""
        assert self.ranker.rank([]) == []

    def test_sorted_by_engagement(self):
        """结果按互动分降序排列"""
        results = [
            _make_result(title="低互动", likes=100, comments_count=1),
            _make_result(title="高互动", likes=100, comments_count=50),
            _make_result(title="中互动", likes=100, comments_count=20),
        ]
        ranked = self.ranker.rank(results)
        assert ranked[0].title == "高互动"
        assert ranked[1].title == "中互动"
        assert ranked[2].title == "低互动"

    def test_returns_all_when_less_than_20(self):
        """结果总数 < 20 时返回全部"""
        results = [_make_result(title=f"文章{i}") for i in range(15)]
        ranked = self.ranker.rank(results)
        assert len(ranked) == 15

    def test_truncates_to_top_n(self):
        """结果总数 >= 20 时截断到 top_n"""
        results = [_make_result(title=f"文章{i}", comments_count=i) for i in range(30)]
        ranked = self.ranker.rank(results, top_n=20)
        assert len(ranked) == 20

    def test_custom_top_n(self):
        """自定义 top_n 参数"""
        results = [_make_result(title=f"文章{i}", comments_count=i) for i in range(30)]
        ranked = self.ranker.rank(results, top_n=15)
        assert len(ranked) == 15

    def test_cross_platform_ranking(self):
        """跨平台结果统一排序"""
        results = [
            _make_result(title="小红书低", likes=100, comments_count=1, platform="xiaohongshu"),
            _make_result(title="Google高", likes=100, comments_count=50, platform="google"),
            _make_result(title="B站中", likes=100, comments_count=20, platform="bilibili"),
        ]
        ranked = self.ranker.rank(results)
        assert ranked[0].title == "Google高"
        assert ranked[0].platform == "google"

    def test_exactly_20_returns_all(self):
        """恰好 20 条时返回全部"""
        results = [_make_result(title=f"文章{i}") for i in range(20)]
        ranked = self.ranker.rank(results)
        assert len(ranked) == 20
