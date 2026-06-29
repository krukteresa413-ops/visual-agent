"""图三: 画布 AI 对话历史持久化 + 租户隔离 测试(真实 auth + 真实 DB 查询, 无逻辑 mock)。"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.models.project import Project  # noqa: F401 注册 projects 表
from app.models.chat_conversation import ChatConversation  # noqa: F401 注册 chat_conversations 表


def make_client():
    from main import app

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    return app, TestClient(app), session


def register_and_login(client, email, tenant_name):
    r = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Secret123!", "name": email.split("@")[0], "tenant_name": tenant_name,
    })
    assert r.status_code == 201, r.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Secret123!"})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _tenant_id(client, token):
    return client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["tenant_id"]


def seed_project(session, name, tenant_id):
    p = Project(name=name, description="", tenant_id=tenant_id)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def test_history_requires_auth():
    app, client, session = make_client()
    try:
        resp = client.get("/api/v1/chat/history", params={"project_id": 1})
    finally:
        app.dependency_overrides.clear()
        session.close()
    assert resp.status_code == 401


def test_history_save_and_load_roundtrip():
    app, client, session = make_client()
    try:
        token = register_and_login(client, "a@example.com", "Tenant A")
        proj = seed_project(session, "A Project", _tenant_id(client, token))
        headers = {"Authorization": f"Bearer {token}"}
        msgs = [
            {"id": "1", "role": "user", "step": "用户指令", "content": "生成一台冰箱", "status": "user", "percent": 0, "assets": []},
            {"id": "2", "role": "assistant", "step": "完成", "content": "生成完成", "status": "completed", "percent": 100, "assets": [{"url": "/uploads/generated/x.png"}]},
        ]
        save = client.put("/api/v1/chat/history", json={"project_id": proj.id, "messages": msgs}, headers=headers)
        assert save.status_code == 200, save.text
        load = client.get("/api/v1/chat/history", params={"project_id": proj.id}, headers=headers)
        assert load.status_code == 200
        got = load.json()["messages"]
        assert len(got) == 2
        assert got[0]["content"] == "生成一台冰箱"
        assert got[1]["assets"][0]["url"] == "/uploads/generated/x.png"
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_history_upsert_overwrites():
    app, client, session = make_client()
    try:
        token = register_and_login(client, "a@example.com", "Tenant A")
        proj = seed_project(session, "A Project", _tenant_id(client, token))
        headers = {"Authorization": f"Bearer {token}"}
        client.put("/api/v1/chat/history", json={"project_id": proj.id, "messages": [{"id": "1", "role": "user", "content": "v1"}]}, headers=headers)
        client.put("/api/v1/chat/history", json={"project_id": proj.id, "messages": [{"id": "1", "role": "user", "content": "v2"}]}, headers=headers)
        got = client.get("/api/v1/chat/history", params={"project_id": proj.id}, headers=headers).json()["messages"]
        assert len(got) == 1 and got[0]["content"] == "v2"
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_history_tenant_isolation():
    app, client, session = make_client()
    try:
        token_a = register_and_login(client, "a@example.com", "Tenant A")
        token_b = register_and_login(client, "b@example.com", "Tenant B")
        proj_a = seed_project(session, "A Project", _tenant_id(client, token_a))
        client.put(
            "/api/v1/chat/history",
            json={"project_id": proj_a.id, "messages": [{"id": "1", "role": "user", "content": "A 的私密对话"}]},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        # B 用自己的 token 读 A 的 project → 租户隔离, 读不到
        load_b = client.get("/api/v1/chat/history", params={"project_id": proj_a.id}, headers={"Authorization": f"Bearer {token_b}"})
        assert load_b.status_code == 200
        assert load_b.json()["messages"] == []
        # A 自己能读到
        load_a = client.get("/api/v1/chat/history", params={"project_id": proj_a.id}, headers={"Authorization": f"Bearer {token_a}"})
        assert load_a.json()["messages"][0]["content"] == "A 的私密对话"
    finally:
        app.dependency_overrides.clear()
        session.close()
