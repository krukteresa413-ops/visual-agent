"""
创意策略 Schema — "先出方向再出图" 的核心数据结构。
"""
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, ConfigDict


class SellingPointPriority(BaseModel):
    """卖点优先级排序"""
    rank: int
    point: str
    rationale: str


class VisualStrategy(BaseModel):
    """PRD 创意策略层输出 — 在生成素材前确定视觉方向"""

    model_config = ConfigDict(from_attributes=True)

    # 品牌定位
    visual_positioning: str

    # 目标客户画像（可选）
    target_customer_analysis: Optional[str] = None

    # 视觉风格方向
    visual_style: str

    # 卖点优先级排序
    selling_points_priority: List[SellingPointPriority]

    # 各素材类型的策略方向（可选）
    asset_plan_summary: Optional[Dict[str, str]] = None

    # 品牌语调
    brand_tone: str

    # 受众类型
    audience_type: Literal["B2B", "B2C"]

    # 核心差异化
    key_differentiators: str

    def to_context_string(self) -> str:
        """将策略序列化为可注入 prompt 的文本上下文"""
        lines = [
            f"## 创意策略上下文",
            f"品牌定位: {self.visual_positioning}",
            f"视觉风格: {self.visual_style}",
            f"品牌语调: {self.brand_tone}",
            f"受众类型: {self.audience_type}",
            f"核心差异化: {self.key_differentiators}",
        ]
        if self.target_customer_analysis:
            lines.append(f"目标客户: {self.target_customer_analysis}")
        if self.selling_points_priority:
            sp_lines = [
                f"  {sp.rank}. {sp.point} — {sp.rationale}"
                for sp in self.selling_points_priority
            ]
            lines.append(f"卖点优先级:\n" + "\n".join(sp_lines))
        if self.asset_plan_summary:
            lines.append(f"素材策略:")
            for asset_type, plan in self.asset_plan_summary.items():
                lines.append(f"  {asset_type}: {plan}")
        return "\n".join(lines)
