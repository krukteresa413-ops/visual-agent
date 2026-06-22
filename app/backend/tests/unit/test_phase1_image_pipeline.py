"""Phase 1 image URL integration tests."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.unit.test_parallel import MOCKS, SAMPLE_BRIEF


class _GeneratedImage:
    def __init__(self, url: str, width: int = 768, height: int = 768):
        self.url = url
        self.width = width
        self.height = height


@pytest.mark.asyncio
async def test_generate_all_embeds_local_image_urls_into_plan():
    """generate_all should render planned images and persist URLs in the plan."""
    from app.services.visual_agent import VisualAgent

    agent = VisualAgent()
    agent._llm.call = AsyncMock(side_effect=MOCKS.copy())

    async def fake_generate(request):
        return SimpleNamespace(
            images=[_GeneratedImage(f"/uploads/generated/{request.provider}_{request.model or 'auto'}_{request.width}x{request.height}.png")]
        )

    with patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
        mock_layout.return_value = None
        with patch("app.services.image_generation_service.image_generation_service.generate", new=fake_generate):
            result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)

    main = result.main_image.model_dump()
    scenes = [scene.model_dump() for scene in result.scene_images]

    assert main["url"].startswith("/uploads/generated/dataeyes_auto_")
    assert main["thumbnail_url"] == main["url"]
    assert scenes[0]["url"].startswith("/uploads/generated/dataeyes_auto_")
    assert scenes[0]["thumbnail_url"] == scenes[0]["url"]


def test_ensure_canvas_image_elements_seeds_thumbnail_elements():
    """Rendered images should become image elements in canvas-state."""
    from app.api.unified_generation_routes import _ensure_canvas_image_elements

    state_holder = {"state": None}

    class Query:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return state_holder["state"]

    db = MagicMock()
    db.query.return_value = Query()

    asset_plan = {
        "main_image": {"goal": "Hero", "url": "/uploads/generated/main.png"},
        "white_bg": {"goal": "White", "url": "/uploads/generated/white.png"},
        "scene_images": [
            {"scene_name": "Scene A", "url": "/uploads/generated/scene-a.png"},
        ],
    }

    _ensure_canvas_image_elements(db, 99, asset_plan)

    created_state = db.add.call_args.args[0]
    state_holder["state"] = created_state
    assert db.commit.called

    import json
    elements = json.loads(created_state.elements_json)
    assert len(elements) == 3
    assert {element["type"] for element in elements} == {"image"}
    assert all(element["thumbnail_url"].startswith("/uploads/generated/") for element in elements)
    assert all(element["asset_ref"]["url"] == element["thumbnail_url"] for element in elements)


@pytest.mark.asyncio
async def test_generate_all_passes_selected_image_provider_and_model():
    from app.services.visual_agent import VisualAgent

    agent = VisualAgent()
    agent._llm.call = AsyncMock(side_effect=MOCKS.copy())
    seen = []

    async def fake_generate(request):
        seen.append((request.provider, request.model))
        return SimpleNamespace(images=[_GeneratedImage("/uploads/generated/selected.png")])

    with patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
        mock_layout.return_value = None
        with patch("app.services.image_generation_service.image_generation_service.generate", new=fake_generate):
            await agent.generate_all(
                project_id=1,
                brief=SAMPLE_BRIEF,
                image_provider="dataeyes",
                image_model="gemini-3-pro-image-preview",
            )

    assert seen
    assert all(provider == "dataeyes" for provider, _ in seen)
    assert all(model == "gemini-3-pro-image-preview" for _, model in seen)
