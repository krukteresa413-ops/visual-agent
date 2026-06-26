"""
灵感库 API 测试 — RED phase.
"""
import pytest
import json
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db

# Ensure model is registered with Base.metadata before create_all
import app.models.inspiration  # noqa: F401


@pytest.fixture
def db_session(tmp_path):
    """Create a fresh SQLite DB per test function."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _seed(session):
    from app.models.inspiration import InspirationItem
    items = [
        InspirationItem(
            category="poster", sub_category="拼贴海报",
            preview_url="https://oss.example.com/p1.webp",
            prompt_template="A poster for {product_name}, style: collage",
            aspect_ratio="9 / 16",
        ),
        InspirationItem(
            category="poster", sub_category="渐变艺术",
            preview_url="https://oss.example.com/p2.webp",
            prompt_template="Gradient art poster for {product_name}",
            aspect_ratio="9 / 16",
        ),
        InspirationItem(
            category="app", sub_category="App 图标",
            preview_url="https://oss.example.com/a1.webp",
            prompt_template="macOS icon for {product_name}",
            aspect_ratio="1 / 1",
        ),
    ]
    session.add_all(items)
    session.commit()
    return items


class TestInspirationModel:

    def test_create_item(self, db_session):
        from app.models.inspiration import InspirationItem

        item = InspirationItem(
            category="poster", sub_category="拼贴海报",
            preview_url="https://oss.example.com/test.webp",
            prompt_template="A poster for {product_name}...",
            aspect_ratio="9 / 16",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.category == "poster"
        assert item.sub_category == "拼贴海报"
        assert item.created_at is not None

    def test_create_minimal_item(self, db_session):
        from app.models.inspiration import InspirationItem

        item = InspirationItem(
            category="app", sub_category="App 图标",
            preview_url="https://oss.example.com/icon.webp",
            prompt_template="An app icon for {product_name}",
        )
        db_session.add(item)
        db_session.commit()
        assert item.id is not None
        assert item.aspect_ratio is None

    def test_query_by_category(self, db_session):
        from app.models.inspiration import InspirationItem
        _seed(db_session)

        results = db_session.query(InspirationItem).filter(
            InspirationItem.category == "poster"
        ).all()
        assert len(results) == 2


class TestInspirationAPI:

    @pytest.fixture
    def client(self, db_session):
        from app.api.inspiration_routes import router

        def override_get_db():
            yield db_session

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)

    def test_list_all_inspirations(self, db_session, client):
        _seed(db_session)
        resp = client.get("/api/v1/inspirations")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_by_category(self, db_session, client):
        _seed(db_session)
        resp = client.get("/api/v1/inspirations?category=poster")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(item["category"] == "poster" for item in data)

    def test_rewrites_static_absolute_preview_url_to_same_origin_path(self, db_session, client):
        from app.models.inspiration import InspirationItem

        db_session.add(InspirationItem(
            category="poster", sub_category="电影海报",
            preview_url="http://47.237.203.217/static/inspiration/assets/posters/algorithm-fog.webp",
            prompt_template="Movie poster for {product_name}",
            aspect_ratio="9 / 16",
        ))
        db_session.commit()

        resp = client.get("/api/v1/inspirations?category=poster")

        assert resp.status_code == 200
        assert resp.json()[0]["preview_url"] == "/static/inspiration/assets/posters/algorithm-fog.webp"

    def test_filter_by_sub_category(self, db_session, client):
        _seed(db_session)
        resp = client.get("/api/v1/inspirations?sub_category=App 图标")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["sub_category"] == "App 图标"

    def test_get_single_inspiration(self, db_session, client):
        items = _seed(db_session)
        resp = client.get(f"/api/v1/inspirations/{items[0].id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "poster"
        assert "prompt_template" in data

    def test_get_nonexistent_returns_404(self, db_session, client):
        resp = client.get("/api/v1/inspirations/99999")
        assert resp.status_code == 404

    def test_list_categories(self, db_session, client):
        _seed(db_session)
        resp = client.get("/api/v1/inspirations/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "poster" in data
        assert "app" in data
        assert "拼贴海报" in data["poster"]

    def test_search_by_natural_language(self, db_session, client):
        """自然语言搜索 — 如"运动鞋场景图"应匹配相关提示词"""
        _seed(db_session)
        resp = client.get("/api/v1/inspirations?q=poster")
        assert resp.status_code == 200
        data = resp.json()
        # 应匹配 prompt_template 中包含"poster"的项
        assert len(data) == 2  # 只有poster类的2个项
        assert all("poster" in item["prompt_template"].lower() for item in data)

    def test_search_chinese_natural_language(self, db_session, client):
        """中文自然语言搜索 — 如"海报"应匹配相关子分类"""
        _seed(db_session)
        resp = client.get("/api/v1/inspirations?q=海报")
        assert resp.status_code == 200
        data = resp.json()
        # 应匹配 sub_category 中包含"海报"的项
        assert len(data) == 1  # 只有1个包含"海报"的项（拼贴海报）
        assert "海报" in data[0]["sub_category"]

    def test_search_no_match(self, db_session, client):
        """搜索无匹配应返回空列表"""
        _seed(db_session)
        resp = client.get("/api/v1/inspirations?q=不存在的关键词xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0


def test_normalize_preview_url_host_agnostic_and_guards():
    from app.api.inspiration_routes import _normalize_preview_url
    # http / https / 任意 host 的 /static 绝对地址 → 同源相对路径
    assert _normalize_preview_url("http://47.237.203.217/static/a/b.webp") == "/static/a/b.webp"
    assert _normalize_preview_url("https://47.237.203.217/static/a/b.webp") == "/static/a/b.webp"
    assert _normalize_preview_url("https://moyaops.xyz/static/a/b.webp") == "/static/a/b.webp"
    # 非 /static 外链、已是相对路径、空串 → 原样放行（幂等）
    assert _normalize_preview_url("https://cdn.example.com/img/x.webp") == "https://cdn.example.com/img/x.webp"
    assert _normalize_preview_url("/static/a/b.webp") == "/static/a/b.webp"
    assert _normalize_preview_url("") == ""


def test_detail_endpoint_normalizes_static_url(db_session):
    from app.models.inspiration import InspirationItem
    from app.api.inspiration_routes import router
    item = InspirationItem(
        category="poster", sub_category="电影海报",
        preview_url="http://47.237.203.217/static/inspiration/assets/posters/x.webp",
        prompt_template="t", aspect_ratio="9 / 16",
    )
    db_session.add(item); db_session.commit(); db_session.refresh(item)

    def override_get_db():
        yield db_session
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app)
    resp = c.get(f"/api/v1/inspirations/{item.id}")
    assert resp.status_code == 200
    assert resp.json()["preview_url"] == "/static/inspiration/assets/posters/x.webp"
