from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_upload_document_parse_uses_conservative_cleaning_without_telemetry():
    from main import app

    client = TestClient(app)
    raw_text = "\n".join(
        ["COMPANY PROFILE", "Page 1 of 20", "产品名称: ArcticPro 300L 商用冷柜"]
        + [f"品牌故事段落 {i}: 这是需要保留的品牌调性、色彩、字体和卖点上下文。" for i in range(90)]
        + ["规格参数: 300L, 220V", "Features: Fast cooling"]
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

    with patch("app.services.document_parser.parse_document", AsyncMock(return_value=raw_text)), patch(
        "app.services.brief_parser.parse_brief_text", parse_brief_mock
    ):
        response = client.post(
            "/api/v1/upload/document/parse",
            files={"file": ("product.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    sent_text = parse_brief_mock.await_args.args[0]
    assert 3000 < len(sent_text) <= 8000
    assert "品牌故事段落 60" in sent_text
    assert "text_prefilter_metrics" not in data
    assert data["extracted_text_length"] == len(sent_text)
