"""Cria a tabela de metas mensais por categoria.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23 15:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela metas (no máximo uma meta por categoria)."""
    op.create_table(
        "metas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.CheckConstraint("valor_centavos > 0", name=op.f("ck_metas_valor_positivo")),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            name=op.f("fk_metas_categoria_id_categorias"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name=op.f("fk_metas_usuario_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metas")),
        sa.UniqueConstraint("categoria_id", name=op.f("uq_metas_categoria_id")),
    )
    op.create_index(op.f("ix_metas_usuario_id"), "metas", ["usuario_id"])


def downgrade() -> None:
    """Apaga a tabela metas."""
    op.drop_index(op.f("ix_metas_usuario_id"), table_name="metas")
    op.drop_table("metas")
