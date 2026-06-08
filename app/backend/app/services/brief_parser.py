"""
Brief Parser — PRD 8.1 增强版。
支持必需/推荐/可选字段三级分类，自动检测缺失字段并给出提示。
"""
import json
from typing import Optional
from app.services.llm_client import LLMClient

REQUIRED_FIELDS = ["product_name", "category", "specifications", "selling_points"]
RECOMMENDED_FIELDS = ["target_market", "usage_scenarios", "target_customer"]
OPTIONAL_FIELDS = ["brand_style", "compliance_notes", "materials"]

PARSE_SYSTEM_PROMPT = """你是一个精确的产品信息提取器。从文本中提取以下字段。

- product_name: 产品名称
- category: 品类
- specifications: 规格参数（数组）
- selling_points: 主要卖点（数组）
- target_market: 目标市场（数组）
- usage_scenarios: 使用场景（数组）
- target_customer: 目标客户（数组）
- materials: 材质（数组）
- brand_style: 品牌风格
- compliance_notes: 合规说明（数组）

找不到信息时对应值设为 null。只输出 JSON，不要输出其他内容。"""

PARSE_USER_TEMPLATE = """从以下文本提取产品信息：
---
{text}
---
严格输出 JSON："""

FIELD_HINTS = {
    "product_name": "例如：Commercial Chest Freezer",
    "category": "例如：Commercial Refrigeration",
    "specifications": "例如：300L, stainless steel, low noise",
    "selling_points": "例如：fast cooling, energy saving, OEM",
    "target_market": "例如：US, EU, Middle East",
    "usage_scenarios": "例如：supermarket, restaurant",
    "target_customer": "例如：supermarket buyer, distributor",
    "brand_style": "例如：professional, clean, industrial",
    "compliance_notes": "例如：CE certified",
    "materials": "例如：stainless steel",
}


LIST_FIELDS = [
    "specifications", "selling_points", "target_market",
    "usage_scenarios", "target_customer", "materials", "compliance_notes",
]


async def parse_brief_text(text: str, llm: Optional[LLMClient] = None) -> dict:
    """从自由文本提取结构化 ProductBrief，标注缺失字段。"""
    if llm is None:
        llm = LLMClient()

    raw = await llm.call(
        system_prompt=PARSE_SYSTEM_PROMPT,
        user_prompt=PARSE_USER_TEMPLATE.format(text=text),
        temperature=0.3,
    )

    # Normalize: list fields must never be None (protects Jinja2 templates)
    for field in LIST_FIELDS:
        if raw.get(field) is None:
            raw[field] = []

    missing = []
    for field in REQUIRED_FIELDS:
        val = raw.get(field)
        if val is None or val == "" or val == []:
            missing.append({"field": field, "level": "required", "hint": FIELD_HINTS.get(field, f"请填写 {field}")})

    for field in RECOMMENDED_FIELDS:
        val = raw.get(field)
        if val is None or val == "" or val == []:
            missing.append({"field": field, "level": "recommended", "hint": FIELD_HINTS.get(field, f"建议填写 {field}")})

    raw["missing_fields"] = missing
    return raw
