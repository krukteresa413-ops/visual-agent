"""Skill registry — centralized config for AI companion skills (P2-12).

Each skill has a preset prompt that gets injected into the chat when selected.
Admins can enable/disable skills without frontend changes.
"""
SKILLS = [
    {
        "id": "seedance",
        "title": "Seedance 2.0 视频创作",
        "description": "将你的创意落地成可直接发布的视频。",
        "category": "Video",
        "prompt": "请为我生成一段产品展示视频：Seedance 2.0、720p、5秒、16:9横屏。产品主体居中，灯光柔和，慢速推进镜头。",
        "enabled": True,
    },
    {
        "id": "one-shot",
        "title": "一镜到底视频",
        "description": "首尾帧衔接，自动生成无缝长镜头视频。",
        "category": "Video",
        "prompt": "请为我生成一段一镜到底视频：使用 Seedance 2.0，首尾帧无缝衔接，10秒连续运镜，展示产品360度全貌。",
        "enabled": True,
    },
    {
        "id": "drone",
        "title": "无人机运镜视频",
        "description": "使用 Seedance 2.0 创建无人机运镜视频",
        "category": "Video",
        "prompt": "请为我生成一段无人机航拍风格视频：从高空俯冲至产品特写，Seedance 2.0、1080p、8秒。",
        "enabled": True,
    },
    {
        "id": "product",
        "title": "产品广告视频",
        "description": "快速生成专业级产品广告短片",
        "category": "Social Media",
        "prompt": "请为我生成一段15秒社交媒体产品广告：快节奏剪辑、文字覆盖、适配 TikTok/Reels 竖屏 9:16。",
        "enabled": True,
    },
    {
        "id": "social-reel",
        "title": "社交媒体 Reel",
        "description": "适配 Instagram/TikTok 的竖屏短视频",
        "category": "Social Media",
        "prompt": "请为我生成一段竖屏社交媒体 Reel：潮流 BGM 风格、产品展示、快速转场，适配 Instagram/TikTok。",
        "enabled": True,
    },
    {
        "id": "brand-story",
        "title": "品牌故事短片",
        "description": "用视觉叙事传达品牌核心价值",
        "category": "Branding",
        "prompt": "请为我生成一段品牌故事短片：30秒内讲述品牌起源与核心价值，温暖色调、真实场景、人物出镜。",
        "enabled": True,
    },
    {
        "id": "create",
        "title": "基于此对话创建 Skill",
        "description": "在 Thinking 模式下将对话总结为可复用的 Skill",
        "category": "Video",
        "prompt": "",
        "enabled": False,
    },
    {
        "id": "background-removal",
        "title": "智能抠图",
        "description": "一键去除图片背景，保留主体",
        "category": "E-Commerce",
        "prompt": "请帮我去除这张图片的背景，只保留产品主体，输出白色背景 PNG。",
        "enabled": True,
    },
    {
        "id": "color-variant",
        "title": "换色方案",
        "description": "为产品生成多色变体展示图",
        "category": "E-Commerce",
        "prompt": "请为这个产品生成 4 种不同配色方案的展示图：经典黑、简约白、品牌橙、高级灰。",
        "enabled": True,
    },
    {
        "id": "social-post",
        "title": "社交媒体图文",
        "description": "一键生成小红书/朋友圈图文素材",
        "category": "Social Media",
        "prompt": "请为我生成一张小红书风格的图文素材：产品居中、文字覆盖标题和卖点、暖色调、1080x1440竖屏。",
        "enabled": True,
    },
    {
        "id": "detail-page",
        "title": "详情页排版",
        "description": "自动生成电商详情页视觉排版",
        "category": "E-Commerce",
        "prompt": "请为我生成一张电商详情页排版图：产品主图+卖点图标+规格参数+使用场景，750x2000，品牌橙色点缀。",
        "enabled": True,
    },
    {
        "id": "logo-design",
        "title": "Logo 设计",
        "description": "AI 生成品牌 Logo 方案",
        "category": "Branding",
        "prompt": "请为我设计一个现代简约风格的品牌 Logo：以几何图形为主，品牌橙色+深灰配色，适合科技/AI 行业。",
        "enabled": True,
    },
]


def get_enabled_skills(category: str | None = None) -> list[dict]:
    """Return enabled skills, optionally filtered by category."""
    skills = [s for s in SKILLS if s["enabled"]]
    if category:
        skills = [s for s in skills if s["category"] == category]
    return [dict(s) for s in skills]


def get_skill(skill_id: str) -> dict | None:
    """Get a single skill by ID (including disabled ones for direct lookup)."""
    for s in SKILLS:
        if s["id"] == skill_id:
            return dict(s)
    return None


def get_categories() -> list[str]:
    """Return list of categories that have at least one enabled skill."""
    cats = set()
    for s in SKILLS:
        if s["enabled"]:
            cats.add(s["category"])
    return sorted(cats)
