"""
结果导出服务。
PRD：支持复制 Markdown、导出文档。
Simplicity First：MVP 只做 Markdown。
"""
from typing import Any


def to_markdown(plan: dict) -> str:
    """将 VisualAssetPlan 转换为 Markdown 格式"""
    lines = []
    pid = plan.get("project_id", "")
    lines.append(f"# 视觉素材方案（Project {pid}）\n")

    # 主图方案
    lines.append("## 主图方案")
    mi = plan.get("main_image", {})
    if mi:
        _f(lines, "目标", mi.get("goal"))
        _f(lines, "构图", mi.get("composition"))
        _f(lines, "背景", mi.get("background"))
        _f(lines, "光影", mi.get("lighting"))
        _f(lines, "文案", mi.get("copywriting"))
        _f(lines, "图像Prompt", mi.get("prompt"), code=True)
        _f(lines, "禁用项", mi.get("negative_prompt"))
        _f(lines, "适配平台", mi.get("platform"))

    # 白底图方案
    lines.append("\n## 白底图方案")
    wb = plan.get("white_bg", {})
    if wb:
        _f(lines, "目标", wb.get("goal"))
        _f(lines, "处理指令", wb.get("instructions"))
        checklist = wb.get("quality_checklist", [])
        if checklist:
            lines.append("**质量检查项**")
            for item in checklist:
                lines.append(f"- {item}")

    # 场景图方案
    lines.append("\n## 场景图方案")
    scenes = plan.get("scene_images", [])
    if scenes:
        for i, s in enumerate(scenes, 1):
            lines.append(f"\n### 场景 {i}：{s.get('scene_name', '')}")
            _f(lines, "目标用户", s.get("target_user"))
            _f(lines, "场景叙事", s.get("scene_narrative"))
            elements = s.get("visual_elements", [])
            if elements:
                lines.append(f"**画面元素**：{', '.join(elements)}")
            _f(lines, "产品位置", s.get("product_position"))
            _f(lines, "图像Prompt", s.get("prompt"), code=True)
    else:
        lines.append("_（无场景图方案）_")

    # 卖点图模块
    lines.append("\n## 卖点图模块")
    sps = plan.get("selling_points", [])
    if sps:
        for i, sp in enumerate(sps, 1):
            lines.append(f"\n### 卖点 {i}：{sp.get('title', '')}")
            _f(lines, "文案", sp.get("description"))
            _f(lines, "视觉表现", sp.get("visual_representation"))
            _f(lines, "图标建议", sp.get("icon_suggestion"))
            _f(lines, "布局建议", sp.get("layout_suggestion"))
    else:
        lines.append("_（无卖点图模块）_")

    # 短视频脚本
    lines.append("\n## 短视频脚本")
    scripts = plan.get("video_scripts", [])
    if scripts:
        for s in scripts:
            dur = s.get("duration_seconds", "?")
            lines.append(f"\n### {dur}秒脚本")
            _f(lines, "视频目标", s.get("video_goal"))
            _f(lines, "CTA", s.get("cta"))
            _f(lines, "节奏", s.get("pacing"))
            material = s.get("material_requirements", [])
            if material:
                lines.append(f"**所需素材**：{', '.join(material)}")
            storyboard = s.get("storyboard", [])
            if storyboard:
                lines.append("\n**分镜**\n")
                lines.append("| 镜头 | 时长 | 画面 | 字幕 | 旁白 |")
                lines.append("|------|------|------|------|------|")
                for shot in storyboard:
                    lines.append(
                        f"| {shot.get('shot_number','')} | {shot.get('duration','')} | "
                        f"{shot.get('visual','')} | {shot.get('subtitle','')} | {shot.get('voiceover','')} |"
                    )
    else:
        lines.append("_（无短视频脚本）_")

    # 广告素材方案
    lines.append("\n## 广告素材方案")
    ad = plan.get("ad_material", {})
    if ad:
        _f(lines, "广告目标", ad.get("ad_goal"))
        _f(lines, "目标人群", ad.get("target_audience"))
        _f(lines, "切入角度", ad.get("ad_angle"))
        _f(lines, "开头钩子", ad.get("hook"), code=True)
        ksp = ad.get("key_selling_points", [])
        if ksp:
            lines.append(f"**核心卖点**：{', '.join(ksp)}")
        ml = ad.get("material_list", [])
        if ml:
            lines.append(f"**素材清单**：{', '.join(ml)}")
        _f(lines, "CTA", ad.get("cta"))
        _f(lines, "建议平台", ad.get("platform_suggestion"))

    return "\n".join(lines)


def _f(lines: list, label: str, value: Any, code: bool = False):
    if not value:
        return
    if code:
        lines.append(f"\n**{label}**\n```\n{value}\n```")
    else:
        lines.append(f"**{label}**：{value}")
