"""Storyboard generation service — LLM-powered brief-to-storyboard (P2.2)."""
from app.services.llm_utils import parse_json

from app.models.video_generation_model import Storyboard, StoryboardShot

STORYBOARD_SYSTEM_PROMPT = """You are a professional video director and storyboard artist.

Given a creative brief, generate a storyboard with 3-8 shots. Output ONLY valid JSON:

{
    "title": "video title",
    "shots": [
        {
            "shot_number": 1,
            "description": "detailed shot description in Chinese",
            "camera_angle": "close-up|medium|wide|aerial|dutch|pov",
            "duration": 3.0,
            "transition": "cut|fade-in|fade-out|dissolve|wipe",
            "dialogue": "spoken text or empty string",
            "visual_prompt": "detailed visual prompt for AI image generation, in English"
        }
    ],
    "total_duration": 12.0
}

Rules:
- At least 3 shots, at most 8
- visual_prompt must be in English for image generation APIs
- description and dialogue in Chinese
- duration per shot: 2.0-8.0 seconds
- total_duration must equal sum of all shot durations
- Think like a director: variety in camera angles, build a narrative arc
"""


class StoryboardService:
    """Generates storyboards from creative briefs using an LLM."""

    MIN_SHOTS = 3

    def __init__(self, llm_client):
        self._llm = llm_client

    async def generate_storyboard(self, brief: str) -> Storyboard:
        """Generate a storyboard from a creative brief.

        Args:
            brief: Chinese creative brief describing the video concept.

        Returns:
            Storyboard with 3-8 shots.

        Raises:
            Exception: If LLM call fails.
            ValueError: If storyboard has fewer than MIN_SHOTS shots.
        """
        user_prompt = f"为以下创意简报生成分镜脚本：\n\n{brief}"

        try:
            raw = await self._llm.generate(
                system=STORYBOARD_SYSTEM_PROMPT,
                prompt=user_prompt,
            )
        except Exception as e:
            raise Exception(f"storyboard generation failed: {e}") from e

        data = parse_json(raw)
        storyboard = self._build_storyboard(data)

        if len(storyboard.shots) < self.MIN_SHOTS:
            raise ValueError(
                f"Storyboard has {len(storyboard.shots)} shots, "
                f"but at least {self.MIN_SHOTS} required"
            )

        return storyboard


    @staticmethod
    def _safe_str(val: object, default: str = "") -> str:
        """Return str value, falling back to default if None/missing."""
        if val is None:
            return default
        return str(val)

    def _build_storyboard(self, data: dict) -> Storyboard:
        """Build Storyboard from parsed JSON, applying defaults.

        Uses _safe_str to handle JSON null values that Pydantic str fields
        would otherwise reject.
        """
        shots_data = data.get("shots")
        if not isinstance(shots_data, list):
            raise ValueError("storyboard 'shots' must be a non-empty list")

        shots = [
            StoryboardShot(
                shot_number=s.get("shot_number", i + 1),
                description=self._safe_str(s.get("description"), ""),
                visual_prompt=self._safe_str(s.get("visual_prompt"), ""),
                camera_angle=self._safe_str(s.get("camera_angle"), "medium"),
                duration=s.get("duration", 5.0),
                transition=self._safe_str(s.get("transition"), "cut"),
                dialogue=self._safe_str(s.get("dialogue"), ""),
            )
            for i, s in enumerate(shots_data)
        ]
        return Storyboard(
            title=self._safe_str(data.get("title"), "Untitled"),
            shots=shots,
            total_duration=data.get("total_duration", sum(s.duration for s in shots)),
        )
