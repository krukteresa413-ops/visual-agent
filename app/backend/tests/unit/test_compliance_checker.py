"""Tests for compliance_checker rule expansion (借零件 #1: 从原型 compliance.ts 移植).

只验证新增能力 + 不回归既有 pass/fail 语义。
"""
from app.services.compliance_checker import check_compliance


# ---------- ① 极限词:新增词被命中且为 high ----------
def test_new_extreme_words_flagged():
    new_words = [
        "极品", "首个", "冠军", "之王", "巅峰", "顶峰",
        "史无前例", "前无古人", "绝无仅有", "完美", "永远", "王牌", "尖端",
    ]
    for w in new_words:
        r = check_compliance(f"这是一款{w}产品")
        assert any(v["severity"] == "high" for v in r["violations"]), f"{w} 未被命中"
        assert r["compliant"] is False, f"{w} 应使 compliant=False"


# ---------- ② 敏感行业表述:新增医疗/金融/教育词 ----------
def test_new_medical_terms_flagged():
    for w in ["疗效", "药到病除", "包治", "痊愈", "医效", "根除"]:
        r = check_compliance(f"本品{w}显著")
        assert any(v.get("category") == "医疗功效表述" for v in r["violations"]), f"{w} 未被命中"


def test_new_finance_terms_flagged():
    for w in ["保收益", "必赚"]:
        r = check_compliance(f"投资本产品{w}")
        assert any(v.get("category") == "金融投资承诺" for v in r["violations"]), f"{w} 未被命中"


def test_new_education_terms_flagged():
    for w in ["必中", "保证录取"]:
        r = check_compliance(f"报名即{w}")
        assert any(v.get("category") == "教育培训承诺" for v in r["violations"]), f"{w} 未被命中"


# ---------- ③ 平台敏感词(整类新增)----------
def test_platform_sensitive_words_per_platform():
    r = check_compliance("加微信领优惠", platform_id="xiaohongshu")
    assert any(v["type"] == "platform_sensitive_word" and v["word"] == "加微信"
               for v in r["violations"])
    r = check_compliance("好评返现活动来啦", platform_id="taobao")
    assert any(v["type"] == "platform_sensitive_word" and v["word"] == "好评返现"
               for v in r["violations"])
    r = check_compliance("点击外链购买", platform_id="douyin")
    assert any(v["type"] == "platform_sensitive_word" and v["word"] == "外链"
               for v in r["violations"])


def test_platform_sensitive_only_for_matching_platform():
    # 「好评返现」是淘宝词,在小红书平台不应作为平台敏感词触发
    r = check_compliance("好评返现", platform_id="xiaohongshu")
    assert not any(v["type"] == "platform_sensitive_word" for v in r["violations"])


def test_platform_sensitive_is_medium_and_keeps_compliant_true():
    # 仅含平台敏感词(medium、无 high)→ compliant 不应翻转为 False
    r = check_compliance("加微信", platform_id="xiaohongshu")
    assert any(v["type"] == "platform_sensitive_word" for v in r["violations"])
    assert r["compliant"] is True


# ---------- 回归:干净文案仍然通过 ----------
def test_clean_text_passes():
    r = check_compliance("轻薄透气的防晒衣,适合通勤与户外", platform_id="xiaohongshu")
    assert r["compliant"] is True
    # 干净文案不应有 high/medium 违规(平台尺寸 info 提示是既有行为,允许保留)
    assert not any(v["severity"] in ("high", "medium") for v in r["violations"])
