"""Skills API — serves AI companion skills from backend config (P2-12).

Skills are loaded from skill_registry.py. Only enabled skills are exposed.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.config.skill_registry import get_enabled_skills, get_skill, get_categories

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("/categories")
def list_categories():
    """List skill categories that have at least one enabled skill."""
    return get_categories()


@router.get("")
def list_skills(category: Optional[str] = Query(None)):
    """List enabled skills, optionally filtered by category."""
    return get_enabled_skills(category)


@router.get("/{skill_id}")
def get_single_skill(skill_id: str):
    """Get a single skill by ID. Returns 404 if not found or disabled."""
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    if not skill.get("enabled"):
        raise HTTPException(status_code=404, detail=f"Skill is disabled: {skill_id}")
    return skill
