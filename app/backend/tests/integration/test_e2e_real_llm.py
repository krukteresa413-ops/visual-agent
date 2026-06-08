"""
端到端测试：调用真实 LLM API。
标记为 slow，不在 CI 中自动运行。
手动运行：pytest tests/integration/test_e2e_real_llm.py -v -m slow
"""
import pytest

FREEZER_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel", "low noise"],
    "materials": ["stainless steel"],
    "selling_points": ["fast cooling", "energy saving", "OEM customization"],
    "target_market": ["US", "EU"],
    "target_customer": ["supermarket buyer", "restaurant owner"],
    "usage_scenarios": ["supermarket", "restaurant", "convenience store"],
    "brand_style": "clean, professional, industrial",
    "compliance_notes": ["avoid unverifiable certification claims"],
}


@pytest.mark.slow
@pytest.mark.asyncio
async def test_real_main_image_generation():
    """
    用真实 DeepSeek API 生成主图方案。
    验收标准（PRD 8.3）：
    1. 返回有效的 MainImagePlan
    2. Prompt 包含主体、角度、背景、风格
    3. 引用了产品资料（不是泛泛模板）
    """
    from app.services.visual_agent import VisualAgent

    agent = VisualAgent()
    result = await agent.generate_main_image(FREEZER_BRIEF)

    # 结构验证
    assert result.asset_type == "main_image"
    assert len(result.goal) > 10
    assert len(result.prompt) > 30

    # 内容验证：prompt 是否引用了产品资料
    prompt_lower = result.prompt.lower()
    assert any(kw in prompt_lower for kw in ["freezer", "chest", "commercial"]), \
        f"Prompt未引用产品信息: {result.prompt}"

    print(f"\n✅ 主图方案生成成功")
    print(f"  目标: {result.goal}")
    print(f"  构图: {result.composition}")
    print(f"  Prompt: {result.prompt[:100]}...")
