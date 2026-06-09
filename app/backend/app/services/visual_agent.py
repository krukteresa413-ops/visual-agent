"""
视觉Agent核心服务。
职责：接收 ProductBrief dict → 渲染Prompt → 调用LLM → 解析为结构化输出。
"""
from typing import List

from app.schemas.visual_strategy import VisualStrategy
from app.schemas.visual_strategy import VisualStrategy
from app.schemas.visual_assets import (
    MainImagePlan,
    WhiteBgPlan,
    SceneImagePlan,
    SellingPointModule,
    VideoScript,
    AdMaterialPlan,
    VisualAssetPlanOut,
)
from app.services.llm_client import LLMClient
from app.services.prompt_loader import PromptLoader
from app.services.platform_prompt_loader import get_platform_context, load_platform_prompt



class GenerationError(Exception):
    """单个素材生成失败，携带类型名便于上层汇总。"""
    def __init__(self, asset_type: str, message: str):
        self.asset_type = asset_type
        super().__init__(message)


class VisualAgent:
    """
    视觉素材方案生成Agent。
    每个 generate_xxx 方法对应 PRD 中的一类素材。
    """

    def __init__(self):
        self._llm = LLMClient()
        self._prompts = PromptLoader()


    @staticmethod
    def _enrich_system(system: str, platform_id: str | None, brief: dict | None = None) -> str:
        """Inject platform context + strategy + full template into system prompt."""
        parts = [system]
        if platform_id:
            ctx = get_platform_context(platform_id)
            if ctx:
                parts.append(ctx)
            tmpl = load_platform_prompt(platform_id, {})
            if tmpl:
                parts.append(tmpl)
        if brief and brief.get("_strategy_context"):
            parts.append(brief["_strategy_context"])
        if brief and brief.get("_brand_context"):
            parts.append("# 品牌记忆\n" + brief["_brand_context"])
        return "\n".join(parts) if len(parts) > 1 else system

    async def generate_main_image(self, brief: dict, platform_id: str | None = None) -> MainImagePlan:
        try:
            """PRD 8.3：主图生成方案"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("main_image", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            return MainImagePlan(**raw)

        except Exception as e:
            raise GenerationError("generate_main_image", str(e)) from e
    async def generate_white_bg(self, brief: dict, platform_id: str | None = None) -> WhiteBgPlan:
        try:
            """PRD 8.4：白底图方案"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("white_bg", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            return WhiteBgPlan(**raw)

        except Exception as e:
            raise GenerationError("generate_white_bg", str(e)) from e
    async def generate_scene_images(self, brief: dict, platform_id: str | None = None) -> List[SceneImagePlan]:
        try:
            """PRD 8.5：场景图方案（1-3个）"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("scene_image", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            if isinstance(raw, list):
                return [SceneImagePlan(**item) for item in raw]
            return [SceneImagePlan(**raw)]

        except Exception as e:
            raise GenerationError("generate_scene_images", str(e)) from e
    async def generate_selling_points(self, brief: dict, platform_id: str | None = None) -> List[SellingPointModule]:
        try:
            """PRD 8.6：卖点图模块（3-5个）"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("selling_point", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            if isinstance(raw, list):
                return [SellingPointModule(**item) for item in raw]
            return [SellingPointModule(**raw)]

        except Exception as e:
            raise GenerationError("generate_selling_points", str(e)) from e
    async def generate_video_scripts(self, brief: dict, platform_id: str | None = None) -> List[VideoScript]:
        try:
            """PRD 8.7：短视频脚本（15秒+30秒）"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("video_script", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            if isinstance(raw, list):
                return [VideoScript(**item) for item in raw]
            return [VideoScript(**raw)]

        except Exception as e:
            raise GenerationError("generate_video_scripts", str(e)) from e
    async def generate_ad_material(self, brief: dict, platform_id: str | None = None) -> AdMaterialPlan:
        try:
            """PRD 8.8：广告视频素材方案"""
            system = self._enrich_system(self._prompts.render("system", {}), platform_id, brief)
            user = self._prompts.render("ad_material", brief)
            raw = await self._llm.call(system_prompt=system, user_prompt=user)
            return AdMaterialPlan(**raw)

        except Exception as e:
            raise GenerationError("generate_ad_material", str(e)) from e
    async def generate_all(
        self,
        project_id: int,
        brief: dict,
        platform_id: str | None = None,
        db=None,
        brief_id: int = None,
        task_types: list = None,
    ) -> VisualAssetPlanOut:
        """
        PRD 5.1：一次生成六类素材方案。
        支持可选的数据库持久化（Phase 2）。
        """
        import time
        start_time = time.time()

        main_image = await self.generate_main_image(brief)
        white_bg = await self.generate_white_bg(brief)
        scene_images = await self.generate_scene_images(brief)
        selling_points = await self.generate_selling_points(brief)
        video_scripts = await self.generate_video_scripts(brief)
        ad_material = await self.generate_ad_material(brief)

        elapsed = int(time.time() - start_time)

        result = VisualAssetPlanOut(
            project_id=project_id,
            main_image=main_image,
            white_bg=white_bg,
            scene_images=scene_images,
            selling_points=selling_points,
            video_scripts=video_scripts,
            ad_material=ad_material,
        )

        # 持久化（如果传入了 db session）
        if db is not None:
            from app.db.crud_visual_asset_v2 import save_asset_plan
            save_asset_plan(
                db=db,
                project_id=project_id,
                brief_id=brief_id,
                asset_plan=result.model_dump(),
                model_used=self._llm._model,
                generation_seconds=elapsed,
            )

        return result

    async def generate_all_parallel(
        self,
        project_id: int,
        brief: dict,
        platform_id: str | None = None,
        db=None,
        brief_id: int = None,
        task_types: list = None,
    ) -> VisualAssetPlanOut:
        """PRD 5.1 创意策略驱动版：策略 → 注入 → 并行生成六类素材"""
        import asyncio
        import time
        start_time = time.time()

        # Step 0: 先出方向（创意策略）
        try:
            strategy = await self.generate_visual_strategy(brief)
            strategy_context = strategy.to_context_string()
            enriched_brief = {**brief, "_strategy_context": strategy_context}
        except Exception:
            enriched_brief = brief

        # Step 1: 策略注入后并行生成六类素材
        results = await asyncio.gather(
            self.generate_main_image(enriched_brief, platform_id),
            self.generate_white_bg(enriched_brief, platform_id),
            self.generate_scene_images(enriched_brief, platform_id),
            self.generate_selling_points(enriched_brief, platform_id),
            self.generate_video_scripts(enriched_brief, platform_id),
            self.generate_ad_material(enriched_brief, platform_id),
            return_exceptions=True,
        )

        main_image, white_bg, scene_images, selling_points, video_scripts, ad_material = results
        errors = [r for r in results if isinstance(r, BaseException)]

        if len(errors) == 6:
            msg = "; ".join(
                f"{e.asset_type}: {e}" if isinstance(e, GenerationError) else str(e)
                for e in errors
            )
            raise GenerationError("all", msg)

        main_image = main_image if not isinstance(main_image, BaseException) else None
        white_bg = white_bg if not isinstance(white_bg, BaseException) else None
        scene_images = scene_images if not isinstance(scene_images, BaseException) else []
        selling_points = selling_points if not isinstance(selling_points, BaseException) else []
        video_scripts = video_scripts if not isinstance(video_scripts, BaseException) else []
        ad_material = ad_material if not isinstance(ad_material, BaseException) else None

        elapsed = int(time.time() - start_time)

        result = VisualAssetPlanOut(
            project_id=project_id,
            main_image=main_image,
            white_bg=white_bg,
            scene_images=scene_images,
            selling_points=selling_points,
            video_scripts=video_scripts,
            ad_material=ad_material,
        )

        if db is not None:
            from app.db.crud_visual_asset_v2 import save_asset_plan
            save_asset_plan(
                db=db,
                project_id=project_id,
                brief_id=brief_id,
                asset_plan=result.model_dump(),
                model_used=self._llm._model,
                generation_seconds=elapsed,
            )

        return result

    async def generate_images_from_plan(
        self,
        plan,
        provider: str = "dalle",
        width: int = 1024,
        height: int = 1024,
    ) -> dict:
        """从 VisualAssetPlan 批量生成图片。

        Returns:
            {"main_image": {"url": str, ...} | None,
             "scene_images": [{"url": str, ...} | None, ...]}
        """
        import asyncio
        from app.services.image_generation_service import image_generation_service
        from app.models.image_generation_model import ImageGenerationRequest

        result = {"main_image": None, "scene_images": []}

        # Generate main image
        if plan.main_image and plan.main_image.prompt:
            try:
                req = ImageGenerationRequest(
                    provider=provider,
                    prompt=plan.main_image.prompt,
                    width=width,
                    height=height,
                )
                gen = await image_generation_service.generate(req)
                if gen.images:
                    img = gen.images[0]
                    result["main_image"] = {"url": img.url, "width": img.width, "height": img.height}
            except Exception:
                pass  # partial failure OK

        # Generate scene images
        for scene in (plan.scene_images or []):
            if scene.prompt:
                try:
                    req = ImageGenerationRequest(
                        provider=provider,
                        prompt=scene.prompt,
                        width=width,
                        height=height,
                    )
                    gen = await image_generation_service.generate(req)
                    if gen.images:
                        img = gen.images[0]
                        result["scene_images"].append({"url": img.url, "width": img.width, "height": img.height})
                    else:
                        result["scene_images"].append(None)
                except Exception:
                    result["scene_images"].append(None)
            else:
                result["scene_images"].append(None)

        return result


    async def generate_videos_from_plan(
        self,
        plan,
        provider: str = "local",
    ) -> list:
        """从 VisualAssetPlan 的 video_scripts 批量生成视频。

        Returns:
            [{"url": str, ...} | None, ...] — 与 plan.video_scripts 一一对应
        """
        from app.services.video_generation_service import video_generation_service
        from app.models.video_generation_model import VideoGenerationRequest

        results = []
        for script in (plan.video_scripts or []):
            # Build a prompt from the video script fields
            prompt = f"{script.video_goal}. Pacing: {script.pacing}. CTA: {script.cta}"
            try:
                req = VideoGenerationRequest(
                    provider=provider,
                    prompt=prompt,
                    duration=script.duration_seconds,
                )
                gen = await video_generation_service.generate(req)
                if gen.videos:
                    v = gen.videos[0]
                    results.append({"url": v.url, "duration": v.duration, "width": v.width, "height": v.height})
                else:
                    results.append(None)
            except Exception:
                results.append(None)
        return results

    DETAIL_PAGE_SYSTEM_PROMPT = """Product Detail Page / A+ Content

    @staticmethod
    def _audience_context(audience_type: str) -> str:
        if audience_type == B2B:
            return n【B2B 注意事项】n- 目标受众：批发商/经销商/采购决策者n- 风格：专业、数据驱动、强调供应链能力n- CTA：Get Quote / Contact Supplier / Request Samplen- 强调 OEM、MOQ、认证资质n- 突出工厂实力、品控流程、交付能力
        elif audience_type == B2C:
            return n【B2C 注意事项】n- 目标受众：终端消费者n- 风格：场景化、情感共鸣、使用体验n- CTA：Buy Now / Add to Cart / Shop Now / Limited Offern- 强调使用便利性、颜值、用户评价n- 突出生活场景、痛点解决、性价比
        else:
            return n【Both 注意事项】n- 兼顾 B2B 专业性和 B2C 吸引力n- 前半部分面向采购商，后半部分面向终端用户n- CTA 同时提供询盘和购买选项
