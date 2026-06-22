from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.project import Project  # noqa: F401 registers table


def make_client_with_db():
    from main import app
    from app.api.project_routes import get_db as project_get_db
    from app.api.auth_routes import get_db as auth_get_db

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    def override_db():
        yield session

    app.dependency_overrides[project_get_db] = override_db
    app.dependency_overrides[auth_get_db] = override_db
    return app, TestClient(app), session


def seed_project(session, name, tenant_id):
    project = Project(name=name, description="", tenant_id=tenant_id)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def register_and_login(client, email, password="Secret123!", tenant_name="客户A", role="member"):
    register = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "name": email.split("@")[0],
        "tenant_name": tenant_name,
        "role": role,
    })
    assert register.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_projects_require_authentication():
    app, client, session = make_client_with_db()
    try:
        resp = client.get("/api/v1/projects/")
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert resp.status_code == 401


def test_member_only_sees_own_tenant_projects():
    app, client, session = make_client_with_db()
    try:
        token_a = register_and_login(client, "a@example.com", tenant_name="Tenant A")
        token_b = register_and_login(client, "b@example.com", tenant_name="Tenant B")
        me_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
        me_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
        seed_project(session, "A Project", me_a["tenant_id"])
        seed_project(session, "B Project", me_b["tenant_id"])

        resp_a = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token_a}"})
        resp_b = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token_b}"})
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert resp_a.status_code == 200
    assert [project["name"] for project in resp_a.json()] == ["A Project"]
    assert resp_b.status_code == 200
    assert [project["name"] for project in resp_b.json()] == ["B Project"]


def test_platform_admin_can_list_all_projects():
    app, client, session = make_client_with_db()
    try:
        member_token = register_and_login(client, "member@example.com", tenant_name="Member Tenant")
        admin_token = register_and_login(client, "admin@example.com", tenant_name="Admin Tenant", role="platform_admin")
        member_tenant_id = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {member_token}"}).json()["tenant_id"]
        admin_tenant_id = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).json()["tenant_id"]
        seed_project(session, "Member Project", member_tenant_id)
        seed_project(session, "Admin Project", admin_tenant_id)

        resp = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {admin_token}"})
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert resp.status_code == 200
    assert {project["name"] for project in resp.json()} == {"Member Project", "Admin Project"}


def test_user_can_register_and_login_with_china_mobile_number():
    app, client, session = make_client_with_db()
    try:
        register = client.post("/api/v1/auth/register", json={
            "phone": "13800138000",
            "password": "Secret123!",
            "name": "手机用户",
            "tenant_name": "手机号租户",
        })
        assert register.status_code == 201
        assert register.json()["phone"] == "13800138000"
        assert register.json()["email"] is None

        login = client.post("/api/v1/auth/login", json={"identifier": "13800138000", "password": "Secret123!"})
        assert login.status_code == 200
        assert login.json()["user"]["phone"] == "13800138000"
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_register_rejects_invalid_china_mobile_number():
    app, client, session = make_client_with_db()
    try:
        resp = client.post("/api/v1/auth/register", json={
            "phone": "12345",
            "password": "Secret123!",
            "name": "坏手机号",
            "tenant_name": "坏租户",
        })
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert resp.status_code == 422


def test_register_requires_email_or_phone():
    app, client, session = make_client_with_db()
    try:
        resp = client.post("/api/v1/auth/register", json={
            "password": "Secret123!",
            "name": "无账号",
            "tenant_name": "无账号租户",
        })
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert resp.status_code == 422
