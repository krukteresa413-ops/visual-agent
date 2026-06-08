from fastapi import FastAPI
from dotenv import load_dotenv
import os
import psycopg2
import redis

from app.db.session import Base, engine
from app.models.project import Project
from app.api.projects import router as projects_router

load_dotenv("/opt/visual-agent/.env")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Visual Agent API")

app.include_router(projects_router)


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
