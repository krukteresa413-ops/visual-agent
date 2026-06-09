"""
中文合规检查测试。
验证：极限词检测 / 敏感词过滤 / 平台尺寸校验。
"""
import pytest

from app.services.compliance import (
    ComplianceChecker,
    PROHIBITED_TERMS,
    SENSITIVE_WORDS,
)


class TestProhibitedTerms:
    """极限词检测 — 中国广告法禁用词"""

    def test_detects_prohibited_term(self):
        result = ComplianceChecker.check_text("这是我们最好的产品")
        violations = [v for v in result if v["type"] == "prohibited_term"]
        assert len(violations) > 0
        assert any("最好" in v["matched"] for v in violations)

    def test_detects_number_one(self):
        result = ComplianceChecker.check_text("行业第一的品牌")
        violations = [v for v in result if v["type"] == "prohibited_term"]
        assert len(violations) > 0
        assert any("第一" in v["matched"] for v in violations)

    def test_detects_top_level(self):
        result = ComplianceChecker.check_text("顶级品质，全网最佳")
        violations = [v for v in result if v["type"] == "prohibited_term"]
        # Should match at least "顶级" and "最佳"
        assert len(violations) >= 2

    def test_clean_text_no_violations(self):
        result = ComplianceChecker.check_text("这款产品质量可靠，性能稳定")
        violations = [v for v in result if v["type"] == "prohibited_term"]
        assert len(violations) == 0

    def test_empty_text(self):
        result = ComplianceChecker.check_text("")
        assert result == []

    def test_prohibited_terms_list_not_empty(self):
        """验证禁用词列表非空"""
        assert len(PROHIBITED_TERMS) >= 10


class TestSensitiveWords:
    """敏感词过滤"""

    def test_detects_sensitive_word(self):
        result = ComplianceChecker.check_text("假货泛滥的产品")
        violations = [v for v in result if v["type"] == "sensitive_word"]
        assert len(violations) > 0

    def test_clean_text_no_sensitive(self):
        result = ComplianceChecker.check_text("优质产品，品质保证")
        violations = [v for v in result if v["type"] == "sensitive_word"]
        assert len(violations) == 0

    def test_sensitive_words_list_not_empty(self):
        assert len(SENSITIVE_WORDS) >= 5


class TestSizeValidation:
    """平台尺寸校验"""

    def test_valid_taobao_main_image_size(self):
        result = ComplianceChecker.validate_size("taobao", "main_image", 800, 800)
        assert result["valid"] is True

    def test_invalid_taobao_main_image_size(self):
        result = ComplianceChecker.validate_size("taobao", "main_image", 400, 300)
        assert result["valid"] is False
        assert "800" in result.get("message", "")

    def test_valid_xiaohongshu_cover(self):
        result = ComplianceChecker.validate_size("xiaohongshu", "cover", 1080, 1440)
        assert result["valid"] is True

    def test_invalid_xiaohongshu_ratio(self):
        result = ComplianceChecker.validate_size("xiaohongshu", "cover", 1080, 1080)
        assert result["valid"] is False

    def test_unknown_platform_returns_valid(self):
        """未知平台不阻塞"""
        result = ComplianceChecker.validate_size("unknown_platform", "main_image", 100, 100)
        assert result["valid"] is True  # 未知平台宽松处理

    def test_douyin_video_ratio(self):
        result = ComplianceChecker.validate_size("douyin", "video_cover", 1080, 1920)
        assert result["valid"] is True


class TestBriefCompliance:
    """Brief 级别的合规检查"""

    def test_brief_with_prohibited_terms_flagged(self):
        brief = {
            "product_name": "最好的冷柜",
            "category": "Refrigeration",
            "specifications": ["300L"],
            "selling_points": ["行业第一的制冷速度", "顶级品质"],
        }
        result = ComplianceChecker.check_brief(brief)
        assert len(result) >= 2  # "最好" + "第一" + "顶级"

    def test_clean_brief_no_flags(self):
        brief = {
            "product_name": "商用冷柜",
            "category": "Refrigeration",
            "specifications": ["300L"],
            "selling_points": ["快速制冷", "节能省电"],
        }
        result = ComplianceChecker.check_brief(brief)
        assert len(result) == 0

    def test_check_brief_returns_structured_violations(self):
        brief = {"product_name": "全网最好的产品"}
        result = ComplianceChecker.check_brief(brief)
        for v in result:
            assert "field" in v
            assert "type" in v
            assert "matched" in v
            assert "suggestion" in v
