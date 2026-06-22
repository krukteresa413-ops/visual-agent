"""Research templates — pre-built competitor and trend data per category+platform."""

TEMPLATES: dict = {
    "女装": {
        "taobao": {
            "competitors": ["ZARA", "优衣库", "UR", "伊芙丽"],
            "trends": ["法式复古", "多巴胺配色", "Y2K风格", "慵懒风"],
            "price_range": "79-299",
            "hot_topics": ["#穿搭分享", "#显瘦秘籍", "#OOTD"],
        },
        "xiaohongshu": {
            "competitors": ["ZARA", "优衣库", "COS", "toteme"],
            "trends": ["静奢风", "知识分子穿搭", "学院风", "新中式"],
            "price_range": "99-399",
            "hot_topics": ["#穿搭灵感", "#小众设计", "#配色参考"],
        },
        "douyin": {
            "competitors": ["ZARA", "UR", "CHUU", "白小T"],
            "trends": ["多巴胺穿搭", "Y2K辣妹", "慵懒松弛感", "职场穿搭"],
            "price_range": "49-199",
            "hot_topics": ["#变装挑战", "#一周穿搭", "#显高穿搭"],
        },
    },
    "美妆": {
        "taobao": {
            "competitors": ["完美日记", "花西子", "COLORKEY", "INTO YOU"],
            "trends": ["纯净美妆", "以油养肤", "早C晚A", "多巴胺妆"],
            "price_range": "29-199",
            "hot_topics": ["#平价好物", "#黄皮显白", "#持妆测评"],
        },
        "xiaohongshu": {
            "competitors": ["完美日记", "花西子", "酵色", "彩棠"],
            "trends": ["白开水妆", "纯欲风", "伪素颜", "国风彩妆"],
            "price_range": "39-299",
            "hot_topics": ["#妆容教程", "#化妆刷推荐", "#空瓶记"],
        },
        "douyin": {
            "competitors": ["完美日记", "花西子", "AKF", "方里"],
            "trends": ["氛围感妆容", "快速出门妆", "瑕疵皮遮瑕", "爆改妆"],
            "price_range": "19-159",
            "hot_topics": ["#化妆前后", "#美妆测评", "#新手化妆"],
        },
    },
    "食品": {
        "taobao": {
            "competitors": ["三只松鼠", "良品铺子", "百草味", "王小卤"],
            "trends": ["健康零食", "低GI代餐", "国潮包装", "便携装"],
            "price_range": "9.9-99",
        },
        "xiaohongshu": {
            "competitors": ["三只松鼠", "OATLY", "简爱", "每日黑巧"],
            "trends": ["超级食物", "植物基", "低卡零食", "高蛋白"],
            "price_range": "19.9-129",
        },
        "douyin": {
            "competitors": ["三只松鼠", "良品铺子", "锋味派", "满小饱"],
            "trends": ["直播间爆款", "大包装囤货", "地域美食", "办公室零食"],
            "price_range": "9.9-69",
        },
    },
    "3C数码": {
        "taobao": {
            "competitors": ["小米", "华为", "OPPO", "Anker"],
            "trends": ["氮化镓充电", "透明探索版", "磁吸生态", "主动降噪"],
            "price_range": "49-999",
        },
        "xiaohongshu": {
            "competitors": ["苹果", "小米", "Dyson", "Marshall"],
            "trends": ["桌搭美学", "极简桌面", "复古科技", "粉色数码"],
            "price_range": "99-1999",
        },
        "douyin": {
            "competitors": ["小米", "华为", "倍思", "品胜"],
            "trends": ["性价比之王", "学生党必备", "黑科技", "开箱测评"],
            "price_range": "29-499",
        },
    },
    "家居": {
        "taobao": {
            "competitors": ["宜家", "NOME", "网易严选", "源氏木语"],
            "trends": ["奶油风", "原木风", "收纳神器", "智能家居"],
            "price_range": "29-999",
        },
        "xiaohongshu": {
            "competitors": ["宜家", "MUJI", "HAY", "梵几"],
            "trends": ["法式奶油风", "侘寂风", "多巴胺家居", "租房改造"],
            "price_range": "49-1999",
        },
        "douyin": {
            "competitors": ["宜家", "网易严选", "梦百合", "林氏木业"],
            "trends": ["沉浸式回家", "一镜到底", "收纳挑战", "老房改造"],
            "price_range": "19-599",
        },
    },
}

DEFAULT_TEMPLATE: dict = {
    "competitors": ["行业领先品牌A", "新锐品牌B", "性价比品牌C"],
    "trends": ["品质升级", "年轻化设计", "社交传播"],
    "price_range": "根据行业调整",
}


def match_template(category: str, platform: str) -> dict:
    """Match a pre-built research template by category and platform.

    Falls back to generic template if category or platform is unknown.
    """
    cat_data = TEMPLATES.get(category)
    if not cat_data:
        return {"category": f"通用（{category}）", **DEFAULT_TEMPLATE}

    plat_data = cat_data.get(platform)
    if not plat_data:
        return {"category": category, "platform": f"通用（{platform}）", **DEFAULT_TEMPLATE}

    return {"category": category, "platform": platform, **plat_data}
