"""Testes dos cálculos (financeiro/calculos.py)."""

from datetime import date
from decimal import Decimal

from financeiro.calculos import (
    calcular_media,
    calcular_percentual,
    encontrar_maior_e_menor,
    filtrar_por_tipo,
    maior_categoria,
    ranking_categorias,
    somar,
    somar_por_categoria,
    somar_por_mes,
    tem_alta_concentracao,
)
from financeiro.modelos import Lancamento


def lanc(data: date, valor: str, tipo: str, categoria: str = "geral") -> Lancamento:
    """Atalho para criar lançamentos nos testes."""
    return Lancamento(data, Decimal(valor), tipo, categoria, "teste")


# --- Somas ---


def test_somar_usa_decimal_sem_erro_de_arredondamento():
    # Com float, 0.1 + 0.2 dá 0.30000000000000004.
    lancamentos = [
        lanc(date(2026, 9, 1), "0.10", "despesa"),
        lanc(date(2026, 9, 2), "0.20", "despesa"),
    ]

    assert somar(lancamentos) == Decimal("0.30")


def test_somar_lista_vazia_devolve_zero():
    assert somar([]) == 0


def test_filtrar_por_tipo():
    receita = lanc(date(2026, 9, 1), "100", "receita")
    despesa = lanc(date(2026, 9, 2), "30", "despesa")

    assert filtrar_por_tipo([receita, despesa], "despesa") == [despesa]


# --- Percentual e média (bugs de divisão por zero da issue [01]) ---


def test_percentual_sem_receitas_devolve_zero():
    assert calcular_percentual(Decimal(150), Decimal(0)) == 0


def test_percentual_calcula_normalmente():
    assert calcular_percentual(Decimal(25), Decimal(200)) == Decimal("12.5")


def test_media_sem_lancamentos_devolve_zero():
    assert calcular_media(Decimal(0), 0) == 0


def test_media_calcula_normalmente():
    assert calcular_media(Decimal(300), 4) == Decimal(75)


# --- Maior e menor lançamento ---


def test_menor_lancamento_na_primeira_linha():
    cafe = lanc(date(2026, 9, 2), "10.00", "despesa")
    salario = lanc(date(2026, 9, 1), "1800.00", "receita")
    almoco = lanc(date(2026, 9, 3), "45.90", "despesa")

    maior, menor = encontrar_maior_e_menor([cafe, salario, almoco])

    assert maior is salario
    assert menor is cafe


# --- Agrupamento por mês ---


def test_somar_por_mes_separa_anos_diferentes():
    lancamentos = [
        lanc(date(2026, 1, 5), "1000", "receita"),
        lanc(date(2027, 1, 5), "1200", "receita"),
        lanc(date(2026, 1, 20), "300", "receita"),
        lanc(date(2026, 1, 10), "50", "despesa"),
    ]

    receitas = somar_por_mes(lancamentos, "receita")

    assert receitas == {(2026, 1): Decimal(1300), (2027, 1): Decimal(1200)}


def test_somar_por_mes_ordena_cronologicamente():
    lancamentos = [
        lanc(date(2027, 1, 5), "10", "despesa"),
        lanc(date(2026, 12, 5), "20", "despesa"),
        lanc(date(2026, 2, 5), "30", "despesa"),
    ]

    meses = sorted(somar_por_mes(lancamentos, "despesa"))

    assert meses == [(2026, 2), (2026, 12), (2027, 1)]


# --- Categorias ---


def test_somar_por_categoria_mantem_ordem_de_aparicao():
    lancamentos = [
        lanc(date(2026, 9, 1), "40", "despesa", "transporte"),
        lanc(date(2026, 9, 2), "25", "despesa", "alimentacao"),
        lanc(date(2026, 9, 3), "10", "despesa", "transporte"),
        lanc(date(2026, 9, 4), "999", "receita", "salario"),
    ]

    totais = somar_por_categoria(lancamentos, "despesa")

    assert list(totais.items()) == [
        ("transporte", Decimal(50)),
        ("alimentacao", Decimal(25)),
    ]


def test_ranking_categorias_do_maior_para_o_menor():
    totais = {"lazer": Decimal(10), "moradia": Decimal(900), "mercado": Decimal(300)}

    assert [categoria for categoria, _ in ranking_categorias(totais)] == [
        "moradia",
        "mercado",
        "lazer",
    ]


def test_maior_categoria():
    totais = {"lazer": Decimal(10), "moradia": Decimal(900)}

    assert maior_categoria(totais) == ("moradia", Decimal(900))


def test_maior_categoria_sem_categorias():
    assert maior_categoria({}) == ("", 0)


def test_alta_concentracao_inclui_o_limite():
    assert tem_alta_concentracao(Decimal(20))
    assert not tem_alta_concentracao(Decimal("19.99"))
