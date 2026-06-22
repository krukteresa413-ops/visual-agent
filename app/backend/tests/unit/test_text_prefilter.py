from app.services.text_prefilter import clean_pdf_text


def test_clean_pdf_text_removes_repeated_headers_without_dropping_facts():
    raw = (
        "COMPANY PROFILE\nPage 1 of 20\n" * 8
        + "产品名称: ArcticPro 300L 商用冷柜\n"
        + "品牌调性: 专业、可靠、节能\n"
        + "规格参数: 300L, 220V, stainless steel body\n"
        + "卖点: Fast cooling; Energy saving compressor\n"
        + ("COMPANY PROFILE\nPage 2 of 20\n" * 8)
    )

    cleaned = clean_pdf_text(raw)

    assert "Page 1 of" not in cleaned
    assert cleaned.count("COMPANY PROFILE") < 3
    assert "ArcticPro 300L" in cleaned
    assert "品牌调性" in cleaned
    assert "Fast cooling" in cleaned


def test_clean_pdf_text_does_not_aggressively_extract_snippets():
    raw = "\n".join(
        ["产品名称: ArcticPro 300L 商用冷柜"]
        + [f"品牌故事段落 {i}: 这是品牌手册中需要保留的语气、颜色、字体和渠道信息。" for i in range(80)]
        + ["规格参数: 300L, 220V, stainless steel body"]
    )

    cleaned = clean_pdf_text(raw)

    assert len(cleaned) > 3000
    assert "品牌故事段落 60" in cleaned
    assert "规格参数" in cleaned
