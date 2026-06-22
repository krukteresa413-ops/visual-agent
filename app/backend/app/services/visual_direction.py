"""
Visual Direction service - pure logic implementation.
"""


class VisualDirection:
    """视觉方向服务：提取风格参数、生成 Moodboard、检查一致性。"""

    def extract_style_params(self, brief: dict) -> dict:
        """从 brief 提取风格参数，包含配色方案和风格关键词。"""
        brand_style = brief.get("brand_style", "")
        keywords = [k.strip() for k in brand_style.split("/") if k.strip()]
        
        # 根据风格关键词推断主色调
        primary_color = "#2d5a27"  # 默认自然绿
        if any(k in brand_style for k in ["自然", "禅意", "东方"]):
            primary_color = "#2d5a27"
        
        return {
            "primary_color": primary_color,
            "secondary_color": "#e8d5b7",
            "style_keywords": keywords if keywords else ["简约", "现代"],
            "typography": "serif",
            "composition": "centered",
        }

    def build_moodboard_context(self, style_params: dict) -> str:
        """构建 Moodboard 上下文，包含配色、字体、构图三部分。"""
        return f"""配色方案：
主色：{style_params['primary_color']}
辅色：{style_params.get('secondary_color', 'N/A')}

字体：{style_params.get('typography', 'sans-serif')}

构图：{style_params.get('composition', 'balanced')}"""

    def check_consistency(self, style_params: dict, asset_description: str) -> dict:
        """检查资产描述与风格参数的一致性。"""
        desc_lower = asset_description.lower()
        keywords = [k.lower() for k in style_params.get("style_keywords", [])]
        
        # 检测明显不匹配的风格词
        mismatch_keywords = ["赛博朋克", "霓虹", "大红色", "cyberpunk"]
        has_mismatch = any(k in desc_lower for k in mismatch_keywords)
        
        # 检测匹配的风格词
        has_match = any(k in desc_lower for k in keywords)
        
        if has_mismatch:
            return {
                "consistent": False,
                "warnings": ["风格描述与预期风格不符"],
            }
        
        return {
            "consistent": True,
            "warnings": [],
        }
