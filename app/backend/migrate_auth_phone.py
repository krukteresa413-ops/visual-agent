from sqlalchemy import text
from app.db.session import engine


def column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name=:table AND column_name=:column
    """), {"table": table, "column": column}).first())

with engine.begin() as conn:
    if not column_exists(conn, "users", "phone"):
        conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"))
    conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
print("phone migration done")
