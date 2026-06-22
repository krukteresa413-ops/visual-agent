"""Conservative document text cleaner before LLM brief parsing.

This module intentionally does NOT do aggressive field extraction. It only
removes structural PDF noise (page numbers/repeated headers/footers) and lets
route-level callers keep the original 8000-character budget for parsing quality.
"""
from __future__ import annotations

import re

_NOISE_LINE_PATTERNS = [
    re.compile(r"^\s*page\s+\d+(?:\s+of\s+\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*第\s*\d+\s*页\s*$"),
    re.compile(r"^\s*[\d\-|.\s]{3,}\s*$"),
]

_FACT_HINT_PATTERN = re.compile(
    r"[:：]|产品|规格|参数|卖点|特点|品牌|调性|颜色|色彩|字体|故事|受众|市场|"
    r"Feature|Material|Category|Brand|Color|Font|Tone|Story|Market|Audience",
    re.IGNORECASE,
)


def clean_pdf_text(text: str) -> str:
    """Remove common PDF extraction noise while preserving document content."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if any(pattern.match(line) for pattern in _NOISE_LINE_PATTERNS):
            continue
        normalized_lines.append(line)

    counts = {line: normalized_lines.count(line) for line in set(normalized_lines) if line}
    kept: list[str] = []
    for line in normalized_lines:
        if counts.get(line, 0) > 3 and len(line) <= 120 and not _FACT_HINT_PATTERN.search(line):
            continue
        kept.append(line)

    cleaned = "\n".join(kept)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
