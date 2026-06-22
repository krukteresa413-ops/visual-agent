"""
品牌套件提取 API 测试 — TDD RED phase。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestBrandExtractAPI:
    """POST /api/v1/brand/extract — 从文本中提取品牌元素。"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    @pytest.fixture
    def mock_llm(self):
        """模拟 LLM 返回品牌 JSON dict。"""
        return AsyncMock(return_value={
            "brand_name": "小米",
            "tagline": "为发烧而生",
            "primary_color": "#FF6900",
            "secondary_color": "#000000",
            "accent_color": "#FFFFFF",
            "font_headings": "MiSans Bold",
            "font_body": "MiSans Regular",
            "tone_of_voice": "科技简约、年轻活力",
            "visual_style": "极简科技风",
            "iconography": "线性图标",
            "brand_story": "让每个人都能享受科技的乐趣",
        })

    def test_extract_from_text_returns_brand_kit(self, client, mock_llm):
        """提交文本 → 返回完整品牌元素。"""
        with patch(
            "app.api.brand_routes.LLMClient.call",
            mock_llm,
        ):
            resp = client.post("/api/v1/brand/extract", data={
                "text": "小米科技公司，主打智能硬件，品牌色为橙色",
                "project_id": 1,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["brand_name"] == "小米"
        assert data["primary_color"] == "#FF6900"
        assert data["secondary_color"] == "#000000"
        assert data["tagline"] == "为发烧而生"
        assert data["font_headings"] == "MiSans Bold"
        assert data["tone_of_voice"] == "科技简约、年轻活力"
        assert data["visual_style"] == "极简科技风"


    def test_extract_from_pdf_uses_document_parser_and_preserves_brand_content(self, client):
        """PDF 文件必须走 document_parser，而不是把 PDF bytes 当 UTF-8 文本硬解码。"""
        parsed_text = (
            "品牌名称: ArcticPro\n"
            "品牌色: #0B1F3A / #FF6900\n"
            "字体: Inter Bold / Inter Regular\n"
            "品牌调性: 专业、可靠、节能\n"
            "品牌故事: 面向商超冷链场景的高效制冷品牌。"
        )
        brand_result = {
            "brand_name": "ArcticPro",
            "tagline": "高效冷链，可靠守护",
            "primary_color": "#0B1F3A",
            "secondary_color": "#FF6900",
            "accent_color": "#FFFFFF",
            "font_headings": "Inter Bold",
            "font_body": "Inter Regular",
            "tone_of_voice": "专业、可靠、节能",
            "visual_style": "现代工业科技",
            "iconography": "线性图标",
            "brand_story": "面向商超冷链场景的高效制冷品牌。",
        }
        parse_document_mock = AsyncMock(return_value=parsed_text)
        llm_mock = AsyncMock(return_value=brand_result)

        with patch("app.services.document_parser.parse_document", parse_document_mock), patch(
            "app.api.brand_routes.LLMClient.call", llm_mock
        ):
            resp = client.post(
                "/api/v1/brand/extract",
                data={"project_id": 0},
                files={"file": ("brand.pdf", b"%PDF-1.4\xff\x00fake", "application/pdf")},
            )

        assert resp.status_code == 200
        parse_document_mock.assert_awaited_once()
        user_prompt = llm_mock.await_args.kwargs["user_prompt"]
        assert parsed_text in user_prompt
        assert "%PDF" not in user_prompt
        data = resp.json()
        assert data["brand_name"] == "ArcticPro"
        assert data["primary_color"] == "#0B1F3A"

    def test_extract_empty_text_returns_400(self, client):
        """空文本 → 400。"""
        resp = client.post("/api/v1/brand/extract", data={
            "text": "",
            "project_id": 1,
        })
        assert resp.status_code == 400

    def test_extract_no_text_or_file_returns_400(self, client):
        """既没 text 也没 file → 400。"""
        resp = client.post("/api/v1/brand/extract", data={
            "project_id": 1,
        })
        assert resp.status_code == 400

    def test_extract_llm_returns_incomplete_json(self, client):
        """LLM 返回不完整的 JSON → 部分字段默认值。"""
        partial_mock = AsyncMock(return_value={"brand_name": "TestOnly"})
        with patch(
            "app.api.brand_routes.LLMClient.call",
            partial_mock,
        ):
            resp = client.post("/api/v1/brand/extract", data={
                "text": "测试品牌",
                "project_id": 1,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["brand_name"] == "TestOnly"
        # 未返回的字段应有默认值
        assert data.get("primary_color") is None or data["primary_color"] == ""
        assert data.get("tagline") is None or data["tagline"] == ""


class TestBrandKitSchema:
    """BrandKit Pydantic schema 验证。"""

    def test_schema_all_fields(self):
        from app.schemas.brand_kit import BrandKitOut
        kit = BrandKitOut(
            brand_name="Nike",
            tagline="Just Do It",
            primary_color="#000000",
            secondary_color="#FFFFFF",
            accent_color="#FF0000",
            font_headings="Futura Bold",
            font_body="Helvetica",
            tone_of_voice="激励人心、运动精神",
            visual_style="动感、现代",
            iconography="粗线条图标",
            brand_story="始于1972年的运动品牌传奇",
        )
        assert kit.brand_name == "Nike"
        assert kit.tagline == "Just Do It"
        assert kit.primary_color == "#000000"

    def test_schema_minimal(self):
        from app.schemas.brand_kit import BrandKitOut
        kit = BrandKitOut(brand_name="Min")
        assert kit.brand_name == "Min"
        assert kit.primary_color is None


class TestBrandKitCacheAPI:
    """GET /api/v1/brand/{project_id} — 读取缓存的品牌套件。"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_get_nonexistent_returns_none(self, client):
        """不存在的项目 → brand_kit is None。"""
        resp = client.get("/api/v1/brand/99999")
        assert resp.status_code == 200
        assert resp.json()["brand_kit"] is None

    def test_get_existing_structure(self, client):
        """端点结构正确 — 返回 brand_kit 键。"""
        resp = client.get("/api/v1/brand/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "brand_kit" in data
