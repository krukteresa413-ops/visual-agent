"""Chinese platform compliance checker. PRD 7.4 Agent 10."""
import re

# 极限词 — 广告法禁用的绝对化用语
# 注:单字「最」「第一」会子串命中「最优」「全国第一」等,无需逐一列举。
FORBIDDEN_WORDS = {
    "最", "第一", "唯一", "独家", "首选", "顶级", "极致", "全网",
    "全国", "全球", "国家级", "世界级", "最高", "最低", "最佳",
    "最大", "最小", "最好", "最便宜", "绝对", "百分百", "100%",
    "永不", "永久", "万能", "零风险", "无效退款", "彻底",
    # 借零件 #1:从原型 compliance.ts 补充
    "极品", "首个", "冠军", "之王", "巅峰", "顶峰", "史无前例",
    "前无古人", "绝无仅有", "完美", "永远", "王牌", "尖端",
}

# 敏感行业表述
SENSITIVE_PATTERNS = [
    (r"(治疗|治愈|根治|根除|康复|疗程|疗效|药到病除|包治|痊愈|医效)", "医疗功效表述"),
    (r"(美白|祛斑|祛痘|抗皱|紧致|瘦脸|减肥|瘦身|丰胸)", "化妆品功效过度表述"),
    (r"(收益|回报率|保本|保收益|稳赚|翻倍|暴富|必赚)", "金融投资承诺"),
    (r"(包过|保过|签约|提分|升学|必中|保证录取)", "教育培训承诺"),
]

# 平台尺寸校验
PLATFORM_DIMENSIONS = {
    "taobao": {"main_image": (800, 800)},
    "amazon": {"main_image": (2000, 2000)},
    "xiaohongshu": {"cover": (1080, 1440)},
    "douyin": {"video_cover": (1080, 1920)},
}

# 平台敏感词 — 导流/作弊类,触发平台限流(借零件 #1:原型 PLATFORM_SENSITIVE)
PLATFORM_SENSITIVE_WORDS = {
    "xiaohongshu": ["加微信", "微信号", "私聊", "二维码", "外链"],
    "douyin": ["加微信", "外链"],
    "taobao": ["好评返现", "刷单"],
}


def check_compliance(text: str, platform_id: str | None = None) -> dict:
    """检查文案和平台合规性。返回违规项列表。"""
    violations = []

    # 1. 极限词检查
    for word in FORBIDDEN_WORDS:
        if word in text:
            violations.append({
                "type": "forbidden_word",
                "word": word,
                "severity": "high",
                "suggestion": f"删除或替换「{word}」，使用客观描述代替",
            })

    # 2. 敏感表述检查
    for pattern, category in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            violations.append({
                "type": "sensitive_claim",
                "match": m,
                "category": category,
                "severity": "high",
                "suggestion": f"避免{category}，删去或弱化相关表述",
            })

    # 3. 平台敏感词检查(导流/作弊词,易被限流)
    if platform_id and platform_id in PLATFORM_SENSITIVE_WORDS:
        for word in PLATFORM_SENSITIVE_WORDS[platform_id]:
            if word in text:
                violations.append({
                    "type": "platform_sensitive_word",
                    "word": word,
                    "platform": platform_id,
                    "severity": "medium",
                    "suggestion": f"{platform_id} 平台敏感词「{word}」，可能被限流，建议移除",
                })

    # 4. 平台尺寸提示
    if platform_id and platform_id in PLATFORM_DIMENSIONS:
        dims = PLATFORM_DIMENSIONS[platform_id]
        violations.append({
            "type": "platform_dimension",
            "platform": platform_id,
            "required": dims,
            "severity": "info",
            "suggestion": f"确保生成图片符合{dims}尺寸要求",
        })

    return {
        "compliant": len([v for v in violations if v["severity"] == "high"]) == 0,
        "violations": violations,
        "platform": platform_id,
    }
