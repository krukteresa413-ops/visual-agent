"""Tests for P4.1: Campaign Agent — autonomous 6-step pipeline.

TDD: RED phase.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCampaignAgent:
    """Test the campaign orchestration agent."""

    def test_campaign_agent_model_exists(self):
        """CampaignBrief should be importable."""
        from app.models.campaign_models import CampaignBrief, CampaignResult
        brief = CampaignBrief(
            project_name="Spring Campaign 2025",
            description="春季户外运动品牌 campaign",
            target_audience="25-35岁城市户外爱好者",
            key_message="唤醒野性",
            platforms=["taobao", "douyin", "xiaohongshu"],
        )
        assert brief.project_name == "Spring Campaign 2025"
        assert len(brief.platforms) == 3

    def test_campaign_result_model(self):
        """CampaignResult should hold pipeline output."""
        from app.models.campaign_models import CampaignResult, CampaignStep
        steps = [
            CampaignStep(step="creative_brief", status="completed", output={"parsed": True}),
            CampaignStep(step="mood_direction", status="completed", output={"style": "minimal"}),
            CampaignStep(step="concept_generation", status="in_progress", output={}),
        ]
        result = CampaignResult(
            project_id=1,
            steps=steps,
            status="in_progress",
        )
        assert len(result.steps) == 3
        assert result.status == "in_progress"
        assert result.steps[0].status == "completed"

    def test_campaign_step_model(self):
        """Each step should have progress tracking."""
        from app.models.campaign_models import CampaignStep
        step = CampaignStep(
            step="concept_generation",
            status="pending",
            progress=0,
            output={},
        )
        assert step.progress == 0
        assert step.status == "pending"


class TestCampaignOrchestrator:
    """Test the campaign orchestrator that runs the 6-step pipeline."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        return {
            "brief_parser": AsyncMock(return_value={"parsed_brief": {"title": "test"}}),
            "mood_agent": AsyncMock(return_value={"style": "minimal", "palette": ["#000"]}),
            "concept_agent": AsyncMock(return_value={"images": ["url1", "url2"]}),
            "refine_agent": AsyncMock(return_value={"approved": True}),
            "adapt_agent": AsyncMock(return_value={"formats": ["taobao", "douyin"]}),
            "export_agent": AsyncMock(return_value={"package_url": "/exports/test.zip"}),
        }

    @pytest.mark.asyncio
    async def test_campaign_pipeline_runs_all_6_steps(self, mock_dependencies):
        """Campaign orchestrator should execute all 6 pipeline steps."""
        from app.services.campaign_orchestrator import CampaignOrchestrator
        from app.models.campaign_models import CampaignBrief

        brief = CampaignBrief(
            project_name="Test Campaign",
            description="test",
            target_audience="all",
            key_message="test",
            platforms=["taobao"],
        )

        orchestrator = CampaignOrchestrator(
            brief_parser=mock_dependencies["brief_parser"],
            mood_agent=mock_dependencies["mood_agent"],
            concept_agent=mock_dependencies["concept_agent"],
            refine_agent=mock_dependencies["refine_agent"],
            adapt_agent=mock_dependencies["adapt_agent"],
            export_agent=mock_dependencies["export_agent"],
        )

        result = await orchestrator.run(brief, project_id=1)

        assert result.status == "completed"
        assert len(result.steps) == 6
        assert all(s.status == "completed" for s in result.steps)
        assert mock_dependencies["brief_parser"].called
        assert mock_dependencies["export_agent"].called

    @pytest.mark.asyncio
    async def test_campaign_stops_on_critical_failure(self, mock_dependencies):
        """Pipeline should stop at the failing step and report partial results."""
        from app.services.campaign_orchestrator import CampaignOrchestrator
        from app.models.campaign_models import CampaignBrief

        # concept_agent fails
        mock_dependencies["concept_agent"].side_effect = RuntimeError("Generation failed")

        brief = CampaignBrief(
            project_name="Test",
            description="test",
            target_audience="all",
            key_message="test",
            platforms=["taobao"],
        )

        orchestrator = CampaignOrchestrator(
            brief_parser=mock_dependencies["brief_parser"],
            mood_agent=mock_dependencies["mood_agent"],
            concept_agent=mock_dependencies["concept_agent"],
            refine_agent=mock_dependencies["refine_agent"],
            adapt_agent=mock_dependencies["adapt_agent"],
            export_agent=mock_dependencies["export_agent"],
        )

        result = await orchestrator.run(brief, project_id=1)

        assert result.status == "failed"
        # First 2 steps should complete, concept should be failed, rest untouched
        assert result.steps[0].status == "completed"
        assert result.steps[1].status == "completed"
        assert result.steps[2].status == "failed"

    @pytest.mark.asyncio
    async def test_campaign_emits_progress_events(self, mock_dependencies):
        """Orchestrator should emit progress updates after each step."""
        from app.services.campaign_orchestrator import CampaignOrchestrator
        from app.models.campaign_models import CampaignBrief

        progress_events = []
        async def progress_callback(step_name, percent, status):
            progress_events.append({"step": step_name, "percent": percent, "status": status})

        brief = CampaignBrief(
            project_name="Test",
            description="test",
            target_audience="all",
            key_message="test",
            platforms=["taobao"],
        )

        orchestrator = CampaignOrchestrator(
            brief_parser=mock_dependencies["brief_parser"],
            mood_agent=mock_dependencies["mood_agent"],
            concept_agent=mock_dependencies["concept_agent"],
            refine_agent=mock_dependencies["refine_agent"],
            adapt_agent=mock_dependencies["adapt_agent"],
            export_agent=mock_dependencies["export_agent"],
            on_progress=progress_callback,
        )

        await orchestrator.run(brief, project_id=1)
        assert len(progress_events) == 7  # 6 steps + final "完成"
        assert progress_events[-1]["percent"] == 100
        assert progress_events[-1]["status"] == "completed"
