"""
Platform specifications for Chinese and international e-commerce/social platforms.
PRD 7.7 — 本土化平台适配
"""
PLATFORM_SPECS = {
    # ===== 国内电商平台 =====
    "taobao": {
        "name": "淘宝/天猫",
        "category": "电商",
        "main_image": {"width": 800, "height": 800, "format": "JPG/PNG", "max_size_kb": 500},
        "detail_page": {"width": 750, "max_height": "不限", "tips": "首屏突出卖点+场景图，信息密度适中"},
        "video": {"ratio": "1:1 或 16:9", "max_seconds": 60, "tips": "前3秒必须有钩子"},
        "style": "促销氛围适度，白底图干净，场景图真实感强",
        "文案风格": "直接有力，突出卖点和优惠，禁止极限词",
    },
    "jd": {
        "name": "京东",
        "category": "电商",
        "main_image": {"width": 800, "height": 800},
        "detail_page": {"width": 750, "tips": "偏品质感，信息结构化"},
        "style": "品质感强，偏理性消费，数据支撑卖点",
        "文案风格": "专业可信，突出参数和品质",
    },
    "pinduoduo": {
        "name": "拼多多",
        "category": "电商",
        "main_image": {"width": 800, "height": 800},
        "style": "强价格感，促销利益点突出，信息密度高，活动标签明显",
        "文案风格": "价格导向，利益点前置，口语化，紧迫感",
    },
    # ===== 国内社媒平台 =====
    "xiaohongshu": {
        "name": "小红书",
        "category": "社媒",
        "cover": {"width": 1080, "height": 1440, "ratio": "3:4"},
        "feed": {"width": 1080, "height": 1080, "ratio": "1:1"},
        "style": "生活方式感、真实体验、高审美、种草感强",
        "文案风格": "个人化口吻，真实体验分享，避免硬广感，标题有吸引力但不标题党",
    },
    "douyin": {
        "name": "抖音",
        "category": "社媒",
        "video_cover": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "feed": {"width": 1080, "height": 1920},
        "live_bg": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "style": "竖版优先、强钩子开头、节奏快、视觉冲击力强",
        "文案风格": "口语化、有网感、前3秒决定留存、商品卖点前置",
        "video": {"ratio": "9:16", "max_seconds": 60, "tips": "前3秒强钩子，黄金5秒转化"},
    },
    # ===== 微信生态 =====
    "wechat": {
        "name": "微信公众号",
        "category": "微信",
        "cover": {"width": 900, "height": 383, "ratio": "2.35:1"},
        "style": "信息清晰，适合手机阅读，品牌调性统一",
    },
    "video_hao": {
        "name": "视频号",
        "category": "微信",
        "cover": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "style": "竖版、社交感、真实感",
    },
    "pengyouquan": {
        "name": "朋友圈",
        "category": "微信",
        "poster": {"width": 1080, "height": 1080, "ratio": "1:1"},
        "long_image": {"width": 1080, "max_height": 20000},
        "style": "社交分享感，不过度商业化",
    },
    # ===== 本地生活 =====
    "meituan": {
        "name": "美团/大众点评",
        "category": "本地生活",
        "activity": {"width": 1080, "height": 720},
        "menu": {"width": 1080, "height": 1920},
        "style": "利益明确、食物诱人、活动信息清晰",
        "文案风格": "套餐信息前置，价格醒目，门店引导明确",
    },
    # ===== 国际平台 =====
    "alibaba": {
        "name": "阿里巴巴国际站/中国制造网",
        "category": "B2B",
        "main_image": {"width": 800, "height": 800},
        "style": "专业商务、产品为主、工厂实力展示",
    },
    "amazon": {
        "name": "Amazon",
        "category": "电商",
        "main_image": {"width": 2000, "height": 2000, "white_bg": True},
        "video": {"ratio": "16:9", "max_seconds": 60},
        "style": "白底主图纯净，场景图展示使用情境，A+内容结构化",
    },
    "shopify": {
        "name": "Shopify",
        "category": "独立站",
        "main_image": {"width": 2048, "height": 2048},
        "style": "品牌调性强，视觉统一",
    },
    "tiktok": {
        "name": "TikTok",
        "category": "社媒",
        "video": {"ratio": "9:16", "resolution": "1080x1920", "max_seconds": 60},
    },
    "meta": {
        "name": "Meta (FB/IG)",
        "category": "社媒",
        "feed_image": {"width": 1080, "height": 1080},
        "story": {"width": 1080, "height": 1920, "ratio": "9:16"},
    },
}

# ===== 行业场景模板 =====
INDUSTRY_SCENES = [
    {"id": "ecommerce_launch", "name": "电商上新", "icon": "🛍️", "desc": "淘宝/天猫/京东/拼多多新品发布套装", "platforms": ["taobao", "jd", "pinduoduo"]},
    {"id": "xiaohongshu_seed", "name": "小红书种草", "icon": "📕", "desc": "小红书封面+正文图+标题文案", "platforms": ["xiaohongshu"]},
    {"id": "douyin_short", "name": "抖音短视频", "icon": "🎵", "desc": "短视频分镜+封面+口播文案+直播间背景", "platforms": ["douyin"]},
    {"id": "restaurant", "name": "餐饮活动", "icon": "🍜", "desc": "门店海报+菜单+团购图+小红书种草", "platforms": ["meituan", "xiaohongshu", "pengyouquan"]},
    {"id": "local_life", "name": "本地生活推广", "icon": "📍", "desc": "美业/健身/教育/宠物店活动物料", "platforms": ["meituan", "xiaohongshu", "douyin"]},
    {"id": "brand_system", "name": "品牌视觉系统", "icon": "🎨", "desc": "Logo+色彩+字体+VI+包装概念", "platforms": ["taobao", "xiaohongshu"]},
    {"id": "packaging", "name": "包装设计", "icon": "📦", "desc": "产品包装概念+mockup+标签", "platforms": []},
    {"id": "festival", "name": "节日营销", "icon": "🎉", "desc": "节日海报+活动KV+社媒模板", "platforms": ["taobao", "xiaohongshu", "pengyouquan"]},
    {"id": "live_stream", "name": "直播间视觉", "icon": "📺", "desc": "直播间背景+贴片+优惠券图", "platforms": ["douyin", "taobao"]},
    {"id": "private_domain", "name": "私域朋友圈", "icon": "💬", "desc": "朋友圈海报+社群转发图+活动长图", "platforms": ["pengyouquan", "wechat"]},
]


def get_all_specs():
    return PLATFORM_SPECS


def get_platform_spec(platform_id: str) -> dict | None:
    return PLATFORM_SPECS.get(platform_id)


def get_all_scenes():
    return INDUSTRY_SCENES


def get_scene(scene_id: str) -> dict | None:
    for s in INDUSTRY_SCENES:
        if s["id"] == scene_id:
            return s
    return None


def get_size_recommendations(markets: list[str]) -> list[dict]:
    mapping = {
        "US": ["amazon", "meta", "tiktok"],
        "EU": ["amazon", "meta"],
        "Middle East": ["alibaba", "meta"],
        "Southeast Asia": ["shopify", "tiktok"],
        "Global": ["alibaba", "amazon"],
        "中国": ["taobao", "xiaohongshu", "douyin", "wechat"],
        "国内": ["taobao", "xiaohongshu", "douyin"],
    }
    recs = set()
    for m in markets:
        for mk, pl in mapping.items():
            if mk.lower() in m.lower():
                recs.update(pl)
    return [{"platform": p, **PLATFORM_SPECS.get(p, {})} for p in recs]
