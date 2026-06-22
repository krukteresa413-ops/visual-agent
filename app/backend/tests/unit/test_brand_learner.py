"""
TDD Step 1 (RED→GREEN): BrandMemoryLearner tests.
Mock SessionLocal at source: app.db.session
"""
import pytest
from unittest.mock import AsyncMock, patch


def make_brand_profile(**overrides):
    data = {
        "id": 1, "project_id": 1, "name": "Test Brand",
        "tone_of_voice": "professional",
        "visual_keywords": '["minimal", "clean"]',
        "forbidden_words": '["cheap"]',
        "font_style": "sans-serif", "primary_color": "#333333",
    }
    data.update(overrides)
    return data


def make_mock_db():
    """Create a mock DB session that supports SQLAlchemy query chains."""
    bp = type("BP", (), make_brand_profile())()
    db = type("DB", (), {
        "query": lambda *a, **kw: db,
        "filter_by": lambda *a, **kw: db,
        "first": lambda *a: bp,
        "commit": lambda *a: None,
        "close": lambda *a: None,
    })()
    return db


@pytest.mark.asyncio
async def test_learn_from_text_edit_updates_tone():
    """文本编辑后应分析语调并更新 BrandProfile.tone_of_voice。"""
    from app.services.brand_memory_learner import BrandMemoryLearner

    mock_llm = AsyncMock(return_value={
        "tone_detected": "playful", "confidence": 0.85,
    })

    with patch("app.db.session.SessionLocal", return_value=make_mock_db()):
        learner = BrandMemoryLearner(llm=mock_llm)
        result = await learner.learn_from_edit(
            project_id=1, edit_type="text",
            before="专业高端品质", after="轻松活泼好玩",
        )
    assert result["tone_updated"] is True
    mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_learn_skips_when_no_change():
    """无实质变化时不应触发 LLM 调用。"""
    from app.services.brand_memory_learner import BrandMemoryLearner
    mock_llm = AsyncMock()
    with patch("app.db.session.SessionLocal", return_value=make_mock_db()):
        learner = BrandMemoryLearner(llm=mock_llm)
        result = await learner.learn_from_edit(
            project_id=1, edit_type="text",
            before="same text", after="same text",
        )
    assert result["tone_updated"] is False
    mock_llm.assert_not_called()
