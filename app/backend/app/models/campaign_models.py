"""Campaign workflow models for P4.1 — autonomous 6-step pipeline."""
from pydantic import BaseModel
from typing import Optional


class CampaignBrief(BaseModel):
    """User-submitted creative brief for a campaign."""
    project_name: str
    description: str
    target_audience: str = ""
    key_message: str = ""
    platforms: list[str] = []
    style_preferences: Optional[str] = None


class CampaignStep(BaseModel):
    """A single step in the campaign pipeline."""
    step: str
    status: str = "pending"  # pending, in_progress, completed, failed
    progress: int = 0  # 0-100
    output: dict = {}


class CampaignResult(BaseModel):
    """Result of running the full campaign pipeline."""
    project_id: int
    steps: list[CampaignStep]
    status: str = "pending"  # pending, in_progress, completed, failed
