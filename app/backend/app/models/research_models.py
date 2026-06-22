"""Research data models for platform trend analysis (P2.3)."""
from pydantic import BaseModel


class PlatformTrend(BaseModel):
    """Trend data for one platform + category."""
    platform: str
    category: str
    trends: list[str]
    visual_styles: list[str]
    copywriting_patterns: list[str]
    price_range: str
    hot_keywords: list[str]


class ResearchReport(BaseModel):
    """Aggregated trend research report across platforms."""
    category: str
    platforms: list[PlatformTrend]
    summary: str
    moe_recommendations: list[str]
