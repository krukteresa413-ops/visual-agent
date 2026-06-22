"""Feedback Loop — orchestrates feedback → modification → regeneration."""
from typing import Dict, Optional
from app.services.feedback_processor import FeedbackProcessor


class FeedbackLoop:
    """Manage the iteration loop: generate → preview → feedback → regenerate."""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations

    def iterate(
        self,
        asset: Dict,
        feedback: str,
        iteration: int = 1,
        previous_result: Optional[Dict] = None,
    ) -> Dict:
        """Process one iteration of the feedback loop."""
        # Check max iterations
        if iteration > self.max_iterations:
            return {
                "action": "stop",
                "previous_asset": asset,
                "new_prompt_hint": f"已达到最大修改次数({self.max_iterations})，建议确认当前版本或重新开始。",
                "iteration": iteration,
                "history": (previous_result or {}).get("history", []),
            }

        # Process feedback
        processor = FeedbackProcessor()
        action = processor.process(feedback=feedback, asset_context=asset)

        # Build history
        history = (previous_result or {}).get("history", [])
        history.append({
            "iteration": iteration,
            "feedback": feedback,
            "action": action["action"],
        })

        # Build new prompt hint
        hint_parts = []
        if action["element"]:
            hint_parts.append(f"修改{action['element']}")
        hint_parts.append(action["target"])
        new_hint = "，".join(hint_parts)

        return {
            "action": action["action"],
            "previous_asset": asset,
            "new_prompt_hint": new_hint,
            "iteration": iteration,
            "history": history,
            "element": action["element"],
        }
