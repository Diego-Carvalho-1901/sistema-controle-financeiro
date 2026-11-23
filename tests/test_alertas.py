"""Testes da regra do alerta de meta."""

from decimal import Decimal

import pytest

from financeiro.alertas import metas_para_alertar
from financeiro.banco.metas import SituacaoMeta


def situacao(gasto: str, meta: str = "100", categoria: str = "mercado"):
    return SituacaoMeta(categoria, Decimal(meta), Decimal(gasto))


@pytest.mark.parametrize(
    ("gasto", "alerta"),
    [
        ("0", False),
        ("79.99", False),
        ("80", True),  # exatamente 80% já alerta
        ("80.01", True),
        ("100", True),
        ("250", True),  # estourou a meta
    ],
)
def test_alerta_a_partir_de_80_por_cento(gasto, alerta):
    assert bool(metas_para_alertar([situacao(gasto)], set())) is alerta


def test_nao_alerta_de_novo_a_mesma_categoria():
    assert metas_para_alertar([situacao("90")], {"mercado"}) == []


def test_alerta_so_as_categorias_novas():
    situacoes = [
        situacao("90", categoria="mercado"),
        situacao("85", categoria="lazer"),
        situacao("10", categoria="saude"),
    ]

    alertas = metas_para_alertar(situacoes, ja_alertadas={"mercado"})

    assert [s.categoria for s in alertas] == ["lazer"]


def test_limite_pode_ser_outro():
    assert metas_para_alertar([situacao("50")], set(), limite=Decimal(50))
