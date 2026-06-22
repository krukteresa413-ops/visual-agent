"""Brand Strategy Agent - Template-based brand strategy generation."""
from typing import Optional, Dict, List
from app.services.industry_templates import INDUSTRY_TEMPLATES


class BrandStrategyAgent:
    """Template-based brand strategy agent, no LLM required."""

    def generate_strategy(
        self,
        industry: str,
        product_name: str,
        target_audience: Optional[str] = None
    ) -> Optional[Dict]:
        """Generate brand strategy from industry template."""
        template = INDUSTRY_TEMPLATES.get(industry)
        if not template:
            return None

        return {
            "visual_style": template["visual_style"],
            "color_palette": template["color_palette"],
            "tone_of_voice": template["copywriting_tone"],
            "forbidden_elements": template["forbidden"],
            "prompt_modifiers": template["prompt_modifiers"],
            "scene_suggestions": template["scene_suggestions"],
            "photo_style": template["photo_style"],
            "industry_name": template["name"],
        }

    def generate_copywriting_guidelines(self, industry: str) -> Optional[Dict]:
        """Generate copywriting guidelines from industry template."""
        template = INDUSTRY_TEMPLATES.get(industry)
        if not template:
            return None

        return {
            "tone": template["copywriting_tone"],
            "forbidden": template["forbidden"],
        }

    def generate_visual_keywords(self, industry: str) -> Optional[List[str]]:
        """Extract visual keywords from industry template."""
        template = INDUSTRY_TEMPLATES.get(industry)
        if not template:
            return None

        keywords = []
        keywords.extend(template["scene_suggestions"])
        keywords.append(template["visual_style"])
        keywords.append(template["photo_style"])
        
        return keywords
