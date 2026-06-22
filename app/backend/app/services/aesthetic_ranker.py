"""
Aesthetic Ranker — technical quality + pairwise comparison + ranking.

Step 2 of AI aesthetic evaluation pipeline:
  - Technical quality (MUSIQ via pyiqa): sharpness, noise, compression
  - Pairwise comparison: vision LLM judges A vs B against brief
  - Combined ranking: weighted scores → ordered list
"""
import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class AestheticRanker:
    """Image aesthetic evaluation and comparison service."""

    def __init__(self):
        self._musiq_metric = None

    def _get_musiq(self):
        """Lazy-load MUSIQ metric (downloads model on first use)."""
        if self._musiq_metric is None:
            import pyiqa
            self._musiq_metric = pyiqa.create_metric("musiq", device="cpu")
        return self._musiq_metric

    # ── Technical Quality ──────────────────────────────────────

    def technical_quality(self, image_path: str) -> dict:
        """Evaluate technical image quality using MUSIQ (no-reference).

        Returns:
            {"score": float 0-100, "metric": "MUSIQ", "error": str | None}
        """
        if not os.path.exists(image_path):
            return {"score": 0.0, "metric": "MUSIQ", "error": f"File not found: {image_path}"}

        try:
            metric = self._get_musiq()
            # pyiqa returns a tensor; convert to float
            score_tensor = metric(image_path)
            score = float(score_tensor.item()) if hasattr(score_tensor, 'item') else float(score_tensor)
            # MUSIQ scores are typically 0-100, but clamp just in case
            score = max(0.0, min(100.0, score))
            return {"score": round(score, 2), "metric": "MUSIQ"}
        except Exception as e:
            logger.warning(f"MUSIQ failed for {image_path}: {e}")
            return {"score": 0.0, "metric": "MUSIQ", "error": str(e)}

    # ── Pairwise Comparison ────────────────────────────────────

    def compare_pair(
        self,
        image_a_path: str,
        image_b_path: str,
        brief: dict,
    ) -> dict:
        """Compare two images against brief requirements.

        Uses technical quality when no vision LLM available.
        When brief is provided, attempts style-aware comparison.

        Returns:
            {
                "winner": "A" | "B" | "tie",
                "reasoning": str,
                "scores": {"A": float, "B": float},
            }
        """
        qa = self.technical_quality(image_a_path)
        qb = self.technical_quality(image_b_path)

        score_a = qa.get("score", 0)
        score_b = qb.get("score", 0)

        # Check if brief has style requirements for LLM comparison
        has_style_brief = bool(
            brief.get("brand_style")
            or brief.get("target_audience")
            or brief.get("_strategy_context")
        )

        verdict = ""
        suggestion = ""
        dimensions = []

        if has_style_brief:
            # Use vision LLM for style-aware comparison. compare_pair is a
            # synchronous API, so bridge the async vision call when safe.
            llm_result = self._llm_compare_sync(image_a_path, image_b_path, brief)
            if llm_result:
                llm_score_a = llm_result["scores"]["A"]
                llm_score_b = llm_result["scores"]["B"]
                score_a = score_a * 0.3 + llm_score_a * 0.7
                score_b = score_b * 0.3 + llm_score_b * 0.7
                winner = "A" if score_a > score_b else ("B" if score_b > score_a else "tie")
                reasoning = llm_result.get("reasoning", "")
                verdict = llm_result.get("verdict", reasoning)
                dimensions = llm_result.get("dimensions", [])
                suggestion = llm_result.get("suggestion", "")
            else:
                # LLM unavailable — fallback with partial dimension analysis
                winner = "A" if score_a > score_b else ("B" if score_b > score_a else "tie")
                reasoning = f"技术质量 MUSIQ: A={score_a:.1f}, B={score_b:.1f}"
                verdict = f"图片{winner}技术质量更优（MUSIQ评分），建议配置 API Key 启用风格化多维度对比"
                dimensions = [
                    {"name": "技术质量", "score_a": round(score_a, 2), "score_b": round(score_b, 2),
                     "note": f"MUSIQ无参考质量评分"},
                ]
                suggestion = "配置 MIGEAPI_API_KEY 环境变量可启用: 风格匹配度、受众吸引力、构图质量、商业适用性 四维度对比"
        else:
            # Pure technical comparison
            winner = "A" if score_a > score_b else ("B" if score_b > score_a else "tie")
            reasoning = f"技术质量 MUSIQ: A={score_a:.1f}, B={score_b:.1f}"
            verdict = f"图片{winner}技术质量更优" if winner != "tie" else "两张图片技术质量持平"
            dimensions = [
                {"name": "技术质量", "score_a": round(score_a, 2), "score_b": round(score_b, 2),
                 "note": f"MUSIQ无参考质量评分"},
            ]
            suggestion = "填写Brief中的品牌风格和目标用户信息可启用风格化多维度对比"

        return {
            "winner": winner,
            "reasoning": reasoning,
            "verdict": verdict,
            "scores": {"A": round(score_a, 2), "B": round(score_b, 2)},
            "dimensions": dimensions,
            "suggestion": suggestion,
        }

    def _llm_compare_sync(self, image_a: str, image_b: str, brief: dict) -> Optional[dict]:
        """Run async vision comparison from the synchronous comparison API.

        FastAPI sync routes and unit tests call compare_pair from a normal thread,
        where asyncio.run is safe. If compare_pair is ever called inside an
        existing event loop, fall back to technical quality instead of leaking a
        coroutine or blocking the loop.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._llm_compare(image_a, image_b, brief))

        logger.warning("Vision compare skipped inside running event loop; using technical quality fallback")
        return None

    async def _llm_compare(self, image_a: str, image_b: str, brief: dict) -> Optional[dict]:
        """Use vision LLM to compare two images against style brief.

        Uses DataEyesAI vision API with actual image data.
        Falls back to text-only comparison if vision fails.
        """
        try:
            from app.services.vision_service import vision_service

            style = brief.get("brand_style", "")
            audience = brief.get("target_audience", "")
            product = brief.get("product_name", "product")

            criteria = f"""Product: {product}
