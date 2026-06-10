"""
Layout Agent — PRD 多 Agent 编排中的独立 Layout Agent。

职责（来自 MOYAG 设计文档）：
  - 中文排版（中文字体选择、字号层级、行距行高）
  - 主副标题层级（主标/副标/正文的视觉层级关系）
  - 详情页结构（模块排列顺序和布局类型）
  - 尺寸适配（跨平台尺寸转换规则）

输出：LayoutPlan — 像素级排版方案，可供前端 Canvas 渲染。
"""
from app.services.llm_client import LLMClient
from app.schemas.layout_plan import LayoutPlan
from app.schemas.visual_assets import VisualAssetPlanOut


LAYOUT_SYSTEM_PROMPT = """你是一位资深中文版式设计师（Layout Designer），专精电商和社媒视觉排版。

## 你的任务
根据产品信息、已生成的视觉素材方案、平台规格，生成完整的排版布局方案。

## 中文排版规则（必须遵守）
1. **字号层级**：主标题 28-48pt → 副标题 18-24pt → 正文 12-16pt → 注释 10-12pt
2. **行距**：标题 1.2 倍行距，正文 1.5-1.8 倍行距
3. **字体建议**：主标题用粗体（思源黑体 Bold/苹方 Bold），正文用常规（思源黑体 Regular/苹方 Regular）
4. **对齐**：中文优先左对齐或居中，避免两端对齐（会导致字符间距不均）
5. **留白**：四周边距 ≥ 8%，元素间距 ≥ 4%

## 电商排版模式（常用布局）
- **主图**：中心产品 + 左上品牌标 + 底部卖点条 + 右下 CTA
- **详情页**：首屏大图 → 卖点模块（左图右文/右图左文交替）→ 场景展示 → 规格参数 → 信任背书 → CTA
- **卖点模块**：图标(左) + 标题 + 说明文字(右)，或图标(上) + 文字(下)
- **社媒帖子**：顶部大标题 → 中间主图区 → 底部品牌信息

## 尺寸适配规则
- 淘宝/天猫主图：800×800，方图
- 小红书封面：1080×1440（3:4 竖版）
- 抖音/快手封面：1080×1920（9:16 竖版）
- Amazon 主图：2000×2000，纯白底
- 微信朋友圈：1080×1260

## 输出格式
严格输出以下 JSON，不要任何额外文字：
{
  "global_style_notes": "整体排版风格说明",
  "typography_rules": "字体层级/行距规则",
  "color_system": "配色使用规则",
  "main_image_layout": {
    "canvas_width": 800, "canvas_height": 800, "background_color": "#ffffff",
    "layout_strategy": "布局策略描述",
    "title_hierarchy": "标题层级说明",
    "elements": [
      {"element_type": "title", "content": "主标题", "x_pct": 5, "y_pct": 5, "width_pct": 90, "height_pct": 12, "font_size_pt": 36, "font_weight": "bold", "color": "#1a1a2e", "alignment": "left", "z_index": 10}
    ]
  },
  "detail_page_layout": {
    "canvas_width": 750, "canvas_height": 6000,
    "module_order": ["hero_banner", "selling_point_1", "scene_showcase", "specs", "trust", "cta"],
    "modules": [
      {"module_name": "hero_banner", "height_px": 600, "background_color": "#f5f0e8", "layout_type": "full_width_image", "elements": []}
    ]
  },
  "selling_point_layouts": [],
  "scene_image_layouts": [],
  "social_post_layout": null
}
"""

LAYOUT_USER_TEMPLATE = """## 产品信息
产品名：{product_name}
品类：{category}
卖点：{selling_points}
目标市场：{target_market}
目标客户：{target_customer}
品牌风格：{brand_style}

## 已生成的素材方案
{asset_plan_summary}

## 目标平台
{platform_context}

## 品牌配色
{brand_colors}

请生成完整排版布局方案。"""


