from app.services.llm_client import LLMClient
import json

INSPIRATION_SYSTEM_PROMPT = """设计灵感搜索助手。基于产品信息生成5-8个视觉灵感方向。
每个灵感包含: inspiration_title, description, reference_keywords(Pinterest/Dribbble搜索词), visual_style, applicable_to(适用素材类型), example_brands(1-2个参考品牌), is_ad_example
直接输出JSON数组"""

async def search_inspiration(query: str, product_name: str = '', category: str = '') -> list:
    llm = LLMClient()
    user_prompt = f"""搜索:{query} 产品:{product_name} 品类:{category}
生成5-8个灵感+1-2个广告示例"""
    raw = await llm.call(system_prompt=INSPIRATION_SYSTEM_PROMPT, user_prompt=user_prompt)
    if isinstance(raw, list): return raw
    return [raw]
