"""Cria a tabela que registra os alertas de meta já enviados.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-23 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria alertas_meta (um alerta por categoria por mês)."""
    op.create_table(
        "alertas_meta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            name=op.f("fk_alertas_meta_categoria_id_categorias"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_alertas_meta_usuario_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alertas_meta")),
        sa.UniqueConstraint(
            "categoria_id",
            "ano",
            "mes",
            name=op.f("uq_alertas_meta_categoria_id_ano_mes"),
        ),
    )


def downgrade() -> None:
    """Apaga a tabela alertas_meta."""
    op.drop_table("alertas_meta")