class LayoutAgent:
    """排版 Agent — 独立 LLM 调用，生成 LayoutPlan。"""

    def __init__(self):
        self._llm = LLMClient()

    @staticmethod
    def _sanitize_field(value, max_len=200):
        s = str(value)[:max_len]
        s = s.replace("<", "&lt;").replace(">", "&gt;")
        return s


    async def generate_layout(
        self,
        project_id: int,
        brief: dict,
        asset_plan: dict,
        platform_id: str | None = None,
        brand_context: str | None = None,
    ) -> LayoutPlan:
        """根据产品信息和素材方案生成排版布局。"""

        # 构建素材方案摘要（避免 token 过长）
        asset_summary = _summarize_asset_plan(asset_plan)

        # 提取品牌配色
        brand_colors = brand_context or "使用默认配色方案（#333 文字 / #fff 背景 / #1a73e8 强调色）"

        # 平台上下文
        platform_context = _get_platform_layout_context(platform_id)

        user_prompt = LAYOUT_USER_TEMPLATE.format(
            product_name=LayoutAgent._sanitize_field(brief.get("product_name", "")),
            category=LayoutAgent._sanitize_field(brief.get("category", "")),
            selling_points=LayoutAgent._sanitize_field(", ".join(brief.get("selling_points", []))),
            target_market=LayoutAgent._sanitize_field(", ".join(brief.get("target_market", []))),
            target_customer=LayoutAgent._sanitize_field(", ".join(brief.get("target_customer", []))),
            brand_style=LayoutAgent._sanitize_field(brief.get("brand_style", "professional")),
            asset_plan_summary=asset_summary,
            platform_context=platform_context,
            brand_colors=brand_colors,
        )

        raw = await self._llm.call(
            system_prompt=LAYOUT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.5,
        )

        raw["project_id"] = project_id
        raw["platform_id"] = platform_id
        return LayoutPlan(**raw)


# ── 辅助函数 ──────────────────────────────────────────────

def _summarize_asset_plan(plan: dict) -> str:
    """将完整的 asset_plan 压缩为摘要，减少 token 消耗。"""
    lines = []

    mi = plan.get("main_image", {})
    if mi:
        lines.append(
            f"主图: goal={mi.get('goal','')}, "
            f"构图={mi.get('composition','')}, "
            f"文案={mi.get('copywriting','')}, "
            f"prompt={mi.get('prompt','')[:200]}"
        )

    scenes = plan.get("scene_images", [])
    for i, s in enumerate(scenes[:3]):
        lines.append(
            f"场景图{i+1}: 场景={s.get('scene','')}, "
            f"prompt={s.get('prompt','')[:150]}"
        )

    sps = plan.get("selling_points", [])
    for i, sp in enumerate(sps[:5]):
        lines.append(
            f"卖点{i+1}: 标题={sp.get('title','')}, "
            f"描述={sp.get('description','')[:100]}"
        )

    vs = plan.get("video_scripts", [])
    for i, v in enumerate(vs[:2]):
        lines.append(f"视频{i+1}: {v.get('video_goal','')[:100]}")

    ad = plan.get("ad_material", {})
    if ad:
        lines.append(f"广告: headline={ad.get('headline','')[:100]}")

    return "\n".join(lines)


def _get_platform_layout_context(platform_id: str | None) -> str:
    """返回平台排版约束。"""
    if not platform_id:
        return "通用电商排版，默认 750px 宽 + 方图"

    specs = {
        "taobao": "淘宝天猫：主图 800×800 方图，详情页 750px 宽，信息密度适中",
        "jd": "京东：主图 800×800，风格偏品质感，信息结构化",
        "pinduoduo": "拼多多：主图 800×800，信息密度高，强调价格和促销",
        "xiaohongshu": "小红书：封面 1080×1440 竖版 3:4，标题大且醒目，种草风",
        "douyin": "抖音：封面 1080×1920 竖版 9:16，前3秒视觉钩子，口语化",
        "amazon": "Amazon：主图 2000×2000 纯白底，无文字无Logo，产品占85%",
        "alibaba": "Alibaba：主图 1000×1000，可带少量文字，专业工业风",
        "shopify": "Shopify：主图 2048×2048，纯白底，无装饰",
    }
    return specs.get(platform_id, f"目标平台 {platform_id}，按通用电商排版")
