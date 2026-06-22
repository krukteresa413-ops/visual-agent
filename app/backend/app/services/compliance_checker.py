"""Chinese platform compliance checker. PRD 7.4 Agent 10."""
import re

# 极限词 — 广告法禁用的绝对化用语
FORBIDDEN_WORDS = {
    "最", "第一", "唯一", "独家", "首选", "顶级", "极致", "全网",
    "全国", "全球", "国家级", "世界级", "最高", "最低", "最佳",
    "最大", "最小", "最好", "最便宜", "绝对", "百分百", "100%",
    "永不", "永久", "万能", "零风险", "无效退款", "彻底",
}

# 敏感行业表述
SENSITIVE_PATTERNS = [
    (r"(治疗|治愈|根治|康复|疗程)", "医疗功效表述"),
    (r"(美白|祛斑|祛痘|抗皱|紧致|瘦脸|减肥|瘦身|丰胸)", "化妆品功效过度表述"),
    (r"(收益|回报率|保本|稳赚|翻倍|暴富)", "金融投资承诺"),
    (r"(包过|保过|签约|提分|升学)", "教育培训承诺"),
]

# 平台尺寸校验
PLATFORM_DIMENSIONS = {
    "taobao": {"main_image": (800, 800)},
    "amazon": {"main_image": (2000, 2000)},
    "xiaohongshu": {"cover": (1080, 1440)},
    "douyin": {"video_cover": (1080, 1920)},
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

    # 3. 平台尺寸提示
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
