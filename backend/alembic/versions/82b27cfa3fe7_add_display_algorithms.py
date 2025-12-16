"""Add display algorithms table and link gain_algorithm via id"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "82b27cfa3fe7"
down_revision = "979506117e6b"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None

ALGORITHMS: Sequence[dict[str, str | int | None]] = [
    {"id": 1, "code": "percentile-gamma", "name": "Percentile + Gamma", "description": "2%-98%拉伸后叠加 Gamma 修正"},
    {"id": 2, "code": "percentile", "name": "Percentile Stretch", "description": "2%-98% 分位数线性拉伸"},
    {"id": 3, "code": "gamma", "name": "Gamma Correction", "description": "Gamma 曲线"},
    {"id": 4, "code": "linear", "name": "Linear Stretch", "description": "线性归一化"},
    {"id": 5, "code": "log", "name": "Logarithmic Stretch", "description": "对数压缩"},
    {"id": 6, "code": "histogram", "name": "Histogram Equalization", "description": "直方图均衡"},
    {"id": 7, "code": "raw", "name": "Raw Data", "description": "不做拉伸"},
]


def upgrade() -> None:
    op.create_table(
        "display_algorithms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    algorithms_table = sa.table(
        "display_algorithms",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(algorithms_table, ALGORITHMS)

    op.add_column(
        "spectral_display_modes",
        sa.Column("gain_algorithm_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "annotation_detail_modes",
        sa.Column("gain_algorithm_id", sa.Integer(), nullable=True),
    )

    bind = op.get_bind()
    for algorithm in ALGORITHMS:
        params = {"alg_id": algorithm["id"], "code": algorithm["code"]}
        bind.execute(
            sa.text(
                "UPDATE spectral_display_modes "
                "SET gain_algorithm_id = :alg_id "
                "WHERE gain_algorithm = :code"
            ),
            params,
        )
        bind.execute(
            sa.text(
                "UPDATE annotation_detail_modes "
                "SET gain_algorithm_id = :alg_id "
                "WHERE gain_algorithm = :code"
            ),
            params,
        )

    bind.execute(
        sa.text(
            "UPDATE spectral_display_modes "
            "SET gain_algorithm_id = :alg_id "
            "WHERE gain_algorithm_id IS NULL"
        ),
        {"alg_id": 4},
    )
    bind.execute(
        sa.text(
            "UPDATE annotation_detail_modes "
            "SET gain_algorithm_id = :alg_id "
            "WHERE gain_algorithm_id IS NULL"
        ),
        {"alg_id": 4},
    )

    op.alter_column("spectral_display_modes", "gain_algorithm_id", nullable=False)
    op.alter_column("annotation_detail_modes", "gain_algorithm_id", nullable=False)

    op.create_foreign_key(
        "spectral_modes_gain_algorithm_fk",
        "spectral_display_modes",
        "display_algorithms",
        ["gain_algorithm_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "detail_modes_gain_algorithm_fk",
        "annotation_detail_modes",
        "display_algorithms",
        ["gain_algorithm_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column("spectral_display_modes", "gain_algorithm")
    op.drop_column("annotation_detail_modes", "gain_algorithm")


def downgrade() -> None:
    op.add_column(
        "annotation_detail_modes",
        sa.Column("gain_algorithm", sa.String(length=100), nullable=False, server_default="linear"),
    )
    op.add_column(
        "spectral_display_modes",
        sa.Column("gain_algorithm", sa.String(length=100), nullable=False, server_default="linear"),
    )

    bind = op.get_bind()
    algorithms_lookup = {alg["id"]: alg["code"] for alg in ALGORITHMS}

    result = bind.execute(sa.text("SELECT id, gain_algorithm_id FROM spectral_display_modes"))
    for row in result:
        bind.execute(
            sa.text(
                "UPDATE spectral_display_modes "
                "SET gain_algorithm = :code WHERE id = :id"
            ),
            {"code": algorithms_lookup.get(row.gain_algorithm_id, "linear"), "id": row.id},
        )

    result = bind.execute(sa.text("SELECT id, gain_algorithm_id FROM annotation_detail_modes"))
    for row in result:
        bind.execute(
            sa.text(
                "UPDATE annotation_detail_modes "
                "SET gain_algorithm = :code WHERE id = :id"
            ),
            {"code": algorithms_lookup.get(row.gain_algorithm_id, "linear"), "id": row.id},
        )

    op.drop_constraint("detail_modes_gain_algorithm_fk", "annotation_detail_modes", type_="foreignkey")
    op.drop_constraint("spectral_modes_gain_algorithm_fk", "spectral_display_modes", type_="foreignkey")
    op.drop_column("annotation_detail_modes", "gain_algorithm_id")
    op.drop_column("spectral_display_modes", "gain_algorithm_id")
    op.drop_table("display_algorithms")
