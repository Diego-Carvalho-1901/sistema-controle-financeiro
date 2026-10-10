"""Testes dos bugs conhecidos do relatório (issue [01])."""

from datetime import datetime

from analise import calcular_media, calcular_percentual, encontrar_maior_e_menor

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
