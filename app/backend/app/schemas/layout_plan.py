"""
Layout Plan Schema — PRD Layout Agent 输出。

Layout Agent 职责（来自 MOYAG 设计文档）：
  中文排版、主副标题层级、详情页结构和尺寸适配。

输出结构化布局方案，指导前端渲染和设计师执行。
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator


# ── 通用元素定义 ──────────────────────────────────────────

class LayoutElement(BaseModel):
    """画布上的单个排版元素"""
    model_config = ConfigDict(from_attributes=True)

    element_type: Literal[
        "title", "subtitle", "body_text", "cta_button",
        "product_image", "scene_image", "logo", "badge",
        "divider", "price_tag", "selling_point_icon",
    ]
    content: str = ""                # 元素展示的文字内容
    # 位置 (百分比定位，便于跨尺寸适配)
    x_pct: float                     # 左上角 X，0-100
    y_pct: float                     # 左上角 Y，0-100
    width_pct: float                 # 宽度百分比
    height_pct: float                # 高度百分比
    font_size_pt: int = 14           # 字号
    font_weight: Literal["normal", "bold", "light"] = "normal"
    color: str = "#333333"           # 文字颜色
    alignment: Literal["left", "center", "right"] = "left"
    z_index: int = 1                 # 层级


# ── 各资产类型的布局方案 ──────────────────────────────────

class MainImageLayout(BaseModel):
    """主图排版 — 产品主视觉的标题/卖点/CTA 布局"""
    model_config = ConfigDict(from_attributes=True)
    asset_type: Literal["main_image_layout"] = "main_image_layout"

    canvas_width: int = 800
    canvas_height: int = 800
    background_color: str = "#ffffff"

    # 布局策略说明
    layout_strategy: str = ""        # 如 "中心产品+左上角品牌标+底部卖点条"
    title_hierarchy: str = ""        # 主副标题层级关系说明

    elements: List[LayoutElement] = []

    # 尺寸适配规则
    platform_adaptations: Optional[dict] = None
    # 例: {"taobao": {"canvas_width": 800, "canvas_height": 800},
    #       "xiaohongshu": {"canvas_width": 1080, "canvas_height": 1440, "elements_mod": "stacked"}}


class DetailPageLayout(BaseModel):
    """详情页排版 — A+ 内容 / 详情页的模块顺序和布局"""
    model_config = ConfigDict(from_attributes=True)
    asset_type: Literal["detail_page_layout"] = "detail_page_layout"

    canvas_width: int = 750          # 淘宝详情页宽
    canvas_height: int = 6000        # 无限长，这里给估值

    module_order: List[str] = []     # 模块排列顺序，如 ["hero_banner", "selling_points", "scene_showcase", "specs_table", "trust_badges", "cta"]
    modules: List["DetailPageModuleLayout"] = []

    platform_adaptations: Optional[dict] = None


class DetailPageModuleLayout(BaseModel):
    """详情页中的单个模块布局"""
    model_config = ConfigDict(from_attributes=True)
    module_name: str                 # "hero_banner", "selling_point_1", etc.
    height_px: int = 600
    background_color: str = "#ffffff"
    layout_type: Literal[
        "full_width_image", "left_image_right_text",
        "right_image_left_text", "three_column_grid",
        "text_only_centered", "before_after_compare",
    ]
    elements: List[LayoutElement] = []


class SellingPointModuleLayout(BaseModel):
    """卖点图模块排版 — 单个卖点的图文布局"""
    model_config = ConfigDict(from_attributes=True)
    asset_type: Literal["selling_point_layout"] = "selling_point_layout"

    canvas_width: int = 750
    canvas_height: int = 600

    icon_position: Literal["top", "left", "background"] = "left"
    text_alignment: Literal["left", "center", "right"] = "left"
    elements: List[LayoutElement] = []


class SceneImageLayout(BaseModel):
    """场景图排版 — 场景图中叠加的文字信息布局"""
    model_config = ConfigDict(from_attributes=True)
    asset_type: Literal["scene_image_layout"] = "scene_image_layout"

    canvas_width: int = 1024
    canvas_height: int = 1024

    text_overlay_position: Literal["bottom_strip", "top_left", "center_overlay", "none"] = "bottom_strip"
    elements: List[LayoutElement] = []


class SocialPostLayout(BaseModel):
    """社媒帖子排版 — 小红书/抖音/朋友圈等社媒封面布局"""
    model_config = ConfigDict(from_attributes=True)
    asset_type: Literal["social_post_layout"] = "social_post_layout"

    platform: str = "xiaohongshu"    # xiaohongshu / douyin / wechat_moments
    canvas_width: int = 1080
    canvas_height: int = 1440

    # 标题区
    title_area: Optional[str] = None  # "顶部大标题"
    # 图片区
    image_grid: Literal["single", "two_column", "three_grid", "carousel_indicator"] = "single"
    # 底部信息
    elements: List[LayoutElement] = []


# ── 总布局方案（一次包含多个资产类型） ──────────────────────

class LayoutPlan(BaseModel):
    """Layout Agent 的完整输出 — 覆盖所有资产类型的排版方案"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    platform_id: Optional[str] = None

    # 全局排版原则
    global_style_notes: str = ""     # 整体排版风格说明
    typography_rules: str = ""       # 中文字体/字号/行距规则
    color_system: str = ""           # 配色使用规则

    # 各资产布局
    main_image_layout: Optional[MainImageLayout] = None
    detail_page_layout: Optional[DetailPageLayout] = None
    selling_point_layouts: List[SellingPointModuleLayout] = []
    scene_image_layouts: List[SceneImageLayout] = []
    social_post_layout: Optional[SocialPostLayout] = None
