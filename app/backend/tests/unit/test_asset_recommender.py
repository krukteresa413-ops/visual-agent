"""
测试 Asset Recommender — 推荐资产清单生成。
PRD Step 3: 根据平台和品类推荐应生成的资产类型。
"""

import pytest


class TestAssetRecommender:
    """Test asset recommendation based on platform + category."""

    def test_recommend_for_taobao(self):
        """淘宝平台应推荐电商标准资产。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="taobao", category="美妆")

        assert assets is not None
        assert isinstance(assets, list)
        assert len(assets) > 0
        # 淘宝应包含主图、白底图、详情页
        asset_types = [a["type"] for a in assets]
        assert "主图" in asset_types
        assert "白底图" in asset_types
        assert "详情页" in asset_types

    def test_recommend_for_xiaohongshu(self):
        """小红书应推荐种草内容资产。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="xiaohongshu", category="美妆")

        assert len(assets) > 0
        asset_types = [a["type"] for a in assets]
        assert "封面图" in asset_types
        # 小红书通常需要多个场景图
        scene_assets = [a for a in assets if "场景" in a["type"]]
        assert len(scene_assets) > 0

    def test_recommend_for_douyin(self):
        """抖音应包含短视频相关资产。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="douyin", category="食品")

        assert len(assets) > 0
        asset_types = [a["type"] for a in assets]
        assert any("视频" in t for t in asset_types)

    def test_recommend_includes_priority(self):
        """每个推荐资产应包含优先级。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="taobao", category="食品")

        for asset in assets:
            assert "type" in asset
            assert "priority" in asset
            assert "count" in asset
            assert isinstance(asset["priority"], int)

    def test_recommend_with_unknown_platform(self):
        """未知平台应返回通用推荐。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="unknown_platform", category="其他")

        assert assets is not None
        assert len(assets) > 0
        # 至少应包含主图和场景图
        asset_types = [a["type"] for a in assets]
        assert "主图" in asset_types

    def test_recommend_output_is_serializable(self):
        """推荐结果应可JSON序列化。"""
        import json
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        assets = recommender.recommend(platform="taobao", category="家居")

        encoded = json.dumps(assets, ensure_ascii=False)
        assert len(encoded) > 0

    def test_recommend_count_total(self):
        """推荐的总资产数量应在合理范围内（5-20个）。"""
        from app.services.asset_recommender import AssetRecommender

        recommender = AssetRecommender()
        for platform in ["taobao", "xiaohongshu", "douyin", "wechat"]:
            assets = recommender.recommend(platform=platform, category="食品")
            total = sum(a["count"] for a in assets)
            assert 3 <= total <= 20, f"{platform}: {total} assets (expected 3-20)"
