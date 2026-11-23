"""Cria a tabela com as regras de categoria aprendidas de cada usuário.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-23 16:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria regras_categoria (uma regra por palavra e usuário)."""
    op.create_table(
        "regras_categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("palavra", sa.String(length=50), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_regras_categoria_usuario_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_regras_categoria")),
        sa.UniqueConstraint(
            "usuario_id",
            "palavra",
            name=op.f("uq_regras_categoria_usuario_id_palavra"),
        ),
    )


def downgrade() -> None:
    """Apaga a tabela regras_categoria."""
    op.drop_table("regras_categoria")
