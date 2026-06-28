"""图四 迁移:users 加 credits 列 + 建 credit_orders 表(幂等)。

沿用仓库 migrate_auth_phone.py 的裸 SQL 幂等模式。credit_orders 也可由
Base.metadata.create_all 自动建,但这里显式建表/索引让迁移自洽、可重跑。
"""
from sqlalchemy import text

from app.db.session import engine


def column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name=:table AND column_name=:column
    """), {"table": table, "column": column}).first())


with engine.begin() as conn:
    if not column_exists(conn, "users", "credits"):
        conn.execute(text("ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_orders (
            id SERIAL PRIMARY KEY,
            out_trade_no VARCHAR(64) NOT NULL UNIQUE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount_fen INTEGER NOT NULL,
            credits INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            alipay_trade_no VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            paid_at TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_orders_user_id ON credit_orders (user_id)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_credit_orders_out_trade_no ON credit_orders (out_trade_no)"))

print("credits migration done")
