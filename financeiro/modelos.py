"""Estruturas de dados do sistema."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

TIPOS = ("receita", "despesa")


@dataclass(frozen=True)
class Lancamento:
    """Uma movimentação financeira (uma linha do CSV).

    `valor` é sempre positivo; é o `tipo` ("receita" ou "despesa") que diz
    se o dinheiro entrou ou saiu.
    """

    data: date
    valor: Decimal
    tipo: str
    categoria: str
    descricao: str
