"""Adiciona aos lançamentos o momento em que foram gravados.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-23 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identificadores usados pelo Alembic para ordenar as migrações.
revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a coluna criado_em; as linhas antigas recebem o momento atual."""
    with op.batch_alter_table("lancamentos") as tabela:
        tabela.add_column(
            sa.Column(
                "criado_em",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            )
        )
        tabela.create_index(op.f("ix_lancamentos_criado_em"), ["criado_em"])


def downgrade() -> None:
    """Remove a coluna criado_em."""
    with op.batch_alter_table("lancamentos") as tabela:
        tabela.drop_index(op.f("ix_lancamentos_criado_em"))
        tabela.drop_column("criado_em")