1. Hero Banner 2. 3-5卖点模块 3. 场景展示 4. 规格参数 5. 信任背书 6. CTA
支持 Alibaba / Amazon / Shopify 区分 B2B / B2C
JSON 输出 6-10 模块"""

    DETAIL_PAGE_USER_TEMPLATE = """
{product_name} {category} | 规格:{specifications} | 卖点:{selling_points}
市场:{target_market} | 场景:{usage_scenarios} | 客户:{target_customer}
风格:{brand_style} | 合规:{compliance_notes} | 平台:{platform} 受众:{audience_type}
JSON 输出 6-10 模块"""

    async def generate_detail_page(self, brief: dict, platform: str = "alibaba", audience_type: str = "B2B"):
        import json
        from app.schemas.detail_page import DetailPagePlan, DetailPageModule
        user_prompt = self.DETAIL_PAGE_USER_TEMPLATE.format(
            product_name=brief.get("product_name",""), category=brief.get("category",""),
            specifications=", ".join(brief.get("specifications",[])),
            selling_points=", ".join(brief.get("selling_points",[])),
            target_market=", ".join(brief.get("target_market",[])),
            usage_scenarios=", ".join(brief.get("usage_scenarios",[])),
            target_customer=", ".join(brief.get("target_customer",[])),
            brand_style=brief.get("brand_style","professional"),
            compliance_notes=", ".join(brief.get("compliance_notes",[])),
            platform=platform, audience_type=audience_type)
        raw = await self._llm.call(system_prompt=self.DETAIL_PAGE_SYSTEM_PROMPT, user_prompt=user_prompt)
        modules = [DetailPageModule(**m) for m in raw.get("modules",[])]
        raw["modules"] = modules
        return DetailPagePlan(**raw)

    VISUAL_STRATEGY_SYSTEM_PROMPT = """你是一位资深视觉策略师（Creative Strategist）。在生成任何视觉素材之前，你负责确定整体的创意方向和策略框架。

