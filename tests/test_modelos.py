"""Testes do modelo Lancamento (financeiro/modelos.py)."""

from datetime import date
from decimal import Decimal

import pytest

from financeiro.modelos import Lancamento

DATA = date(2026, 9, 1)


def test_conta_padrao_e_pessoal():
    lancamento = Lancamento(DATA, Decimal(10), "despesa", "lazer", "Cinema")

    assert lancamento.conta == "pessoal"
    assert lancamento.produto is None
    assert lancamento.quantidade is None


def test_venda_guarda_produto_e_quantidade():
    venda = Lancamento(
        DATA, Decimal(45), "venda", "bolos", "Bolo", "negocio", "Bolo", 3
    )

    assert venda.produto == "Bolo"
    assert venda.quantidade == 3


@pytest.mark.parametrize(
    ("campos", "mensagem"),
    [
        ({"tipo": "transferencia"}, "tipo inválido"),
        ({"conta": "empresa"}, "conta inválida"),
        ({"tipo": "venda", "produto": "Bolo", "quantidade": 1}, "conta 'negocio'"),
        ({"tipo": "venda", "conta": "negocio"}, "produto e quantidade"),
        (
            {"tipo": "venda", "conta": "negocio", "produto": "Bolo", "quantidade": 0},
            "produto e quantidade",
        ),
        ({"produto": "Bolo"}, "só vendas"),
    ],
)
def test_combinacoes_invalidas_sao_recusadas(campos, mensagem):
    dados = {
        "data": DATA,
        "valor": Decimal(10),
        "tipo": "despesa",
        "categoria": "geral",
        "descricao": "teste",
    }
    dados.update(campos)

    with pytest.raises(ValueError, match=mensagem):
        Lancamento(**dados)
