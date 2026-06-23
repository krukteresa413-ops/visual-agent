"""Brand memory learner — detects edit patterns and updates BrandProfile."""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BrandMemoryLearner:
    """Analyzes user edits to learn brand preferences over time."""

    def __init__(self, llm=None):
        self._llm = llm

    async def learn_from_edit(
        self,
        project_id: int,
        edit_type: str,
        before: str,
        after: str,
    ) -> Dict:
        """Analyze an edit and update BrandProfile if a pattern is detected."""
        if before.strip() == after.strip():
            return {"tone_updated": False, "reason": "no_change"}

        if edit_type != "text":
            return {"tone_updated": False, "reason": f"unsupported_type:{edit_type}"}

        if self._llm is None:
            return {"tone_updated": False, "reason": "no_llm"}

        # Ask LLM to analyze the tone shift
        analysis = await self._llm(
            system_prompt=(
                "Analyze the tone change between two versions of marketing copy. "
                "Return JSON: {\"tone_detected\": \"<one word>\", \"confidence\": 0.0-1.0}"
            ),
            user_prompt=f"Before: {before}\nAfter: {after}",
        )

        if analysis.get("confidence", 0) < 0.7:
            return {"tone_updated": False, "reason": "low_confidence"}

        # Update BrandProfile
        from app.db.session import SessionLocal
        from app.models.brand_profile import BrandProfile

        db = SessionLocal()
        try:
            bp = db.query(BrandProfile).filter_by(project_id=project_id).first()
            if bp:
                bp.tone_of_voice = analysis["tone_detected"]
                db.commit()
                logger.info(
                    f"BrandProfile tone updated: project={project_id} "
                    f"tone={analysis['tone_detected']}"
                )
                return {"tone_updated": True, "tone": analysis["tone_detected"]}
            return {"tone_updated": False, "reason": "no_brand_profile"}
        finally:
            db.close()
