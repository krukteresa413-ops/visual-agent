"""cascade delete: visual_assets + brand_profiles 的 project 外键补 ON DELETE CASCADE

删项目 500 的根因(第一性): projects 有 9 个子表外键, 其中 7 个已是 ON DELETE CASCADE,
唯独 visual_assets_project_id_fkey 与 brand_profiles_project_id_fkey 漏配, 为 NO ACTION。
删项目端点走 db.delete(project) 依赖 DB 级联, 项目下只要还有素材/项目级品牌资料, 就撞这
两个外键 → psycopg2 ForeignKeyViolation → 500(生产日志 DELETE /api/v1/projects/2 复现)。
本迁移把这两个外键补齐 CASCADE, 与其余 7 张子表对齐, 消除 7-vs-2 的不对称, 一次修好所有
删除路径(两个删除端点 + 手工删 + 未来代码)。

注意 brand_profiles.project_id 可空: ON DELETE CASCADE 只在被引用的 project 被删时对
"引用了该 project 的行"生效; 租户级品牌库(project_id=NULL, 无引用)不受任何影响, 安全保留。

纯约束替换, 表数据不变, 可 downgrade 回退为 NO ACTION。

Revision ID: 68b489e6ad2f
Revises: c3d4e5f6a7b8
Create Date: 2026-07-02 01:10:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "68b489e6ad2f"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # visual_assets.project_id → ON DELETE CASCADE
    op.drop_constraint(
        "visual_assets_project_id_fkey", "visual_assets", type_="foreignkey"
    )
    op.create_foreign_key(
        "visual_assets_project_id_fkey",
        "visual_assets",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # brand_profiles.project_id → ON DELETE CASCADE
    op.drop_constraint(
        "brand_profiles_project_id_fkey", "brand_profiles", type_="foreignkey"
    )
    op.create_foreign_key(
        "brand_profiles_project_id_fkey",
        "brand_profiles",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 还原为 NO ACTION(不带 ondelete)
    op.drop_constraint(
        "brand_profiles_project_id_fkey", "brand_profiles", type_="foreignkey"
    )
    op.create_foreign_key(
        "brand_profiles_project_id_fkey",
        "brand_profiles",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.drop_constraint(
        "visual_assets_project_id_fkey", "visual_assets", type_="foreignkey"
    )
    op.create_foreign_key(
        "visual_assets_project_id_fkey",
        "visual_assets",
        "projects",
        ["project_id"],
        ["id"],
    )
