"""
测试 Feedback Loop — 生成→预览→反馈→再生成 闭环。
PRD Step 5: 迭代循环支持。
"""

import pytest


class TestFeedbackLoop:
    """Test the full feedback iteration loop."""

    def test_process_feedback_and_regenerate(self):
        """Should process feedback and return regeneration parameters."""
        from app.services.feedback_loop import FeedbackLoop

        loop = FeedbackLoop()
        result = loop.iterate(
            asset={"id": "1", "type": "主图", "url": "/old.jpg"},
            feedback="标题再年轻一点",
        )

        assert result is not None
        assert "action" in result
        assert "previous_asset" in result
        assert "new_prompt_hint" in result

    def test_loop_preserves_history(self):
        """Should track iteration history."""
        from app.services.feedback_loop import FeedbackLoop

        loop = FeedbackLoop()
        asset = {"id": "1", "type": "主图", "url": "/v1.jpg"}

        r1 = loop.iterate(asset=asset, feedback="颜色亮一点", iteration=1)
        r2 = loop.iterate(asset=asset, feedback="加logo", iteration=2,
                          previous_result=r1)

        assert r2["iteration"] == 2
        assert len(r2["history"]) == 2  # tracks both iterations

    def test_max_iterations(self):
        """Should return warning when max iterations reached."""
        from app.services.feedback_loop import FeedbackLoop

        loop = FeedbackLoop(max_iterations=3)
        result = loop.iterate(
            asset={"id": "1", "type": "主图"},
            feedback="再改改",
            iteration=4,
        )

        assert result["action"] == "stop"
        assert "最大" in result["new_prompt_hint"]

    def test_result_is_serializable(self):
        """Result should be JSON-serializable."""
        import json
        from app.services.feedback_loop import FeedbackLoop

        loop = FeedbackLoop()
        result = loop.iterate(
            asset={"id": "1", "type": "主图"},
            feedback="背景换成夏日感",
        )

        encoded = json.dumps(result, ensure_ascii=False)
        assert len(encoded) > 0
