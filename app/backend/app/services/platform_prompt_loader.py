"""
Platform prompt loader — loads platform-specific Jinja2 templates and
appends them to the system prompt for platform-aware generation.

PRD 7.7 — 本土化平台适配
"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_prompt_dir = Path(__file__).parent.parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_prompt_dir)))

# Map platform IDs to template files
PLATFORM_TEMPLATES = {
    "taobao": "platform_taobao.j2",
    "jd": "platform_taobao.j2",  # JD shares Taobao template (similar)
    "pinduoduo": "platform_pinduoduo.j2",
    "xiaohongshu": "platform_xiaohongshu.j2",
    "douyin": "platform_douyin.j2",
    "amazon": "platform_amazon.j2",
}


def load_platform_prompt(platform_id: str, brief: dict) -> str:
    """Load platform-specific prompt and render with brief context."""
    template_name = PLATFORM_TEMPLATES.get(platform_id)
    if not template_name:
        return ""

    try:
        tmpl = _env.get_template(template_name)
        return tmpl.render(brief=brief)
    except Exception:
        return ""


def get_platform_context(platform_id: str) -> str:
    """Get a concise platform context for the system prompt."""
    from app.services.platform_specs import get_platform_spec

    spec = get_platform_spec(platform_id)
    if not spec:
        return ""

    lines = [f"\n## 平台要求：{spec['name']}"]
    if "style" in spec:
        lines.append(f"视觉风格：{spec['style']}")
    if "文案风格" in spec:
        lines.append(f"文案风格：{spec['文案风格']}")
    if "main_image" in spec:
        mi = spec["main_image"]
        lines.append(f"主图尺寸：{mi.get('width')}x{mi.get('height')}px")

    return "\n".join(lines)
