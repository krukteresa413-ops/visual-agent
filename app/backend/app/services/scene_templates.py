"""Scene Template Service — pre-built scene templates for quick project start."""
from typing import List, Dict, Optional


TEMPLATES = [
    {
        "id": "ecommerce_launch",
        "name": "电商上新",
        "description": "淘宝/天猫新品上架，含主图、详情页、白底图",
        "platforms": ["taobao"],
        "category": "通用",
        "default_assets": ["主图", "白底图", "详情页", "视频主图"],
        "default_brief": {
            "category": "通用",
            "platform": "taobao",
        },
    },
    {
        "id": "social_种草",
        "name": "小红书种草",
        "description": "小红书种草笔记，含封面图、场景图、细节图",
        "platforms": ["xiaohongshu"],
        "category": "通用",
        "default_assets": ["封面图", "场景图", "细节图", "前后对比图"],
        "default_brief": {
            "category": "通用",
            "platform": "xiaohongshu",
        },
    },
    {
        "id": "restaurant_promo",
        "name": "餐饮活动",
        "description": "餐饮推广活动，含海报、菜单图、环境图",
        "platforms": ["wechat", "xiaohongshu"],
        "category": "食品",
        "default_assets": ["主图", "场景图", "海报", "菜单图"],
        "default_brief": {
            "category": "食品",
            "platform": "wechat",
        },
    },
    {
        "id": "brand_system",
        "name": "品牌视觉系统",
        "description": "完整品牌视觉体系，含Logo、色板、字体、VI应用",
        "platforms": ["taobao", "xiaohongshu", "douyin"],
        "category": "通用",
        "default_assets": ["Logo", "色板", "字体", "主图", "封面图", "短视频"],
        "default_brief": {
            "category": "通用",
            "platform": "taobao",
        },
    },
    {
        "id": "short_video_campaign",
        "name": "短视频营销",
        "description": "抖音短视频推广，含口播脚本、封面、切片",
        "platforms": ["douyin"],
        "category": "通用",
        "default_assets": ["短视频", "封面图", "直播切片"],
        "default_brief": {
            "category": "通用",
            "platform": "douyin",
        },
    },
    {
        "id": "amazon_listing",
        "name": "亚马逊上架",
        "description": "亚马逊产品上架，含A+ Content、Lifestyle、Infographic",
        "platforms": ["amazon"],
        "category": "通用",
        "default_assets": ["主图", "A+ Content", "Lifestyle", "Infographic"],
        "default_brief": {
            "category": "通用",
            "platform": "amazon",
        },
    },
]


class SceneTemplateService:
    """Service for listing and applying scene templates."""

    def list_templates(self) -> List[Dict]:
        """List all available scene templates."""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "platforms": t["platforms"],
                "default_assets": t["default_assets"],
            }
            for t in TEMPLATES
        ]

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID."""
        for t in TEMPLATES:
            if t["id"] == template_id:
                return dict(t)
        return None

    def apply_template(self, template_id: str, user_input: Dict) -> Dict:
        """Merge template defaults with user input. User values take precedence."""
        template = self.get_template(template_id)
        if not template:
            return dict(user_input)

        merged = dict(template["default_brief"])
        merged.update(user_input)
        # Ensure these aren't lost
        if "category" not in merged:
            merged["category"] = template["category"]
        if "platform" not in merged:
            merged["platform"] = template["platforms"][0] if template["platforms"] else ""
        return merged
