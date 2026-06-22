"""BriefReviewer 追问服务测试 — TDD RED 阶段"""
import pytest
from unittest.mock import AsyncMock, patch


class TestBriefReviewer:
    """测试追问生成的规则层（不依赖 LLM）。"""

    def test_detect_missing_required_generates_questions(self):
        """required 字段缺失时应生成追问。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": None,
            "category": None,
            "specifications": [],
            "selling_points": ["fast cooling"],
            "target_market": ["US"],
        }
        questions = BriefReviewer.generate_questions(parsed)
        assert len(questions) >= 2  # product_name + category 缺失
        fields = [q["field"] for q in questions]
        assert "product_name" in fields
        assert "category" in fields

    def test_detect_missing_recommended(self):
        """recommended 字段缺失也应生成追问（但优先 required）。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": "Freezer",
            "category": "Refrigeration",
            "specifications": ["300L"],
            "selling_points": ["fast cooling"],
            "target_market": None,
            "usage_scenarios": None,
            "target_customer": None,
        }
        questions = BriefReviewer.generate_questions(parsed)
        assert len(questions) >= 1
        # recommended 缺失应该被检测
        fields = [q["field"] for q in questions]
        assert any(f in fields for f in ["target_market", "usage_scenarios", "target_customer"])

    def test_complete_brief_no_questions(self):
        """完整 brief 不生成任何追问。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": "Freezer",
            "category": "Refrigeration",
            "specifications": ["300L", "stainless steel"],
            "selling_points": ["fast cooling", "energy saving"],
            "target_market": ["US"],
            "usage_scenarios": ["supermarket"],
            "target_customer": ["distributor"],
        }
        questions = BriefReviewer.generate_questions(parsed)
        assert questions == []

    def test_max_five_questions(self):
        """最多 5 个问题。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": None,
            "category": None,
            "specifications": [],
            "selling_points": [],
            "target_market": None,
            "usage_scenarios": None,
            "target_customer": None,
            "materials": None,
        }
        questions = BriefReviewer.generate_questions(parsed)
        assert len(questions) <= 5

    def test_required_priority_over_recommended(self):
        """required 缺失排在 recommended 前面。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": None,
            "category": "Refrigeration",
            "specifications": ["300L"],
            "selling_points": [],
            "target_market": None,
        }
        questions = BriefReviewer.generate_questions(parsed)
        # product_name(required) + selling_points(required) + target_market(recommended)
        assert len(questions) >= 2
        # 前两个应该是 required
        assert questions[0]["level"] == "required"
        assert questions[1]["level"] == "required"

    def test_question_structure(self):
        """每个问题包含 field / level / question / hint。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": None,
            "category": None,
            "specifications": [],
            "selling_points": [],
        }
        questions = BriefReviewer.generate_questions(parsed)
        for q in questions:
            assert "field" in q
            assert "level" in q
            assert "question" in q
            assert "hint" in q
            assert q["level"] in ("required", "recommended")

    def test_question_is_chinese(self):
        """追问语言为中文。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": None,
            "category": "Refrigeration",
            "specifications": ["300L"],
            "selling_points": [],
        }
        questions = BriefReviewer.generate_questions(parsed)
        for q in questions:
            # 至少包含中文字符
            assert any('\u4e00' <= c <= '\u9fff' for c in q["question"])


class TestBriefReviewerLLM:
    """测试 LLM 增强追问（mock LLM）。"""

    @pytest.mark.asyncio
    async def test_review_with_llm(self):
        """LLM 追问应返回自然语言问题。"""
        from app.services.brief_reviewer import BriefReviewer

        parsed = {
            "product_name": "Cooler",
            "category": None,
            "specifications": [],
            "selling_points": [],
        }
        mock_llm = AsyncMock()
        mock_llm.call.return_value = {
            "questions": [
                {"field": "category", "question": "请问这款Cooler属于什么品类？比如商用冷柜、家用冰箱？"},
                {"field": "specifications", "question": "能告诉我Cooler的主要规格参数吗？容量、材质等？"},
            ]
        }
        questions = await BriefReviewer.review(parsed, llm=mock_llm)
        assert len(questions) == 2
        assert questions[0]["field"] == "category"
        assert "Cooler" in questions[0]["question"]
