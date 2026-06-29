"""quick-generate 必须把源图真正透传给图像服务(需求二)。

只 import 路由模块 + patch image_generation_service.generate,不经 main(避免在生产库建表)。
"""
import pytest
from types import SimpleNamespace
from unittest.mock import patch

from app.models.image_generation_model import GeneratedImage, ImageGenerationResult
from app.services.image_generation_service import image_generation_service


def _req(**kw):
    base = dict(
        prompt="把背景换成沙滩",
        image_provider="dataeyes",
        image_model=None,
        auto_model=True,
        reference_image_url="/uploads/src.png",
        project_id=2,
    )
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_quick_image_asset_passes_reference_and_locks_dataeyes():
    from app.api import unified_generation_routes as ugr

    captured = {}

    async def fake_generate(request):
        captured["request"] = request
        return ImageGenerationResult(
            provider="dataeyes",
            status="succeeded",
            images=[GeneratedImage(url="/uploads/generated/out.png", width=1024, height=1024)],
        )

    with patch.object(image_generation_service, "generate", side_effect=fake_generate):
        await ugr._quick_generate_image_asset(_req(), {})

    r = captured["request"]
    # 源图被真正透传(此前完全没传)
    assert r.reference_image_url == "/uploads/src.png"
    # 有源图时锁定 dataeyes(唯一吃图),不静默回退成丢图文生图
    assert r.provider == "dataeyes"
    # img2img 指令注入:保留主体 + 用户原指令
    assert "保留" in r.prompt and "沙滩" in r.prompt


@pytest.mark.asyncio
async def test_quick_image_asset_no_reference_keeps_fallback_chain():
    """回归:无源图时不锁链,保留原 provider 回退行为。"""
    from app.api import unified_generation_routes as ugr

    captured = {}

    async def fake_generate(request):
        captured["request"] = request
        return ImageGenerationResult(
            provider=request.provider,
            status="succeeded",
            images=[GeneratedImage(url="/uploads/generated/out.png", width=1024, height=1024)],
        )

    with patch.object(image_generation_service, "generate", side_effect=fake_generate):
        await ugr._quick_generate_image_asset(_req(reference_image_url=None), {})

    r = captured["request"]
    assert r.reference_image_url is None
    assert "保留" not in r.prompt  # 无源图不注入 img2img 指令
