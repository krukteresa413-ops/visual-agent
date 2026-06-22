"""
文案 Agent 测试。
验证：6类文案生成 + 合规检查。
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

SAMPLE_BRIEF = {
    "product_name": "轻呼吸防晒衣",
    "category": "女装/防晒服饰",
    "specifications": ["UPF50+", "轻薄透气", "均码90-140斤"],
    "selling_points": ["防晒UPF50+", "冰感面料", "通勤户外两穿"],
    "target_market": ["中国"],
    "target_customer": ["25-35岁职场女性"],
    "usage_scenarios": ["通勤", "户外", "逛街"],
    "brand_style": "清爽高级，不网红",
}

MOCK_COPY_RESULT = {
    "headline": "一件防晒衣，通勤户外都自在",
    "body": "UPF50+高倍防晒，冰感面料全天清爽。均码设计包容90-140斤身材，不挑人。",
    "cta": "点击查看详情",
}


class TestCopywritingEndpoint:
    """文案生成端点"""

    def test_generate_ecommerce_copy(self):
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_COPY_RESULT

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/copywriting/generate", json={
                "brief": SAMPLE_BRIEF,
                "copy_types": ["ecommerce_selling_point"],
            })

            assert resp.status_code == 200
            data = resp.json()
            assert "ecommerce_selling_point" in data
            assert "UPF50" in data["ecommerce_selling_point"]["body"]

    def test_generate_multiple_types(self):
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_COPY_RESULT

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/copywriting/generate", json={
                "brief": SAMPLE_BRIEF,
                "copy_types": ["xiaohongshu_title", "douyin_voiceover"],
            })

            assert resp.status_code == 200
            data = resp.json()
            assert "xiaohongshu_title" in data
            assert "douyin_voiceover" in data

    def test_all_six_types(self):
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_COPY_RESULT

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/copywriting/generate", json={
                "brief": SAMPLE_BRIEF,
                "copy_types": ["all"],
            })

            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 6

    def test_compliance_check_included(self):
        """文案返回包含合规检查"""
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "headline": "最好的防晒衣",
                "body": "全世界第一的防晒效果",
                "cta": "立即购买",
            }

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/copywriting/generate", json={
                "brief": SAMPLE_BRIEF,
                "copy_types": ["ecommerce_selling_point"],
            })

            data = resp.json()
            copy_data = data["ecommerce_selling_point"]
            # 合规检查结果
            assert "compliance" in copy_data
            # 应该检出极限词
            warnings = copy_data["compliance"]
            assert len(warnings) > 0
