"""
Quality Checker — OCR text verification + brand color deviation detection.

Step 1 of AI aesthetic evaluation pipeline:
  - OCR check: verify generated image text matches expected copy
  - Brand color check: detect color deviation from brand palette using ΔE CIE2000
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QualityChecker:
    """Post-generation quality verification service."""

    def __init__(self, use_gpu: bool = True):
        self._ocr_reader = None
        self._use_gpu = use_gpu

    def _get_ocr(self):
        """Lazy-load EasyOCR reader (heavy init, do once)."""
        if self._ocr_reader is None:
            import easyocr
            self._ocr_reader = easyocr.Reader(
                ['ch_sim', 'en'],
                gpu=self._use_gpu,
                verbose=False,
            )
        return self._ocr_reader

    # ── OCR Text Verification ──────────────────────────────────

    def check_text_accuracy(
        self,
        image_path: str,
        expected_texts: list[str],
        match_threshold: float = 0.5,
    ) -> dict:
        """Extract text from image via OCR and compare against expected texts.

        Args:
            image_path: Path to the generated image file.
            expected_texts: List of expected text strings (from brief/copy).
            match_threshold: Minimum substring match ratio to count as match.

        Returns:
            {
                "passed": bool,
                "ocr_text": str,           # all detected text joined
                "ocr_details": [...],      # raw OCR results
                "expected_texts": [...],
                "match_count": int,        # how many expected texts found
                "mismatches": [...],       # expected texts not found
                "confidence": float,       # average OCR confidence
            }
        """
        if not expected_texts:
            return {
                "passed": True,
                "ocr_text": "",
                "ocr_details": [],
                "expected_texts": [],
                "match_count": 0,
                "mismatches": [],
                "confidence": 0.0,
            }

        try:
            reader = self._get_ocr()
            raw_results = reader.readtext(image_path)
        except Exception as e:
            logger.warning(f"OCR failed for {image_path}: {e}")
            return {
                "passed": False,
                "ocr_text": "",
                "ocr_details": [],
                "expected_texts": expected_texts,
                "match_count": 0,
                "mismatches": expected_texts,
                "confidence": 0.0,
                "error": str(e),
            }

        # Extract detected text
        detected_texts = []
        confidences = []
        for bbox, text, conf in raw_results:
            detected_texts.append(text)
            confidences.append(conf)

        full_text = " ".join(detected_texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Match expected texts against detected text (substring matching)
        match_count = 0
        mismatches = []
        for expected in expected_texts:
            expected_lower = expected.lower().strip()
            found = False
            for detected in detected_texts:
                detected_lower = detected.lower()
                # Substring match: either expected in detected or vice versa
                if expected_lower in detected_lower or detected_lower in expected_lower:
                    found = True
                    break
            if found:
                match_count += 1
            else:
                mismatches.append(expected)

        passed = match_count >= len(expected_texts) * match_threshold

        return {
            "passed": passed,
            "ocr_text": full_text,
            "ocr_details": [{"text": t, "confidence": round(c, 3)} for t, c in zip(detected_texts, confidences)],
            "expected_texts": expected_texts,
            "match_count": match_count,
            "mismatches": mismatches,
            "confidence": round(avg_confidence, 3),
        }

    # ── Brand Color Deviation ──────────────────────────────────

    def check_brand_colors(
        self,
        image_path: str,
        brand_colors: dict[str, str],
        tolerance: float = 5.0,
        sample_regions: int = 5,
    ) -> dict:
        """Check if dominant colors in image match brand palette within ΔE tolerance.

        Args:
            image_path: Path to the generated image file.
            brand_colors: Dict of {color_name: hex_color}, e.g. {"primary": "#E63946"}.
            tolerance: Maximum acceptable ΔE CIE2000 value.
            sample_regions: Number of regions to sample from the image.

        Returns:
            {
                "passed": bool,
                "deviations": [{"brand_color": ..., "detected_color": ..., "delta_e": ...}],
                "dominant_colors": [...],
                "tolerance": float,
                "skipped": bool | None,
            }
        """
        if not brand_colors:
            return {"passed": True, "deviations": [], "dominant_colors": [], "tolerance": tolerance, "skipped": True}

        try:
            import cv2
            import numpy as np
            from PIL import ImageColor
            from colour.difference import delta_E_CIE2000

            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Cannot read image: {image_path}")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Extract dominant colors by sampling regions
            h, w = img_rgb.shape[:2]
            dominant_colors = []
            for i in range(sample_regions):
                y = int(h * (i + 1) / (sample_regions + 1))
                x = w // 2
                # Sample a 20x20 patch
                patch = img_rgb[max(0, y - 10):min(h, y + 10), max(0, x - 10):min(w, x + 10)]
                avg_color = patch.mean(axis=(0, 1))
                dominant_colors.append(tuple(avg_color.astype(int)))

            # Reduce to unique dominant colors (k-means simplification)
            unique_colors = list(set(dominant_colors))[:3]  # top 3

            deviations = []
            for name, hex_color in brand_colors.items():
                rgb_255 = ImageColor.getrgb(hex_color)
                brand_rgb = (rgb_255[0] / 255.0, rgb_255[1] / 255.0, rgb_255[2] / 255.0)
                brand_lab = self._rgb_to_lab(brand_rgb)

                # Find closest detected color to this brand color
                min_delta_e = float("inf")
                closest_detected = None
                for det_rgb in unique_colors:
                    det_lab = self._rgb_to_lab(tuple(c / 255.0 for c in det_rgb))
                    try:
                        de = delta_E_CIE2000(
                            np.array([brand_lab[0] * 100, brand_lab[1], brand_lab[2]]),
                            np.array([det_lab[0] * 100, det_lab[1], det_lab[2]]),
                        )
                        if de < min_delta_e:
                            min_delta_e = de
                            closest_detected = det_rgb
                    except Exception:
                        continue

                if min_delta_e > tolerance and closest_detected:
                    deviations.append({
                        "brand_color": name,
                        "brand_hex": hex_color,
                        "detected_color": f"#{closest_detected[0]:02x}{closest_detected[1]:02x}{closest_detected[2]:02x}",
                        "delta_e": round(min_delta_e, 2),
                    })

            return {
                "passed": len(deviations) == 0,
                "deviations": deviations,
                "dominant_colors": [f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}" for c in unique_colors],
                "tolerance": tolerance,
            }

        except Exception as e:
            logger.warning(f"Brand color check failed for {image_path}: {e}")
            return {
                "passed": False,
                "deviations": [],
                "dominant_colors": [],
                "tolerance": tolerance,
                "error": str(e),
            }

    @staticmethod
    def _rgb_to_lab(rgb: tuple) -> tuple:
        """Convert RGB (0-1 range) to CIE Lab*."""
        # Simplified conversion — fallback that works for color comparison
        r, g, b = [max(0.0, min(1.0, c)) for c in rgb]

        # Linearize
        def linearize(c):
            if c > 0.04045:
                return ((c + 0.055) / 1.055) ** 2.4
            return c / 12.92

        r_lin, g_lin, b_lin = linearize(r), linearize(g), linearize(b)

        # XYZ
        x = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
        y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
        z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505

        # D65 reference white
        xn, yn, zn = 0.95047, 1.0, 1.08883

        def f(t):
            delta = 6 / 29
            if t > delta**3:
                return t ** (1 / 3)
            return t / (3 * delta**2) + 4 / 29

        L = 116 * f(y / yn) - 16
        a = 500 * (f(x / xn) - f(y / yn))
        b_val = 200 * (f(y / yn) - f(z / zn))

        return (L / 100.0, a, b_val)

    # ── Full Quality Report ────────────────────────────────────

    def run_full_check(
        self,
        image_path: str,
        expected_texts: Optional[list[str]] = None,
        brand_colors: Optional[dict[str, str]] = None,
        tolerance: float = 5.0,
    ) -> dict:
        """Run both OCR and brand color checks, return comprehensive report.

        Returns:
            {
                "text_check": {...},
                "color_check": {...},
                "overall_passed": bool,
                "summary": str,
                "issues": [...],
                "suggestions": [...],
            }
        """
        expected_texts = expected_texts or []
        brand_colors = brand_colors or {}

        text_check = self.check_text_accuracy(image_path, expected_texts)
        color_check = self.check_brand_colors(image_path, brand_colors, tolerance)

        issues = []
        suggestions = []

        if not text_check["passed"] and text_check["mismatches"]:
            issues.append(f"文案不匹配：{', '.join(text_check['mismatches'][:3])}")
            suggestions.append("检查生成图中的文字是否与原文案一致，可能需要重新生成")

        if not color_check["passed"]:
            for dev in color_check.get("deviations", []):
                issues.append(f"品牌色「{dev['brand_color']}」偏差 ΔE={dev['delta_e']}")
            suggestions.append(f"品牌色偏离超过容差 {tolerance}，建议回退到品牌色板")

        overall_passed = text_check["passed"] and color_check["passed"]

        return {
            "text_check": text_check,
            "color_check": color_check,
            "overall_passed": overall_passed,
            "summary": "质检通过" if overall_passed else f"发现 {len(issues)} 个问题",
            "issues": issues,
            "suggestions": suggestions,
        }