Brand style: {style}
Target audience: {audience}
Selling points: {brief.get('selling_points', [])}"""

            result = await vision_service.compare_images(
                image_a=image_a,
                image_b=image_b,
                criteria=criteria,
            )

            if result.get("success"):
                import json as _json
                content = result["content"]
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    parsed = _json.loads(content[json_start:json_end])
                    return {
                        "winner": parsed.get("winner", "tie"),
                        "verdict": parsed.get("verdict", ""),
                        "reasoning": parsed.get("verdict", ""),
                        "scores": parsed.get("scores", {"A": 50, "B": 50}),
                        "dimensions": parsed.get("dimensions", []),
                        "suggestion": parsed.get("suggestion", ""),
                    }

            logger.warning("Vision compare returned invalid JSON, falling back")
            return None

        except Exception as e:
            logger.warning(f"Vision compare failed: {e}, using technical quality fallback")
            return None

    # ── Multi-image Ranking    # ── Multi-image Ranking ────────────────────────────────────

    def rank_images(
        self,
        image_paths: list[str],
        brief: dict,
    ) -> dict:
        """Rank multiple images by aesthetic quality against brief.

        Returns:
            {
                "rankings": [
                    {"rank": 1, "path": ..., "score": ..., "quality": {...}},
                    ...
                ],
                "brief": dict,
            }
        """
        results = []
        for path in image_paths:
            q = self.technical_quality(path)
            results.append({
                "path": path,
                "score": q.get("score", 0),
                "quality": q,
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        # Assign ranks
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "rankings": results,
            "brief": {
                "product_name": brief.get("product_name", ""),
                "brand_style": brief.get("brand_style", ""),
            },
        }
