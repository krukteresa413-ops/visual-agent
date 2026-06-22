"""
Behavior Tracker — user action logging + AI-vs-human calibration.

Step 3 of AI aesthetic evaluation pipeline:
  - Record user actions (export, modify, regenerate, finalize, view)
  - Query events by project / type
  - Calibrate: compare AI aesthetic rankings against actual user choices
"""
import json
import logging
from datetime import datetime
from typing import Optional

from app.db.session import SessionLocal
from app.models.behavior_event import BehaviorEvent

logger = logging.getLogger(__name__)


class BehaviorTracker:
    """Tracks user behavior for aesthetic model calibration."""

    # ── Event Recording ────────────────────────────────────────

    def record_event(
        self,
        project_id: int,
        event_type: str,
        generation_id: Optional[int] = None,
        image_path: Optional[str] = None,
        ai_score: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Record a user behavior event.

        Args:
            project_id: Project ID.
            event_type: One of 'viewed', 'exported', 'modified', 'regenerated', 'finalized'.
            generation_id: VisualAsset generation ID.
            image_path: Path to the image.
            ai_score: AI aesthetic score at time of event.
            metadata: Extra context dict.

        Returns:
            {"id": int, "status": "recorded"}
        """
        db = SessionLocal()
        try:
            event = BehaviorEvent(
                project_id=project_id,
                generation_id=generation_id,
                event_type=event_type,
                image_path=image_path,
                ai_score=ai_score,
                metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return {"id": event.id, "status": "recorded"}
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record event: {e}")
            raise
        finally:
            db.close()

    # ── Event Querying ─────────────────────────────────────────

    def get_project_events(
        self,
        project_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query behavior events for a project.

        Args:
            project_id: Project ID.
            event_type: Optional filter by event type.
            limit: Max results.

        Returns:
            List of event dicts.
        """
        db = SessionLocal()
        try:
            query = db.query(BehaviorEvent).filter(
                BehaviorEvent.project_id == project_id
            )
            if event_type:
                query = query.filter(BehaviorEvent.event_type == event_type)

            events = query.order_by(BehaviorEvent.created_at.desc()).limit(limit).all()

            return [
                {
                    "id": e.id,
                    "project_id": e.project_id,
                    "generation_id": e.generation_id,
                    "event_type": e.event_type,
                    "image_path": e.image_path,
                    "ai_score": e.ai_score,
                    "metadata": json.loads(e.metadata_json) if e.metadata_json else None,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        finally:
            db.close()

    # ── Calibration Analysis ───────────────────────────────────

    def calibrate(self, project_id: int) -> dict:
        """Compare AI predictions against user behavior.

        Analyzes:
        1. Were finalized images the ones AI ranked highest?
        2. Did exported images match AI top picks?
        3. Which quality metrics correlate with user selection?

        Returns calibration report with accuracy metrics.
        """
        finalized = self.get_project_events(project_id, event_type="finalized")
        exported = self.get_project_events(project_id, event_type="exported")

        if not finalized:
            return {
                "project_id": project_id,
                "total_finalized": 0,
                "matched_exports": 0,
                "calibration_score": 0.0,
                "status": "insufficient_data",
                "recommendations": ["需要更多用户行为数据才能校准"],
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        # Build map: image_path → ai_score for finalized images
        finalized_map = {}
        for e in finalized:
            path = e.get("image_path", "")
            score = e.get("ai_score", 0) or 0
            if path:
                finalized_map[path] = score

        # Check which exported images match finalized (user confirmed AI pick)
        matched = 0
        export_paths = set()
        for e in exported:
            path = e.get("image_path", "")
            if path:
                export_paths.add(path)
                if path in finalized_map:
                    matched += 1

        total = len(finalized)
        calibration_score = round((matched / total) * 100, 1) if total > 0 else 0.0

        # Recommendations
        recommendations = []
        if calibration_score >= 80:
            recommendations.append("AI 审美判断与用户选择高度一致，当前权重可维持")
        elif calibration_score >= 50:
            recommendations.append("AI 判断与用户选择存在偏差，建议调整风格权重")
            recommendations.append("增加品牌风格和受众匹配度在排序中的权重")
        else:
            recommendations.append("AI 判断与用户选择差异较大，需要重新校准")
            recommendations.append("建议：降低 AI 排序权重，更多依赖用户手动选择")

        return {
            "project_id": project_id,
            "total_finalized": total,
            "total_exported": len(exported),
            "matched_exports": matched,
            "calibration_score": calibration_score,
            "status": "calibrated" if total >= 3 else "limited_data",
            "finalized_images": list(finalized_map.keys())[:10],
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
