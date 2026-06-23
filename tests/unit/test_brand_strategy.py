"""
TDD (RED): Brand Strategy Agent tests.
claude-coder Kanban worker will implement to make these pass.
"""
import pytest


def test_extract_positioning_from_brief():
    """从 brief 提取品牌定位。"""
    from app.services.brand_strategy import BrandStrategyAgent

    agent = BrandStrategyAgent()
    result = agent.analyze({
        "product_name": "有机绿茶",
        "category": "茶饮",
        "target_market": ["US", "EU"],
        "target_customer": ["health-conscious millennials"],
        "brand_style": "natural, premium",
    })
    assert "positioning" in result
    assert "target_persona" in result
    assert result["category"] == "茶饮"


def test_strategy_includes_differentiators():
    """策略应包含差异化卖点。"""
    from app.services.brand_strategy import BrandStrategyAgent

    agent = BrandStrategyAgent()
    result = agent.analyze({
        "product_name": "智能手表",
        "category": "3C数码",
        "brand_style": "minimal, tech",
    })
    assert len(result["differentiators"]) >= 1
    assert isinstance(result["differentiators"], list)


def test_strategy_outputs_price_tier():
    """策略应推断价格区间。"""
    from app.services.brand_strategy import BrandStrategyAgent

    agent = BrandStrategyAgent()
    result = agent.analyze({
        "product_name": "奢侈手袋",
        "category": "珠宝配饰",
        "brand_style": "luxury, exclusive",
    })
    assert "price_tier" in result
    assert result["price_tier"] in ("budget", "mid", "premium", "luxury")


def test_empty_brief_returns_defaults():
    """空 brief 返回合理的默认值。"""
    from app.services.brand_strategy import BrandStrategyAgent

    agent = BrandStrategyAgent()
    result = agent.analyze({})
    assert "positioning" in result
    assert len(result["differentiators"]) >= 0
