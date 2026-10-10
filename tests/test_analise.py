"""Testes dos bugs conhecidos do relatório (issue [01])."""

from analise import calcular_media, calcular_percentual

# --- Bug: divisão por zero sem receitas ou sem despesas ---


def test_percentual_sem_receitas_devolve_zero():
    assert calcular_percentual(150.0, 0) == 0.0


def test_percentual_calcula_normalmente():
    assert calcular_percentual(25.0, 200.0) == 12.5


def test_media_sem_movimentacoes_devolve_zero():
    assert calcular_media(0, 0) == 0.0


def test_media_calcula_normalmente():
    assert calcular_media(300.0, 4) == 75.0
