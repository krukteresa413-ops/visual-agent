import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_generate_from_document_review_branch_does_not_require_quality_report(client):
    parsed_brief = {
        "category": "鞋服",
        "selling_points": [],
        "specifications": [],
        "target_market": [],
        "usage_scenarios": [],
    }

    required_question = {
        "field": "product_name",
        "question": "产品名称是什么？",
        "level": "required",
    }

    with patch(
        "app.api.unified_generation_routes.BriefReviewer.generate_questions",
        return_value=[required_question],
    ), patch(
        "app.api.unified_generation_routes.ComplianceChecker.check_brief",
        return_value=[],
    ):
        response = client.post(
            "/api/v1/generate-from-document",
            data={"parsed_brief_json": json.dumps(parsed_brief), "skip_review": "false"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["needs_review"] is True
    assert data["questions"] == [required_question]
    assert data["quality_report"] is None
    assert data["generation"] is None
