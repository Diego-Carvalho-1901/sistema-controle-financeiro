"""Cria as tabelas de usuários, categorias e lançamentos.

Revision ID: 0001
Revises:
Create Date: 2026-11-11 00:53:00.976525

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria o esquema inicial."""
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuarios")),
    )
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_categorias_usuario_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categorias")),
        sa.UniqueConstraint(
            "usuario_id", "nome", name=op.f("uq_categorias_usuario_id_nome")
        ),
    )
    op.create_table(
        "lancamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("conta", sa.String(length=10), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("produto", sa.String(length=100), nullable=True),
        sa.Column("quantidade", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "conta IN ('negocio', 'pessoal')", name=op.f("ck_lancamentos_conta_valida")
        ),
        sa.CheckConstraint(
            "tipo IN ('receita', 'despesa', 'venda')",
            name=op.f("ck_lancamentos_tipo_valido"),
        ),
        sa.CheckConstraint(
            "valor_centavos > 0", name=op.f("ck_lancamentos_valor_positivo")
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            name=op.f("fk_lancamentos_categoria_id_categorias"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_lancamentos_usuario_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lancamentos")),
    )
    op.create_index(op.f("ix_lancamentos_data"), "lancamentos", ["data"])
    op.create_index(op.f("ix_lancamentos_usuario_id"), "lancamentos", ["usuario_id"])


def downgrade() -> None:
    """Desfaz o esquema inicial (apaga as três tabelas)."""
    op.drop_index(op.f("ix_lancamentos_usuario_id"), table_name="lancamentos")
    op.drop_index(op.f("ix_lancamentos_data"), table_name="lancamentos")
    op.drop_table("lancamentos")
    op.drop_table("categorias")
    op.drop_table("usuarios")
