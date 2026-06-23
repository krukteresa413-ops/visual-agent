"""
平台 Prompt 模板注入测试。
验证：平台模板正确加载 → _enrich_system 注入完整模板内容。
"""
import pytest

from app.services.platform_prompt_loader import (
    get_platform_context,
    load_platform_prompt,
    PLATFORM_TEMPLATES,
)
from app.services.visual_agent import VisualAgent


class TestPlatformContext:
    """get_platform_context 缩略版测试"""

    def test_taobao_context_includes_style(self):
        ctx = get_platform_context("taobao")
        assert "淘宝/天猫" in ctx

    def test_xiaohongshu_context_includes_name(self):
        ctx = get_platform_context("xiaohongshu")
        assert "小红书" in ctx
        assert "种草" in ctx or "生活方式" in ctx

    def test_douyin_context_includes_video(self):
        ctx = get_platform_context("douyin")
        assert "抖音" in ctx
        assert "9:16" in ctx or "竖版" in ctx

    def test_amazon_context_includes_white_bg(self):
        ctx = get_platform_context("amazon")
        assert "Amazon" in ctx
        assert "2000" in ctx

    def test_unknown_platform_returns_empty(self):
        ctx = get_platform_context("nonexistent_platform_xyz")
        assert ctx == ""


class TestPlatformPromptLoading:
    """load_platform_prompt 完整模板测试"""

    def test_load_taobao_template(self):
        prompt = load_platform_prompt("taobao", {})
        assert "淘宝/天猫" in prompt
        assert "800x800" in prompt
        assert "极限词" in prompt or "禁止" in prompt

    def test_load_xiaohongshu_template(self):
        prompt = load_platform_prompt("xiaohongshu", {})
        assert "小红书" in prompt
        assert "种草" in prompt
        assert "3:4" in prompt or "1080x1440" in prompt

    def test_load_douyin_template(self):
        prompt = load_platform_prompt("douyin", {})
        assert "抖音" in prompt
        assert "9:16" in prompt
        assert "前三秒" in prompt or "前3秒" in prompt or "黄金" in prompt

    def test_load_pinduoduo_template(self):
        prompt = load_platform_prompt("pinduoduo", {})
        assert "拼多多" in prompt
        assert "价格" in prompt

    def test_load_amazon_template(self):
        prompt = load_platform_prompt("amazon", {})
        assert "Amazon" in prompt
        assert "white background" in prompt.lower()

    def test_load_unknown_platform_returns_empty(self):
        prompt = load_platform_prompt("nonexistent_xyz", {})
        assert prompt == ""

    def test_all_mapped_platforms_have_templates(self):
        """验证 PLATFORM_TEMPLATES 中的每个平台都有对应的 .j2 文件"""
        from pathlib import Path

        prompt_dir = Path(__file__).parent.parent.parent / "app" / "prompts"
        mapped = set(PLATFORM_TEMPLATES.values())
        existing = {f.name for f in prompt_dir.glob("platform_*.j2")}
        missing = mapped - existing
        assert missing == set(), f"Missing template files: {missing}"

    def test_load_platform_prompt_with_brief_context(self):
        """模板渲染时可以安全接收 brief 上下文（即使模板不使用它）"""
        brief = {
            "product_name": "测试产品",
            "category": "测试品类",
        }
        prompt = load_platform_prompt("taobao", brief)
        assert "淘宝/天猫" in prompt


class TestSystemEnrichment:
    """_enrich_system 注入测试"""

    def test_enrich_system_injects_platform_template(self):
        """验证 _enrich_system 同时注入缩写 specs 和完整 .j2 模板"""
        enriched = VisualAgent._enrich_system("Base system prompt", "xiaohongshu")

        # 缩写 specs 中包含的
        assert "小红书" in enriched
        # 完整 .j2 模板独有的详细指导（缩写 specs 中没有）
        assert "痛点引入" in enriched or "1080x1440" in enriched, (
            "FAIL: 完整平台模板未注入！"
            "缩写 specs 不含'痛点引入→产品解决→效果展示'或'1080x1440px'等详细结构指导。"
            "需要修改 _enrich_system 使其也调用 load_platform_prompt()。"
        )

    def test_enrich_system_no_platform_returns_unchanged(self):
        base = "Base system prompt"
        result = VisualAgent._enrich_system(base, None)
        assert result == base

    def test_enrich_system_includes_template_content(self):
        """验证抖音模板的完整内容被注入"""
        enriched = VisualAgent._enrich_system("System", "douyin")

        # 缩写 specs 中包含的
        assert "抖音" in enriched
        # 完整 .j2 模板独有的详细指导（缩写 specs 中没有）
        assert "黄金5秒" in enriched or "小黄车" in enriched or "口播节奏" in enriched, (
            "FAIL: 抖音完整模板未注入！"
            "模板包含'黄金5秒'/'小黄车'/'口播节奏'等详细指导，但未被注入到系统提示中。"
        )
