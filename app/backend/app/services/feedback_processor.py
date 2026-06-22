"""Feedback Processor — natural language feedback to modification actions."""
from typing import Dict


# Keyword → action mapping
STYLE_KEYWORDS = {
    "年轻": ("modify_style", "年轻化"),
    "高级": ("enhance_quality", "高级感"),
    "简约": ("modify_style", "简约"),
    "活泼": ("modify_style", "活泼"),
    "温馨": ("modify_style", "温馨"),
}

CONTENT_KEYWORDS = {
    "背景": ("modify_background", None),
    "颜色": ("modify_color", None),
    "文字": ("modify_text", None),
    "文案": ("modify_text", None),
    "标题": ("modify_title", None),
    "logo": ("modify_logo", None),
}

ACTION_KEYWORDS = {
    "换成": "modify",
    "改": "modify",
    "变体": "generate_variant",
    "同风格": "generate_variant",
    "生成": "regenerate",
    "重新": "regenerate",
}

ELEMENT_KEYWORDS = {
    "标题": "title",
    "字号": "title",
    "颜色": "color",
    "背景": "background",
    "排版": "layout",
    "布局": "layout",
    "字体": "font",
    "文案": "copy",
    "logo": "logo",
}


class FeedbackProcessor:
    """Process natural language feedback into structured modification actions."""

    def process(self, feedback: str, asset_context: Dict) -> Dict:
        """Parse feedback and return modification action."""
        result = {
            "action": "regenerate",
            "target": feedback,
            "element": None,
            "count": 1,
        }

        # 1. Check content keywords first (lower priority)
        for keyword, (action, _) in CONTENT_KEYWORDS.items():
            if keyword in feedback:
                result["action"] = action
                result["target"] = feedback
                break

        # 2. Style keywords override content (higher priority)
        for keyword, (action, target) in STYLE_KEYWORDS.items():
            if keyword in feedback:
                result["action"] = action
                result["target"] = target or feedback
                break

        # 3. Action keywords (highest priority)
        for keyword, action in ACTION_KEYWORDS.items():
            if keyword in feedback:
                if action == "generate_variant":
                    result["action"] = action
                    result["count"] = 3
                elif action == "regenerate":
                    result["action"] = action
                break

        # 4. Detect target element (independent of action)
        for keyword, element in ELEMENT_KEYWORDS.items():
            if keyword in feedback:
                result["element"] = element
                break

        return result
