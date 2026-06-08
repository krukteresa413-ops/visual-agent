"""Markdown 导出服务。从 DB 读取 visual_asset_plan，生成可读 Markdown 文档。"""
import json
from sqlalchemy.orm import Session
from app.db.crud_visual_asset import get_visual_asset_plan_by_project


def export_to_markdown(db: Session, project_id: int) -> str | None:
    plan = get_visual_asset_plan_by_project(db, project_id)
    if not plan:
        return None

    main = json.loads(plan.main_image_json)
    white = json.loads(plan.white_bg_json)
    scenes = json.loads(plan.scene_images_json)
    points = json.loads(plan.selling_points_json)
    scripts = json.loads(plan.video_scripts_json)
    ad = json.loads(plan.ad_material_json)

    lines = []
    lines.append("# 视觉素材方案")
    lines.append(f"项目 ID: {plan.project_id}  |  生成时间: {plan.created_at.strftime('%Y-%m-%d %H:%M') if plan.created_at else 'N/A'}")
    lines.append("")

    # 主图
    lines.append("## 主图方案")
    lines.append(f"- **目标**: {main.get('goal', '')}")
    lines.append(f"- **构图**: {main.get('composition', '')}")
    lines.append(f"- **背景**: {main.get('background', '')}")
    if main.get('lighting'):
        lines.append(f"- **光影**: {main['lighting']}")
    if main.get('copywriting'):
        lines.append(f"- **文案**: {main['copywriting']}")
    lines.append(f"- **Prompt**: `{main.get('prompt', '')}`")
    if main.get('negative_prompt'):
        lines.append(f"- **禁用项**: {main['negative_prompt']}")
    if main.get('platform'):
        lines.append(f"- **平台**: {main['platform']}")
    lines.append("")

    # 白底图
    lines.append("## 白底图方案")
    lines.append(f"- **目标**: {white.get('goal', '')}")
    lines.append(f"- **指令**: {white.get('instructions', '')}")
    if white.get('quality_checklist'):
        lines.append(f"- **质量检查**: {', '.join(white['quality_checklist'])}")
    lines.append("")

    # 场景图
    lines.append("## 场景图方案")
    for i, s in enumerate(scenes):
        lines.append(f"### 场景 {i+1}: {s.get('scene_name', '')}")
        lines.append(f"- **目标用户**: {s.get('target_user', '')}")
        lines.append(f"- **描述**: {s.get('scene_narrative', '')}")
        lines.append(f"- **画面元素**: {', '.join(s.get('visual_elements', []))}")
        lines.append(f"- **产品位置**: {s.get('product_position', '')}")
        lines.append(f"- **Prompt**: `{s.get('prompt', '')}`")
        if s.get('negative_prompt'):
            lines.append(f"- **禁用项**: {s['negative_prompt']}")
        lines.append("")

    # 卖点图
    lines.append("## 卖点图模块")
    for i, p in enumerate(points):
        lines.append(f"### 卖点 {i+1}: {p.get('title', '')}")
        lines.append(f"- **描述**: {p.get('description', '')}")
        lines.append(f"- **视觉表现**: {p.get('visual_representation', '')}")
        lines.append(f"- **图标**: {p.get('icon_suggestion', '')}")
        lines.append(f"- **布局**: {p.get('layout_suggestion', '')}")
        lines.append("")

    # 视频脚本
    lines.append("## 短视频脚本")
    for i, v in enumerate(scripts):
        lines.append(f"### 脚本 {i+1}: {v.get('video_goal', '')} ({v.get('duration_seconds', '')}s)")
        lines.append(f"- **CTA**: {v.get('cta', '')}")
        lines.append(f"- **节奏**: {v.get('pacing', '')}")
        lines.append(f"- **所需素材**: {', '.join(v.get('material_requirements', []))}")
        lines.append(f"- **分镜**:")
        for shot in v.get('storyboard', []):
            lines.append(f"  - {shot.get('duration', '')}: {shot.get('visual', '')} | {shot.get('subtitle', '')}")
        lines.append("")

    # 广告素材
    lines.append("## 广告素材方案")
    lines.append(f"- **广告目标**: {ad.get('ad_goal', '')}")
    lines.append(f"- **目标人群**: {ad.get('target_audience', '')}")
    lines.append(f"- **切入角度**: {ad.get('ad_angle', '')}")
    lines.append(f"- **钩子**: {ad.get('hook', '')}")
    lines.append(f"- **卖点**: {', '.join(ad.get('key_selling_points', []))}")
    lines.append(f"- **CTA**: {ad.get('cta', '')}")
    lines.append(f"- **建议平台**: {ad.get('platform_suggestion', '')}")
    lines.append(f"- **素材清单**: {', '.join(ad.get('material_list', []))}")
    lines.append(f"- **镜头顺序**: {' → '.join(ad.get('shot_sequence', []))}")

    return '\n'.join(lines)
