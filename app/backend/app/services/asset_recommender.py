"""Asset Recommender — recommends asset types based on platform and category."""
from typing import List, Dict


# Platform-specific asset templates
PLATFORM_ASSETS = {
    "taobao": [
        {"type": "主图", "priority": 1, "count": 5, "note": "800x800, 白底+场景"},
        {"type": "白底图", "priority": 2, "count": 3, "note": "纯白背景产品图"},
        {"type": "详情页", "priority": 3, "count": 1, "note": "750宽, 含卖点+参数+场景"},
        {"type": "视频主图", "priority": 4, "count": 1, "note": "9-60秒, 16:9"},
        {"type": "sku图", "priority": 5, "count": 4, "note": "不同颜色/规格"},
    ],
    "xiaohongshu": [
        {"type": "封面图", "priority": 1, "count": 3, "note": "3:4竖版, 高颜值种草风"},
        {"type": "场景图", "priority": 2, "count": 4, "note": "生活方式场景, 自然光"},
        {"type": "细节图", "priority": 3, "count": 3, "note": "产品细节特写"},
        {"type": "前后对比图", "priority": 4, "count": 2, "note": "使用前后效果对比"},
        {"type": "合集图", "priority": 5, "count": 1, "note": "多产品组合推荐"},
    ],
    "douyin": [
        {"type": "短视频", "priority": 1, "count": 3, "note": "15-60秒, 9:16竖版"},
        {"type": "封面图", "priority": 2, "count": 3, "note": "抓眼球, 大字标题"},
        {"type": "直播切片", "priority": 3, "count": 2, "note": "产品讲解高光片段"},
        {"type": "挑战赛素材", "priority": 4, "count": 2, "note": "品牌挑战赛模板"},
    ],
    "wechat": [
        {"type": "朋友圈广告图", "priority": 1, "count": 3, "note": "800x800或800x450"},
        {"type": "公众号封面", "priority": 2, "count": 2, "note": "900x383, 2.35:1"},
        {"type": "社群分享图", "priority": 3, "count": 4, "note": "适合微信转发"},
    ],
}


# Category-specific additions
CATEGORY_EXTRAS = {
    "美妆": [{"type": "成分图", "priority": 5, "count": 2, "note": "核心成分/功效可视化"}],
    "食品": [{"type": "包装图", "priority": 3, "count": 2, "note": "产品包装展示"}],
    "女装": [{"type": "模特图", "priority": 2, "count": 3, "note": "真实上身效果"}],
    "3C数码": [{"type": "功能对比图", "priority": 4, "count": 2, "note": "参数功能对比"}],
    "家居": [{"type": "空间效果图", "priority": 2, "count": 3, "note": "家居空间整体效果"}],
}


class AssetRecommender:
    """Recommend asset types for a given platform and category."""

    def recommend(self, platform: str, category: str) -> List[Dict]:
        """Return list of recommended assets with type, priority, count."""
        # Get platform base assets
        assets = PLATFORM_ASSETS.get(platform, [
            {"type": "主图", "priority": 1, "count": 3, "note": "产品主视觉"},
            {"type": "场景图", "priority": 2, "count": 2, "note": "使用场景展示"},
            {"type": "详情图", "priority": 3, "count": 1, "note": "产品详情说明"},
        ])

        # Add category-specific extras
        extras = CATEGORY_EXTRAS.get(category, [])
        assets = assets + extras

        # Deduplicate by type name
        seen = set()
        result = []
        for a in assets:
            if a["type"] not in seen:
                seen.add(a["type"])
                result.append(a)

        # Sort by priority
        result.sort(key=lambda x: x["priority"])
        return result