## 你的任务
根据产品信息，制定完整的视觉策略。这个策略将指导后续所有素材（主图、白底图、场景图、卖点模块、视频脚本、广告素材）的生成。

## 分析维度
1. 品牌定位: 这个产品在市场中的定位是什么？一句话概括
2. 目标客户画像: 谁在买这个产品？他们的关注点是什么？
3. 视觉风格: 色彩、构图、光影的整体方向（如：工业专业风/生活美学风/科技极简风）
4. 卖点优先级: 对卖点进行排序（Rank 1-3），并解释排序理由
5. 素材策略: 针对6类素材分别给出方向建议
6. 品牌语调: B2B 专业可信 / B2C 情感共鸣
7. 受众类型: B2B 或 B2C
8. 核心差异化: 与竞品相比最独特的优势

## 输出格式
严格输出以下 JSON，不要任何额外文字：
{"visual_positioning":"品牌定位","target_customer_analysis":"目标客户分析","visual_style":"视觉风格方向","selling_points_priority":[{"rank":1,"point":"卖点","rationale":"理由"}],"asset_plan_summary":{"main_image":"方向","white_bg":"方向","scene_images":"方向","selling_points":"方向","video_scripts":"方向","ad_material":"方向"},"brand_tone":"语调","audience_type":"B2B或B2C","key_differentiators":"差异化"}"""

    async def generate_visual_strategy(self, brief: dict) -> VisualStrategy:
        """生成创意策略 — 先出方向再出图"""
        product_info = (
            f"产品: {brief.get('product_name','')} | "
            f"品类: {brief.get('category','')} | "
            f"规格: {', '.join(brief.get('specifications',[]))} | "
            f"卖点: {', '.join(brief.get('selling_points',[]))} | "
            f"目标市场: {', '.join(brief.get('target_market',[]))} | "
            f"目标客户: {', '.join(brief.get('target_customer',[]))} | "
            f"使用场景: {', '.join(brief.get('usage_scenarios',[]))} | "
            f"品牌风格: {brief.get('brand_style','')}"
        )
        raw = await self._llm.call(
            system_prompt=self.VISUAL_STRATEGY_SYSTEM_PROMPT,
            user_prompt=product_info,
        )
        return VisualStrategy(**raw)