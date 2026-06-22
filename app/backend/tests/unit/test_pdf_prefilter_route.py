from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_generate_from_document_uses_conservative_cleaning_before_llm_parse():
    from main import app

    client = TestClient(app)
    raw_text = "\n".join(
        ["COMPANY PROFILE", "Page 1 of 20", "产品名称: ArcticPro 300L 商用冷柜"]
        + [f"品牌故事段落 {i}: 这是需要保留的品牌调性、色彩、字体和卖点上下文。" for i in range(90)]
        + ["规格参数: 300L, 220V, stainless steel", "Features: Fast cooling for supermarkets"]
        + ["COMPANY PROFILE", "Page 2 of 20"] * 20
    )
    parsed = {
        "product_name": "ArcticPro 300L 商用冷柜",
        "category": "Commercial Refrigeration",
        "specifications": ["300L", "220V"],
        "selling_points": ["Fast cooling"],
        "target_market": [],
        "usage_scenarios": [],
        "target_customer": [],
        "materials": [],
        "compliance_notes": [],
    }

    parse_brief_mock = AsyncMock(return_value=parsed)
    with patch("app.api.unified_generation_routes.parse_document", AsyncMock(return_value=raw_text)), patch(
        "app.api.unified_generation_routes.parse_brief_text", parse_brief_mock
    ), patch(
        "app.api.unified_generation_routes.ComplianceChecker.check_brief", return_value=[]
    ), patch(
        "app.api.unified_generation_routes.BriefReviewer.generate_questions", return_value=[]
    ):
        response = client.post(
            "/api/v1/generate-from-document",
            files={"file": ("product.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"strategy_first": "true", "skip_review": "true"},
        )

    assert response.status_code == 200
    sent_text = parse_brief_mock.await_args.args[0]
    assert 3000 < len(sent_text) <= 8000
    assert "品牌故事段落 60" in sent_text
    assert "Fast cooling" in sent_text
    assert sent_text.count("COMPANY PROFILE") < 3
    assert "text_prefilter_metrics" not in response.json()
