"""Campaign Orchestrator — autonomous 6-step creative pipeline (P4.1).

User submits a brief → Agent autonomously runs:
  1. Creative Brief → parse & validate
  2. Mood & Direction → style/visual direction
  3. Concept Generation → main image + variants
  4. Refinement → review & approve
  5. Adapt & Extend → multi-format, multi-platform
  6. Export → package delivery
"""
import traceback
from typing import Callable, Optional

from app.models.campaign_models import CampaignBrief, CampaignResult, CampaignStep


PIPELINE_STEPS = [
    ("creative_brief", "创意简报解析"),
    ("mood_direction", "风格定位"),
    ("concept_generation", "概念生成"),
    ("refinement", "精修优化"),
    ("adapt_extend", "多格式适配"),
    ("export", "导出交付"),
]


class CampaignOrchestrator:
    """Runs the 6-step campaign pipeline with progress callbacks."""

    def __init__(
        self,
        brief_parser: Callable,
        mood_agent: Callable,
        concept_agent: Callable,
        refine_agent: Callable,
        adapt_agent: Callable,
        export_agent: Callable,
        on_progress: Optional[Callable] = None,
    ):
        self._agents = {
            "creative_brief": brief_parser,
            "mood_direction": mood_agent,
            "concept_generation": concept_agent,
            "refinement": refine_agent,
            "adapt_extend": adapt_agent,
            "export": export_agent,
        }
        self._on_progress = on_progress

    async def run(self, brief: CampaignBrief, project_id: int) -> CampaignResult:
        """Execute the full campaign pipeline.

        Args:
            brief: User-submitted creative brief.
            project_id: Project ID for asset association.

        Returns:
            CampaignResult with step-by-step status and outputs.
        """
        steps = []
        pipeline_input = brief.model_dump()

        for i, (step_key, step_label) in enumerate(PIPELINE_STEPS):
            agent = self._agents[step_key]
            percent = int(i / len(PIPELINE_STEPS) * 100)

            try:
                step_result = await agent(project_id=project_id, brief=pipeline_input)
                steps.append(CampaignStep(
                    step=step_key,
                    status="completed",
                    progress=100,
                    output=step_result if isinstance(step_result, dict) else {},
                ))
                # Pass output forward to next step
                if isinstance(step_result, dict):
                    pipeline_input.update(step_result)

            except Exception as e:
                steps.append(CampaignStep(
                    step=step_key,
                    status="failed",
                    progress=0,
                    output={"error": str(e)},
                ))
                # Fill remaining steps as pending
                for remaining_key, _ in PIPELINE_STEPS[i + 1:]:
                    steps.append(CampaignStep(step=remaining_key, status="pending"))
                break

            if self._on_progress:
                await self._on_progress(step_label, percent, "completed")

        # Determine final status
        if all(s.status == "completed" for s in steps):
            status = "completed"
        elif any(s.status == "failed" for s in steps):
            status = "failed"
        else:
            status = "in_progress"

        if self._on_progress:
            await self._on_progress("完成", 100, status)

        return CampaignResult(
            project_id=project_id,
            steps=steps,
            status=status,
        )
