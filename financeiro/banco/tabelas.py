"""Tabelas do banco, mapeadas com o ORM do SQLAlchemy 2.x.

Valores em dinheiro são guardados como inteiro em centavos (R$ 12,34 vira
1234). Assim a conta é exata em qualquer banco: o SQLite não tem um tipo
decimal de verdade e guardaria NUMERIC como número de ponto flutuante.
"""

from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from financeiro.modelos import CONTAS, TIPOS


def _valores_sql(valores: tuple[str, ...]) -> str:
    """Monta a lista ('a', 'b') usada nas restrições CHECK."""
    return ", ".join(f"'{valor}'" for valor in valores)


class Base(DeclarativeBase):
    """Classe-mãe de todas as tabelas; guarda o `metadata` do esquema."""


class Usuario(Base):
    """Uma pessoa que usa o app (cada uma vê só os próprios lançamentos)."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))


class Categoria(Base):
    """Categoria de um usuário ("aluguel", "bolos"...).

    Cada usuário tem as próprias categorias, e o nome não se repete dentro
    do mesmo usuário.
    """

    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("usuario_id", "nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    nome: Mapped[str] = mapped_column(String(50))


class LancamentoTabela(Base):
    """Linha da tabela de lançamentos.

    Tem o nome "LancamentoTabela" para não confundir com o
    financeiro.modelos.Lancamento, que é o objeto usado nos cálculos.
    """

    __tablename__ = "lancamentos"
    __table_args__ = (
        CheckConstraint("valor_centavos > 0", name="valor_positivo"),
        CheckConstraint(f"tipo IN ({_valores_sql(TIPOS)})", name="tipo_valido"),
        CheckConstraint(f"conta IN ({_valores_sql(CONTAS)})", name="conta_valida"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    data: Mapped[date] = mapped_column(index=True)
    valor_centavos: Mapped[int]
    tipo: Mapped[str] = mapped_column(String(10))
    conta: Mapped[str] = mapped_column(String(10))
    descricao: Mapped[str] = mapped_column(String(200))
    produto: Mapped[str | None] = mapped_column(String(100))
    quantidade: Mapped[int | None]

    categoria: Mapped[Categoria] = relationship()
