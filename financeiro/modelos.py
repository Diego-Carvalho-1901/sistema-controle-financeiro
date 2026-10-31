"""Estruturas de dados do sistema."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

TIPOS = ("receita", "despesa", "venda")
CONTAS = ("negocio", "pessoal")


@dataclass(frozen=True)
class Lancamento:
    """Uma movimentação financeira (uma linha do CSV).

    `valor` é sempre positivo; é o `tipo` ("receita", "despesa" ou "venda")
    que diz se o dinheiro entrou ou saiu. `conta` separa o dinheiro do
    negócio do dinheiro pessoal.

    Uma venda é uma entrada de dinheiro do negócio que também registra o
    `produto` e a `quantidade`; o `valor` dela é o total da venda
    (quantidade x preço unitário). Nos outros tipos esses dois campos ficam
    como None.
    """

    data: date
    valor: Decimal
    tipo: str
    categoria: str
    descricao: str
    conta: str = "pessoal"
    produto: str | None = None
    quantidade: int | None = None

    def __post_init__(self) -> None:
        """Recusa combinações que não fazem sentido (lança ValueError)."""
        if self.tipo not in TIPOS:
            raise ValueError(f"tipo inválido: {self.tipo!r}")
        if self.conta not in CONTAS:
            raise ValueError(f"conta inválida: {self.conta!r}")
        if self.tipo == "venda":
            if self.conta != "negocio":
                raise ValueError("uma venda sempre pertence à conta 'negocio'")
            if not self.produto or self.quantidade is None or self.quantidade <= 0:
                raise ValueError("uma venda precisa de produto e quantidade > 0")
        elif self.produto is not None or self.quantidade is not None:
            raise ValueError("só vendas têm produto e quantidade")
