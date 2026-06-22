"""
测试 Feedback Processor — 自然语言反馈修改。
PRD Step 5: 用户点选元素 → "标题再年轻一点" → 局部修改。
"""

import pytest


class TestFeedbackProcessor:
    """Test natural language feedback processing."""

    def test_parse_style_feedback(self):
        """Should parse style modification feedback."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="标题再年轻一点",
            asset_context={"type": "主图", "platform": "xiaohongshu"},
        )

        assert result is not None
        assert "action" in result
        assert result["action"] == "modify_style"
        assert "target" in result
        assert "年轻化" in result["target"]

    def test_parse_content_feedback(self):
        """Should parse content change feedback."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="背景换成夏日感",
            asset_context={"type": "主图", "platform": "taobao"},
        )

        assert result["action"] == "modify_background"
        assert "夏日" in result["target"]

    def test_parse_variant_request(self):
        """Should parse variant generation request."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="这个图生成同风格变体",
            asset_context={"type": "主图", "platform": "xiaohongshu"},
        )

        assert result["action"] == "generate_variant"
        assert result["count"] >= 1

    def test_parse_quality_feedback(self):
        """Should parse quality improvement feedback."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="主视觉更高级一些",
            asset_context={"type": "主图", "platform": "taobao"},
        )

        assert result["action"] == "enhance_quality"
        assert "高级" in result["target"]

    def test_parse_element_specific(self):
        """Should identify target element from feedback."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        # 标题相关
        r1 = processor.process(feedback="标题字号大一点", asset_context={})
        assert r1["element"] == "title"

        # 颜色相关
        r2 = processor.process(feedback="颜色太暗了", asset_context={})
        assert r2["element"] == "color"

        # 布局相关
        r3 = processor.process(feedback="排版调整一下", asset_context={})
        assert r3["element"] == "layout"

    def test_fallback_for_unknown_feedback(self):
        """Should provide sensible default for unrecognized feedback."""
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="asdfghjkl random text",
            asset_context={},
        )

        assert result is not None
        assert "action" in result
        # Should default to regenerate
        assert result["action"] == "regenerate"

    def test_output_is_serializable(self):
        """Feedback result should be JSON-serializable."""
        import json
        from app.services.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        result = processor.process(
            feedback="标题更年轻化",
            asset_context={"type": "主图"},
        )

        encoded = json.dumps(result, ensure_ascii=False)
        assert len(encoded) > 0
