"""Quick Generate — skip questions, generate first draft immediately."""
from typing import Dict, List
from app.services.creative_strategy import CreativeStrategyAgent
from app.services.asset_recommender import AssetRecommender
from app.services.brief_reviewer import BriefReviewer


REQUIRED_FIELDS = ["product_name", "category", "specifications", "selling_points"]


class QuickGenerateService:
    """Generate first draft without requiring complete brief."""

    def generate(
        self,
        brief: dict,
        platform: str,
        skip_questions: bool = False,
    ) -> Dict:
        """Generate assets from brief, skipping questions if requested."""
        warnings = []

        # Check for missing fields
        for field in REQUIRED_FIELDS:
            value = brief.get(field)
            if BriefReviewer._is_missing(value):
                field_names = {
                    "product_name": "产品名称",
                    "category": "品类",
                    "specifications": "规格参数",
                    "selling_points": "核心卖点",
                }
                warnings.append(f"缺失信息：{field_names.get(field, field)}，已使用默认值")

        # Fill missing with defaults
        filled = dict(brief)
        if not filled.get("category"):
            filled["category"] = "通用"
        if not filled.get("specifications"):
            filled["specifications"] = ["标准规格"]
        if not filled.get("selling_points"):
            filled["selling_points"] = ["品质优良"]

        # Generate strategy
        strategy_agent = CreativeStrategyAgent()
        strategy = strategy_agent.generate_strategy(
            brief=filled,
            platform=platform,
        )

        # Recommend assets
        recommender = AssetRecommender()
        assets = recommender.recommend(
            platform=platform,
            category=filled.get("category", "通用"),
        )

        return {
            "strategy": strategy,
            "assets": assets,
            "warnings": warnings,
            "skip_questions": skip_questions,
        }
