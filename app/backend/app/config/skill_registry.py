"""Skill registry — centralized config for AI companion skills (P2-12).

Each skill has a preset prompt that gets injected into the chat when selected.
Admins can enable/disable skills without frontend changes.

2026-06-30: 依据「商家.docx」重建为中文技能集，方便中文商家。
保留专有名词（Seedance / Instagram / Facebook / TikTok / LinkedIn / YouTube /
Logo / Slogan / UGC / AI / A+ 等），其余全部汉化。

2026-06-30(prompt 增强): 每个技能点击后只走一条管线、产出"一张图/一段视频"。
故所有 prompt 改写为具体的单产出生成指令；原本"套图/组图/系统/多变体"语义改为
"一张拼版图(九宫格/变体拼版/品牌板)"，既可用又保留含义；两个依赖对话/URL 抓取的
技能(设计指引/网页变灵感)改为可交付的灵感板(moodboard)图。
"""

# 分类固定展示顺序（get_categories 据此返回，避免中文 sorted 乱序）
CATEGORY_ORDER = ["视频", "社交媒体", "电商", "品牌", "营销", "工作室"]

SKILLS = [
    # ── 视频（video-gen，产出一段视频）──
    {
        "id": "seedance",
        "title": "Seedance 2.0 视频创作",
        "description": "将你的创意落地成可直接发布的视频。",
        "category": "视频",
        "prompt": "用 Seedance 2.0 生成一段电商产品展示视频：产品主体居中、背景干净、柔和影棚光，镜头缓慢环绕并轻微推近，画面稳定、商业质感；720p、5 秒、16:9 横屏，可直接发布。",
        "enabled": True,
    },
    {
        "id": "one-shot",
        "title": "一镜到底视频",
        "description": "首尾帧衔接，自动生成无缝长镜头视频。",
        "category": "视频",
        "prompt": "用 Seedance 2.0 生成一段一镜到底视频：单镜头连续运镜、首尾自然衔接，围绕产品 360° 平滑环绕展示全貌、无跳切；1080p、10 秒、16:9。",
        "enabled": True,
    },
    {
        "id": "drone",
        "title": "无人机运镜视频",
        "description": "使用 Seedance 2.0 创建无人机航拍运镜视频。",
        "category": "视频",
        "prompt": "用 Seedance 2.0 生成一段无人机航拍运镜视频：从高空俯瞰缓缓俯冲、拉近至主体特写，运动平稳、空间纵深感强、光线通透、电影质感；1080p、8 秒、16:9。",
        "enabled": True,
    },
    {
        "id": "storyboard",
        "title": "分镜故事板",
        "description": "将剧本和设定转化为可视化分镜，用于动画或视频制作。",
        "category": "视频",
        "prompt": "用 Seedance 2.0 生成一段分镜叙事短片：用 3-4 个连续镜头讲述一个简短产品故事（远景交代场景 → 中景展示使用 → 近景特写卖点），镜头间自然过渡；1080p、8 秒、16:9。",
        "enabled": True,
    },
    # ── 社交媒体（image-gen，产出一张图）──
    {
        "id": "instagram-post",
        "title": "Instagram 帖子",
        "description": "设计具有特定行业视觉基因的 Instagram 原生视觉内容。",
        "category": "社交媒体",
        "prompt": "生成一张 Instagram 原生风格的方形(1:1)帖子图：构图精致、主体突出、留白得当、配色清爽统一，顶部或中部预留少量标题文字位；高分辨率、可直接发布。",
        "enabled": True,
    },
    {
        "id": "ad-creative",
        "title": "广告创意",
        "description": "为 Instagram、Facebook、TikTok、LinkedIn、YouTube 等平台生成广告主视觉。",
        "category": "社交媒体",
        "prompt": "生成一张社交平台广告主视觉(单张 KV)：主体醒目，含清晰的大标题与一句卖点文案区、强视觉对比、引导点击；竖版 4:5、商业广告质感。",
        "enabled": True,
    },
    {
        "id": "cross-platform",
        "title": "一键跨平台适配",
        "description": "将画面主体重排为平台原生视觉变体，支持智能重构构图。",
        "category": "社交媒体",
        "prompt": "把画面主体重新排布，生成一张社交平台原生竖版(9:16)视觉：主体居中、背景自然延展、顶部预留标题位，适配小红书 / 抖音 / Reels；若提供参考图则保留其主体。",
        "enabled": True,
    },
    {
        "id": "youtube-thumbnail",
        "title": "YouTube 封面图",
        "description": "制作高质量的 YouTube 缩略图，提升点击率。",
        "category": "社交媒体",
        "prompt": "生成一张高点击率的 YouTube 封面缩略图(16:9，1280x720)：主体放大、情绪 / 卖点强烈、超大粗体标题文字、高饱和高对比、制造好奇钩子。",
        "enabled": True,
    },
    {
        "id": "design-guide",
        "title": "设计指引",
        "description": "生成设计方向参考板：配色、字体、版式与质感的视觉指引。",
        "category": "社交媒体",
        "prompt": "生成一张设计方向参考板(moodboard)：在一张图内拼贴呈现配色方案、字体风格示例、版式示意与材质质感参考，整体风格统一专业，可作为设计提案的视觉指引。",
        "enabled": True,
    },
    {
        "id": "xhs-cover",
        "title": "小红书封面",
        "description": "一键生成符合平台调性的小红书封面图，提升点击率。",
        "category": "社交媒体",
        "prompt": "生成一张小红书爆款封面图(竖版 3:4)：清新生活化、主体居中、配超大醒目标题文字、暖色调、强种草氛围、留白舒适。",
        "enabled": True,
    },
    # ── 电商（image-gen，产出一张图）──
    {
        "id": "amazon-listing",
        "title": "亚马逊产品套图",
        "description": "为你的产品设计专业的亚马逊商品主图（白底、合规）。",
        "category": "电商",
        "prompt": "生成一张符合亚马逊主图规范的产品图：纯白背景、产品居中占比约 85%、专业电商棚拍布光、无文字无水印、边缘干净、清晰高分辨率；若提供参考图则保留该产品。",
        "enabled": True,
    },
    {
        "id": "ugc-lifestyle",
        "title": "UGC：生活化上身图",
        "description": "产出极具真实感的博主穿搭 / 上身图，贴近生活场景。",
        "category": "电商",
        "prompt": "生成一张 UGC 生活化产品图：真实素人随手拍质感、自然光、居家或街拍场景，产品自然融入生活、非棚拍摆拍、有真实生活气息；若提供参考图则保留该商品。",
        "enabled": True,
    },
    {
        "id": "ai-stylist",
        "title": "AI 造型师：高转化模特图",
        "description": "生成专业模特造型图，全方位展现商品潜力。",
        "category": "电商",
        "prompt": "生成一张高转化电商模特图：专业模特自然展示产品、棚拍柔光或精致生活场景、姿态自然有亲和力、构图突出产品；商业级质感；若提供参考图则保留该商品。",
        "enabled": True,
    },
    # ── 品牌（image-gen，产出一张图/拼版）──
    {
        "id": "web-to-inspiration",
        "title": "网页变灵感",
        "description": "把品牌 / 网站风格变成一张视觉灵感板(moodboard)。",
        "category": "品牌",
        "prompt": "生成一张品牌视觉灵感板(moodboard)：在一张图内拼贴呈现配色、版式、图形语言、字体与整体氛围参考，风格统一，可直接作为品牌视觉灵感。",
        "enabled": True,
    },
    {
        "id": "logo-and-brand",
        "title": "Logo 与品牌",
        "description": "为你的品牌生成 Logo 与周边应用的视觉呈现板。",
        "category": "品牌",
        "prompt": "生成一张品牌视觉呈现板：在一张图内整齐拼版展示主 Logo、品牌配色方案，以及名片与包装样机应用，风格统一、专业。",
        "enabled": True,
    },
    {
        "id": "product-marketing-set",
        "title": "产品营销组图",
        "description": "一张九宫格拼版，覆盖产品的多个营销场景。",
        "category": "品牌",
        "prompt": "生成一张产品营销组图拼版：在一张图内用整齐的 3x3 九宫格呈现同一产品的多个营销场景（使用场景 / 卖点特写 / 氛围图等），排版整洁、风格统一；若提供参考图则以该产品为主体。",
        "enabled": True,
    },
    {
        "id": "logo-design",
        "title": "Logo 设计",
        "description": "生成一张 Logo 设计提案板：主标志加多种应用变体拼版。",
        "category": "品牌",
        "prompt": "生成一张 Logo 设计提案板：在一张图内拼版展示一个主标志及其横版 / 竖版 / 单色 / 反白等应用变体，干净的浅色展示底、专业排版。",
        "enabled": True,
    },
    # ── 营销（image-gen，产出一张图）──
    {
        "id": "marketing-brochure",
        "title": "营销宣传册",
        "description": "设计活动、服务和产品推广的三折页宣传册版面。",
        "category": "营销",
        "prompt": "生成一张三折页营销宣传册的展开版面设计图：三栏式排版、含封面 / 正文 / 卖点区、图文混排、配色专业、平铺展示，可用于活动或产品推广。",
        "enabled": True,
    },
    # ── 工作室（image-gen，产出一张图）──
    {
        "id": "interior-design",
        "title": "室内设计",
        "description": "室内设计出图助手：生成写实空间效果图。",
        "category": "工作室",
        "prompt": "生成一张室内设计空间效果图：写实渲染、合理的空间布局与家具陈设、自然采光配合氛围灯光、材质质感真实、整体风格协调，可作为室内方案效果图。",
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
