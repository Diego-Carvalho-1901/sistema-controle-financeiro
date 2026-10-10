"""Testes dos bugs conhecidos do relatório (issue [01])."""

from datetime import datetime

from analise import (
    calcular_media,
    calcular_percentual,
    encontrar_maior_e_menor,
    nome_do_mes,
    somar_por_mes,
)

# --- Bug: divisão por zero sem receitas ou sem despesas ---


def test_percentual_sem_receitas_devolve_zero():
    assert calcular_percentual(150.0, 0) == 0.0


def test_percentual_calcula_normalmente():
    assert calcular_percentual(25.0, 200.0) == 12.5


def test_media_sem_movimentacoes_devolve_zero():
    assert calcular_media(0, 0) == 0.0


def test_media_calcula_normalmente():
    assert calcular_media(300.0, 4) == 75.0


# --- Bug: primeira linha sendo a menor movimentação ---


def test_menor_movimentacao_na_primeira_linha():
    movimentacoes = [
        [datetime(2026, 9, 2), 10.0, "despesa", "alimentacao", "Cafe"],
        [datetime(2026, 9, 1), 1800.0, "receita", "salario", "Salario"],
        [datetime(2026, 9, 3), 45.9, "despesa", "alimentacao", "Almoco"],
    ]

    maior, menor = encontrar_maior_e_menor(movimentacoes)

    assert maior[1] == 1800.0
    assert menor[1] == 10.0
    assert menor[4] == "Cafe"


# --- Bug: nomes dos meses em inglês ---


def test_nome_do_mes_em_portugues():
    assert nome_do_mes(1) == "janeiro"
    assert nome_do_mes(3) == "março"
    assert nome_do_mes(9) == "setembro"
    assert nome_do_mes(12) == "dezembro"


# --- Bug: meses de anos diferentes somados juntos ---


def test_somar_por_mes_separa_anos_diferentes():
    movimentacoes = [
        [datetime(2026, 1, 5), 1000.0, "receita", "salario", "Jan 2026"],
        [datetime(2027, 1, 5), 1200.0, "receita", "salario", "Jan 2027"],
        [datetime(2026, 1, 20), 300.0, "receita", "freelance", "Extra"],
        [datetime(2026, 1, 10), 50.0, "despesa", "lazer", "Cinema"],
    ]

    receitas = somar_por_mes(movimentacoes, "receita")

    assert receitas == {(2026, 1): 1300.0, (2027, 1): 1200.0}


def test_somar_por_mes_ordena_cronologicamente():
    movimentacoes = [
        [datetime(2027, 1, 5), 10.0, "despesa", "lazer", "a"],
        [datetime(2026, 12, 5), 20.0, "despesa", "lazer", "b"],
        [datetime(2026, 2, 5), 30.0, "despesa", "lazer", "c"],
    ]

    meses = sorted(somar_por_mes(movimentacoes, "despesa"))

    assert meses == [(2026, 2), (2026, 12), (2027, 1)]
