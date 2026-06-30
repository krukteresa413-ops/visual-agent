"""Skill registry — centralized config for AI companion skills (P2-12).

Each skill has a preset prompt that gets injected into the chat when selected.
Admins can enable/disable skills without frontend changes.

2026-06-30: 依据「商家.docx」重建为中文技能集，方便中文商家。
保留专有名词（Seedance / Instagram / Facebook / TikTok / LinkedIn / YouTube /
Logo / Slogan / UGC / AI / A+ 等），其余全部汉化。
"""

# 分类固定展示顺序（get_categories 据此返回，避免中文 sorted 乱序）
CATEGORY_ORDER = ["视频", "社交媒体", "电商", "品牌", "营销", "工作室"]

SKILLS = [
    # ── 视频 ──
    {
        "id": "seedance",
        "title": "Seedance 2.0 视频创作",
        "description": "将你的创意落地成可直接发布的视频。",
        "category": "视频",
        "prompt": "请用 Seedance 2.0 为我生成一段可直接发布的产品视频：720p、5 秒、16:9 横屏，主体居中、光线柔和、缓慢推进镜头。",
        "enabled": True,
    },
    {
        "id": "one-shot",
        "title": "一镜到底视频",
        "description": "首尾帧衔接，自动生成无缝长镜头视频。",
        "category": "视频",
        "prompt": "请用 Seedance 2.0 生成一段一镜到底视频：首尾帧无缝衔接，10 秒连续运镜，360° 展示产品全貌。",
        "enabled": True,
    },
    {
        "id": "drone",
        "title": "无人机运镜视频",
        "description": "使用 Seedance 2.0 创建无人机航拍运镜视频。",
        "category": "视频",
        "prompt": "请用 Seedance 2.0 生成一段无人机航拍风格视频：从高空俯冲到产品特写，1080p、8 秒。",
        "enabled": True,
    },
    {
        "id": "storyboard",
        "title": "分镜故事板",
        "description": "将剧本和设定转化为可视化分镜，用于动画或视频制作。",
        "category": "视频",
        "prompt": "请把我的剧本和设定转化为可视化分镜故事板：按场景拆分镜头，给出每格的画面描述、镜头景别与运镜方式。",
        "enabled": True,
    },
    # ── 社交媒体 ──
    {
        "id": "instagram-post",
        "title": "Instagram 帖子",
        "description": "设计具有特定行业视觉基因的 Instagram 原生视觉内容。",
        "category": "社交媒体",
        "prompt": "请为我设计一组 Instagram 原生帖子视觉：贴合品牌行业的视觉基因，提供 1:1 与 4:5 两种尺寸，含主图与文案排版建议。",
        "enabled": True,
    },
    {
        "id": "ad-creative",
        "title": "广告创意",
        "description": "为 Instagram、Facebook、TikTok、LinkedIn、YouTube 等平台生成广告创意。",
        "category": "社交媒体",
        "prompt": "请为我生成多平台广告创意：覆盖 Instagram、Facebook、TikTok、LinkedIn、YouTube，给出各平台的视觉与文案变体。",
        "enabled": True,
    },
    {
        "id": "cross-platform",
        "title": "一键跨平台适配",
        "description": "将单张图片适配为多个平台的原生视觉变体，支持智能重构构图。",
        "category": "社交媒体",
        "prompt": "请把我这张图片一键适配为多个平台的原生视觉变体（小红书 / 抖音 / Instagram / YouTube），按各平台尺寸智能重构构图。",
        "enabled": True,
    },
    {
        "id": "youtube-thumbnail",
        "title": "YouTube 封面图",
        "description": "制作高质量的 YouTube 缩略图，提升点击率。",
        "category": "社交媒体",
        "prompt": "请为我制作一张高点击率的 YouTube 封面缩略图：1280x720、大标题、高对比、强视觉冲击。",
        "enabled": True,
    },
    {
        "id": "design-guide",
        "title": "设计指引",
        "description": "通过结构化问题明确用户意图，提供专业设计指导并生成方案。",
        "category": "社交媒体",
        "prompt": "请作为设计顾问，先用几个结构化问题明确我的意图，再给出专业设计指导与可执行方案。",
        "enabled": True,
    },
    {
        "id": "xhs-cover",
        "title": "小红书封面",
        "description": "一键生成符合平台调性的小红书封面图，提升点击率。",
        "category": "社交媒体",
        "prompt": "请为我生成一张小红书封面图：3:4 竖版、符合平台调性、标题文字突出、暖色调、强种草感。",
        "enabled": True,
    },
    # ── 电商 ──
    {
        "id": "amazon-listing",
        "title": "亚马逊产品套图",
        "description": "为你的产品设计专业的亚马逊商品图和 A+ 内容。",
        "category": "电商",
        "prompt": "请为我的产品设计一套专业亚马逊商品图：主图（白底）、卖点图、场景图与 A+ 内容版式。",
        "enabled": True,
    },
    {
        "id": "ugc-lifestyle",
        "title": "UGC：生活化上身图",
        "description": "即刻批量产出极具真实感的博主穿搭 / 上身图，贴近生活场景。",
        "category": "电商",
        "prompt": "请为我的产品批量生成 UGC 风格的生活化上身图：真实博主质感、自然光、居家 / 街拍场景，弱化摆拍感。",
        "enabled": True,
    },
    {
        "id": "ai-stylist",
        "title": "AI 造型师：高转化模特图",
        "description": "瞬时生成多款专业模特造型，全方位展现商品潜力，触达更广人群。",
        "category": "电商",
        "prompt": "请用 AI 造型师为我的服饰 / 商品生成多款高转化模特图：不同人种、年龄与场景，专业棚拍光效。",
        "enabled": True,
    },
    # ── 品牌 ──
    {
        "id": "web-to-inspiration",
        "title": "网页变灵感",
        "description": "把任意网页链接变成你自己的设计与视觉灵感。",
        "category": "品牌",
        "prompt": "请把我给的网页链接转化为可复用的设计灵感：提炼配色、版式、字体与视觉风格，并给出应用建议。",
        "enabled": True,
    },
    {
        "id": "logo-and-brand",
        "title": "Logo 与品牌",
        "description": "为你的品牌创建 Logo 和周边视觉系列。",
        "category": "品牌",
        "prompt": "请为我的品牌创建一套 Logo 与周边视觉：主标志、辅助图形、配色，以及名片 / 包装样机。",
        "enabled": True,
    },
    {
        "id": "product-marketing-set",
        "title": "产品营销组图",
        "description": "上传产品图、Logo、品牌名和 Slogan，一键生成 8 张覆盖多场景的营销组图。",
        "category": "品牌",
        "prompt": "请根据我的产品图、Logo、品牌名和 Slogan，一键生成 8 张覆盖多场景的产品营销组图。",
        "enabled": True,
    },
    {
        "id": "logo-design",
        "title": "Logo 设计",
        "description": "从一个品牌名出发，生成完整的 Logo 系统——主标志加多种应用变体。",
        "category": "品牌",
        "prompt": "请从我的品牌名出发，设计一套完整 Logo 系统：主标志、横版 / 竖版 / 图标变体、黑白与反白版本。",
        "enabled": True,
    },
    # ── 营销 ──
    {
        "id": "marketing-brochure",
        "title": "营销宣传册",
        "description": "设计活动、服务和产品推广的三折页宣传册。",
        "category": "营销",
        "prompt": "请为我设计一份三折页营销宣传册：用于活动 / 服务 / 产品推广，含封面、内页版式与文案排布。",
        "enabled": True,
    },
    # ── 工作室 ──
    {
        "id": "interior-design",
        "title": "室内设计",
        "description": "室内设计全流程出图助手。支持六种输出类型：空间效果图、平面方案、风格参考等。",
        "category": "工作室",
        "prompt": "请作为室内设计出图助手：我会说明风格、户型与需求，请输出空间效果图，并给出材质与配色建议。",
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
    """Return categories that have at least one enabled skill, in fixed display order."""
    enabled = {s["category"] for s in SKILLS if s["enabled"]}
    ordered = [c for c in CATEGORY_ORDER if c in enabled]
    extras = sorted(enabled - set(CATEGORY_ORDER))  # 兜底:未列入顺序的分类追加在后
    return ordered + extras
