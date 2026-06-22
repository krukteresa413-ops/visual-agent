from __future__ import annotations

import os
import secrets
from pathlib import Path

from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models.auth import Tenant, User
from app.services.auth_service import hash_password

ADMIN_EMAIL = os.getenv("MOYAG_ADMIN_EMAIL", "admin@moyag.local")
CREDENTIAL_PATH = Path("/root/moyag-admin-credentials.txt")


def column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name=:table AND column_name=:column
    """), {"table": table, "column": column}).first())


def main() -> None:
    from main import app  # noqa: F401 imports all models/routes before create_all
    from app.db.session import Base

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        if not column_exists(conn, "projects", "tenant_id"):
            conn.execute(text("ALTER TABLE projects ADD COLUMN tenant_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_tenant_id ON projects (tenant_id)"))

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "muyuanjia").first()
        if not tenant:
            tenant = Tenant(name="沐源甲科技", slug="muyuanjia")
            db.add(tenant)
            db.flush()

        db.execute(text("UPDATE projects SET tenant_id = :tenant_id WHERE tenant_id IS NULL"), {"tenant_id": tenant.id})

        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            password = secrets.token_urlsafe(18)
            admin = User(
                tenant_id=tenant.id,
                email=ADMIN_EMAIL,
                password_hash=hash_password(password),
                name="MOYAG Admin",
                role="platform_admin",
            )
            db.add(admin)
            CREDENTIAL_PATH.write_text(f"email={ADMIN_EMAIL}\npassword={password}\n", encoding="utf-8")
            CREDENTIAL_PATH.chmod(0o600)
        db.commit()
        print({"tenant_id": tenant.id, "admin_email": ADMIN_EMAIL, "created_admin_credentials": CREDENTIAL_PATH.exists()})
    finally:
        db.close()


if __name__ == "__main__":
    main()
