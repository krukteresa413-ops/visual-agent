"""
中文合规检查服务。
检测：极限词（广告法禁用词）、敏感词、平台尺寸校验。
"""
from app.services.platform_specs import get_platform_spec

# 中国广告法禁用极限词
PROHIBITED_TERMS = [
    "最好", "最佳", "第一", "首个", "首选", "唯一",
    "顶级", "最高", "最低", "最便宜", "最先进",
    "全网最", "全国最", "全球最", "世界最",
    "国家级", "世界级", "最高级", "极品",
    "绝对", "独一无二", "万能", "完美",
    "100%", "百分百", "零风险", "无效退款",
    "永不", "永久", "史上最", "史无前例",
    "全网第一", "销量第一", "排名第一", "冠军",
    "王牌", "至尊", "巅峰", "无敌",
]

# 敏感词（含负面含义）
SENSITIVE_WORDS = [
    "假货", "山寨", "仿冒", "假冒",
    "劣质", "次品", "低劣",
    "骗人", "欺诈", "忽悠",
]

# 平台尺寸容差比例（允许的偏差）
SIZE_TOLERANCE = 0.05


class ComplianceChecker:
    """合规检查器"""

    @staticmethod
    def check_text(text: str) -> list[dict]:
        """检查文本中的违规词。返回违规列表。"""
        if not text:
            return []
        violations = []

        for term in PROHIBITED_TERMS:
            if term in text:
                violations.append({
                    "type": "prohibited_term",
                    "matched": term,
                    "suggestion": f"建议将「{term}」替换为客观描述，如「品质优良」「广受好评」等",
                })

        for word in SENSITIVE_WORDS:
            if word in text:
                violations.append({
                    "type": "sensitive_word",
                    "matched": word,
                    "suggestion": f"建议移除「{word}」相关表述",
                })

        return violations

    @staticmethod
    def check_brief(brief: dict) -> list[dict]:
        """检查整个 brief 的合规性。返回带字段名的违规列表。"""
        violations = []
        text_fields = [
            "product_name", "category", "brand_style",
        ]
        list_fields = [
            "specifications", "selling_points", "materials",
            "target_market", "target_customer", "usage_scenarios",
            "compliance_notes",
        ]

        for field in text_fields:
            value = brief.get(field)
            if isinstance(value, str):
                for v in ComplianceChecker.check_text(value):
                    violations.append({**v, "field": field})

        for field in list_fields:
            values = brief.get(field, [])
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, str):
                        for v in ComplianceChecker.check_text(item):
                            violations.append({**v, "field": field})

        return violations

    @staticmethod
    def validate_size(
        platform_id: str,
        asset_type: str,
        width: int,
        height: int,
    ) -> dict:
        """验证尺寸是否符合平台规范。返回 {valid: bool, message: str}。"""
        spec = get_platform_spec(platform_id)
        if not spec:
            return {"valid": True, "message": "未知平台，跳过尺寸校验"}

        # 查找对应素材类型的尺寸规范
        dims = None
        # 先精确匹配
        if asset_type in spec:
            dims = spec[asset_type]
        # 再试常见别名
        if not dims and asset_type == "cover":
            dims = spec.get("cover") or spec.get("feed") or spec.get("main_image")
        if not dims and asset_type == "video_cover":
            dims = spec.get("video_cover") or spec.get("video") or spec.get("story")
        if not dims:
            return {"valid": True, "message": f"平台 {platform_id} 未定义 {asset_type} 尺寸规范"}

        expected_w = dims.get("width")
        expected_h = dims.get("height")

        if expected_w and expected_h:
            w_ok = abs(width - expected_w) / expected_w <= SIZE_TOLERANCE
            h_ok = abs(height - expected_h) / expected_h <= SIZE_TOLERANCE
            ratio_ok = True
            # 如果指定了比例，校验比例
            if "ratio" in dims:
                expected_ratio = dims["ratio"]
                if expected_ratio == "1:1":
                    ratio_ok = width == height
                elif expected_ratio == "9:16":
                    ratio_ok = abs(width / height - 9 / 16) <= 0.02
                elif expected_ratio == "16:9":
                    ratio_ok = abs(width / height - 16 / 9) <= 0.02
                elif expected_ratio == "3:4":
                    ratio_ok = abs(width / height - 3 / 4) <= 0.02

            if w_ok and h_ok and ratio_ok:
                return {"valid": True, "message": ""}

            return {
                "valid": False,
                "message": (
                    f"尺寸不符：{platform_id} 的 {asset_type} 要求 "
                    f"{expected_w}x{expected_h}px"
                    + (f"（比例 {dims['ratio']}）" if "ratio" in dims else "")
                ),
            }

        return {"valid": True, "message": ""}
