"""Tests for VisualAgent core generation methods (updated for new API).

Note: generate_detail_page and generate_visual_strategy were removed
in the 2026-06-16 refactor. Generation now flows through generate_all.
"""
import pytest


class TestVisualAgentAPI:
    """Verify VisualAgent exposes its current API surface."""

    def test_agent_has_core_methods(self):
        """VisualAgent should have its core generation methods."""
        from app.services.visual_agent import VisualAgent
        agent = VisualAgent()
        # Core generation methods (post-2026-06-16 refactor)
        assert hasattr(agent, "generate_main_image")
        assert hasattr(agent, "generate_all")
        assert hasattr(agent, "generate_selling_points")
        assert hasattr(agent, "generate_video_scripts")
        assert hasattr(agent, "generate_ad_material")
        assert hasattr(agent, "generate_white_bg")
        assert hasattr(agent, "generate_scene_images")

    def test_generate_all_accepts_project_id(self):
        """generate_all requires project_id, brief, and optional platform_id."""
        import inspect
        from app.services.visual_agent import VisualAgent
        sig = inspect.signature(VisualAgent.generate_all)
        params = list(sig.parameters.keys())
        assert "project_id" in params
        assert "brief" in params
