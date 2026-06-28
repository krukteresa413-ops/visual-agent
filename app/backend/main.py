import os
from dotenv import load_dotenv
load_dotenv("/opt/visual-agent/.env", override=True)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.db.session import Base, engine
from app.models.project import Project
from app.models.canvas_state import CanvasState  # Atelier Flow infinite canvas
from app.models.behavior_event import BehaviorEvent
from app.models.font_generation_model import FontGeneration
from app.models.video_task import VideoTask
from app.models.auth import Tenant, User  # ensure users table mapped before create_all
from app.models.credit import CreditOrder  # 图四 充值订单
from app.api.visual_tasks import router as visual_tasks_router
from app.api.brief_routes import router as brief_router
from app.api.project_routes import router as project_router
from app.api.upload_routes import router as upload_router
from app.api.brand_routes import router as brand_router
from app.api.image_generation_routes import router as image_gen_router
from app.api.platform_routes import router as platform_router
from app.api.video_generation_routes import router as video_gen_router
from app.api.unified_generation_routes import router as unified_router
from app.api.asset_routes import router as asset_router
from app.api.copywriting_routes import router as copywriting_router
from app.api.layout_routes import router as layout_router
from app.api.canvas_routes import router as canvas_router
from app.api.dashboard_routes import router as dashboard_router

from app.api.history_routes import router as history_router
from app.api.progress_routes import router as progress_router
from app.api.campaign_routes import router as campaign_router
from app.api.asset_library_routes import router as asset_library_router
from app.api.inspiration_routes import router as inspiration_router
from app.api.quality_routes import router as quality_router
from app.api.aesthetic_routes import router as aesthetic_router
from app.api.behavior_routes import router as behavior_router
from app.api.atelier_canvas_routes import router as atelier_canvas_router
from app.api.video_edit_routes import router as video_edit_router
from app.api.font_generation_routes import router as font_gen_router
from app.api.canvas_action_routes import router as canvas_action_router
from app.api.canvas_image_action_routes import router as canvas_image_action_router
from app.api.vision_routes import router as vision_router
from app.api.auth_routes import router as auth_router
from app.api.model_catalog_routes import router as model_catalog_router
from app.api.skills_routes import router as skills_router
from app.api.library_routes import router as library_router
from app.api.chat_routes import router as chat_router
from app.api.payment_routes import router as payment_router
from app.api.credits_routes import router as credits_router


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Visual Agent API")


@app.on_event("startup")
async def startup():
    """Start video polling worker + recover unfinished tasks."""
    from app.services.video_polling_worker import recover_unfinished_tasks, video_polling_worker
    recovered = recover_unfinished_tasks()
    if recovered:
        import logging
        logging.getLogger("uvicorn").info(f"Video worker: recovered {recovered} unfinished tasks")
    import asyncio
    asyncio.create_task(video_polling_worker())
app.mount("/uploads", StaticFiles(directory="/opt/visual-agent/uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(visual_tasks_router)
app.include_router(brief_router)
app.include_router(upload_router)
app.include_router(project_router)
app.include_router(brand_router)
app.include_router(image_gen_router)
app.include_router(skills_router)
app.include_router(model_catalog_router)
app.include_router(video_gen_router)
app.include_router(platform_router)
app.include_router(asset_router)
app.include_router(copywriting_router)
app.include_router(layout_router)
app.include_router(canvas_router)
app.include_router(asset_library_router)
app.include_router(library_router)
app.include_router(campaign_router)
app.include_router(dashboard_router)
app.include_router(progress_router)
app.include_router(history_router)
app.include_router(inspiration_router)
app.include_router(quality_router)
app.include_router(aesthetic_router)
app.include_router(behavior_router)
app.include_router(unified_router)
app.include_router(atelier_canvas_router)
app.include_router(chat_router)
app.include_router(video_edit_router)
app.include_router(vision_router)
app.include_router(font_gen_router)
app.include_router(canvas_action_router)
app.include_router(canvas_image_action_router)
app.include_router(payment_router)
app.include_router(credits_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    import psycopg2
    try:
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        conn.close()
        return {"database": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"database": "error", "detail": str(e)})


@app.get("/health/redis")
def health_redis():
    import redis
    try:
        redis_url = os.getenv("REDIS_URL")
        r = redis.from_url(redis_url)
        pong = r.ping()
        return {"redis": "ok", "pong": pong}
    except Exception as e:
        return JSONResponse(status_code=503, content={"redis": "error", "detail": str(e)})
