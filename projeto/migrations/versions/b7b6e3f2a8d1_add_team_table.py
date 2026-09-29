"""add_team_table

Revision ID: b7b6e3f2a8d1
Revises: a4009575c6e0
Create Date: 2026-05-29 14:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7b6e3f2a8d1"
down_revision: Union[str, None] = "a4009575c6e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company.id"],
            name=op.f("fk_team_company_id_company"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team")),
        sa.UniqueConstraint("company_id", "name", name=op.f("uq_team_company_name")),
    )
    op.create_index(op.f("ix_team_company_id"), "team", ["company_id"], unique=False)

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("team_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_user_team_id"), ["team_id"], unique=False)
        batch_op.create_foreign_key(
            batch_op.f("fk_user_team_id_team"),
            "team",
            ["team_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_user_team_id_team"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_user_team_id"))
        batch_op.drop_column("team_id")

    op.drop_index(op.f("ix_team_company_id"), table_name="team")
    op.drop_table("team")
