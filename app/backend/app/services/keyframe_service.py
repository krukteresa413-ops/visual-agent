"""Keyframe generation service — generates images for storyboard shots (P2.2)."""
import asyncio

from app.models.video_generation_model import Storyboard, Keyframe


class KeyframeService:
    """Generates keyframe images for each shot in a storyboard."""

    def __init__(self, image_service):
        """Initialize with an image generation service.

        Args:
            image_service: An async service with a generate() method that accepts
                          a prompt and returns a result with .images[0].url.
        """
        self._image = image_service

    async def generate_keyframes(self, storyboard: Storyboard) -> list[Keyframe]:
        """Generate one keyframe image per storyboard shot.

        Generates all keyframes concurrently.
        Failed shots get an empty image_url — partial success is acceptable.

        Args:
            storyboard: The storyboard with shots to generate keyframes for.

        Returns:
            List of Keyframe objects, one per shot, in shot order.
        """
        tasks = []
        for shot in storyboard.shots:
            tasks.append(self._generate_one(shot.shot_number, shot.visual_prompt))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        keyframes = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                keyframes.append(Keyframe(
                    shot_number=storyboard.shots[i].shot_number,
                    image_url="",
                    prompt=storyboard.shots[i].visual_prompt,
                ))
            else:
                keyframes.append(result)

        return keyframes

    async def _generate_one(self, shot_number: int, prompt: str) -> Keyframe:
        """Generate a single keyframe, raising on failure."""
        from app.models.image_generation_model import ImageGenerationRequest
        img_request = ImageGenerationRequest(
            provider="mige",
            prompt=prompt,
            width=1024,
            height=576,
        )
        result = await self._image.generate(img_request)
        image_url = result.images[0].url
        return Keyframe(shot_number=shot_number, image_url=image_url, prompt=prompt)
