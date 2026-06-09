from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import psycopg2
import redis

from app.db.session import Base, engine
from app.models.project import Project
from app.api.product_briefs import router as product_briefs_router
from app.api.visual_tasks import router as visual_tasks_router
from app.api.brief_routes import router as brief_router
from app.api.project_routes import router as project_router
from app.api.upload_routes import router as upload_router
from app.api.brand_routes import router as brand_router
from app.api.inspiration_routes import router as inspiration_router
from app.api.image_generation_routes import router as image_gen_router
from app.api.platform_routes import router as platform_router
from app.api.video_generation_routes import router as video_gen_router
from app.api.unified_generation_routes import router as unified_router
from app.api.asset_routes import router as asset_router

load_dotenv("/opt/visual-agent/.env")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Visual Agent API")

app.include_router(product_briefs_router)
app.include_router(visual_tasks_router)
app.include_router(brief_router)
app.include_router(project_router)
app.include_router(upload_router)
app.include_router(brand_router)
app.include_router(inspiration_router)
app.include_router(image_gen_router)
app.include_router(video_gen_router)
app.include_router(platform_router)
app.include_router(asset_router)
app.include_router(unified_router)
app.include_router(asset_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": os.getenv("APP_NAME"),
        "region": os.getenv("APP_REGION"),
        "oss_bucket": os.getenv("OSS_BUCKET"),
        "oss_endpoint": os.getenv("OSS_ENDPOINT"),
    }


@app.get("/health/db")
def health_db():
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    conn.close()
    return {"database": "ok"}


@app.get("/health/redis")
def health_redis():
    redis_url = os.getenv("REDIS_URL")
    r = redis.from_url(redis_url)
    pong = r.ping()
    return {"redis": "ok", "pong": pong}