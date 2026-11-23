"""Adiciona aos usuários o id da conta no Telegram.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23 11:48:35.044889

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a coluna telegram_id (opcional e sem repetição)."""
    # batch_alter_table: no SQLite recria a tabela; no PostgreSQL vira ALTER.
    with op.batch_alter_table("usuarios") as tabela:
        tabela.add_column(sa.Column("telegram_id", sa.BigInteger(), nullable=True))
        tabela.create_unique_constraint(
            op.f("uq_usuarios_telegram_id"), ["telegram_id"]
        )


def downgrade() -> None:
    """Remove a coluna telegram_id."""
    with op.batch_alter_table("usuarios") as tabela:
        tabela.drop_constraint(op.f("uq_usuarios_telegram_id"), type_="unique")
        tabela.drop_column("telegram_id")
