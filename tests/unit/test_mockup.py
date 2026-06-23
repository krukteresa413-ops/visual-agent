"""
TDD (RED): Mockup Agent tests.
Hermes writes tests → Claude generates implementation.
"""
import pytest


def test_mockup_types_available():
    """应返回至少3种 mockup 类型。"""
    from app.services.mockup_agent import MockupAgent, MOCKUP_TYPES

    assert len(MOCKUP_TYPES) >= 3
    type_names = {t["id"] for t in MOCKUP_TYPES}
    assert "package_box" in type_names
    assert "phone_screen" in type_names
    assert "store_sign" in type_names


def test_generate_mockup_prompt_includes_product():
    """生成的 prompt 应包含产品名。"""
    from app.services.mockup_agent import MockupAgent

    agent = MockupAgent()
    prompt = agent.build_prompt(
        mockup_type="package_box",
        product_name="智能手表",
        product_image_url="http://img/test.png",
    )
    assert "智能手表" in prompt
    assert "package" in prompt.lower()


def test_get_mockup_spec_returns_dimensions():
    """每种 mockup 类型应有正确的输出尺寸。"""
    from app.services.mockup_agent import MockupAgent

    agent = MockupAgent()
    spec = agent.get_spec("phone_screen")
    assert spec["width"] > 0
    assert spec["height"] > 0
    assert "description" in spec


def test_build_mockup_request_formats_correctly():
    """build_request 应返回符合 image_generation API 的格式。"""
    from app.services.mockup_agent import MockupAgent

    agent = MockupAgent()
    req = agent.build_request(
        mockup_type="phone_screen",
        product_name="蓝牙耳机",
        product_image_url="http://img/earbuds.png",
    )
    assert "prompt" in req
    assert "size" in req
    assert req["mockup_type"] == "phone_screen"


def test_agent_rejects_invalid_type():
    """无效 mockup 类型应抛出 ValueError。"""
    from app.services.mockup_agent import MockupAgent

    agent = MockupAgent()
    with pytest.raises(ValueError, match="Unknown mockup type"):
        agent.build_prompt(mockup_type="spaceship", product_name="x", product_image_url="y")
