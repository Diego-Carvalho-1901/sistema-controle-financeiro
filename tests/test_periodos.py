"""Testes dos períodos (mês e semana)."""

from datetime import date

import pytest

from financeiro.periodos import mes_de, semana_de


@pytest.mark.parametrize(
    ("dia", "fim"),
    [
        (date(2026, 11, 23), date(2026, 11, 30)),
        (date(2026, 12, 31), date(2026, 12, 31)),
        (date(2028, 2, 10), date(2028, 2, 29)),  # ano bissexto
        (date(2027, 2, 10), date(2027, 2, 28)),
    ],
)
def test_mes_de(dia, fim):
    assert mes_de(dia) == (dia.replace(day=1), fim)


@pytest.mark.parametrize(
    "dia", [date(2026, 11, 23), date(2026, 11, 26), date(2026, 11, 29)]
)
def test_semana_vai_de_segunda_a_domingo(dia):
    assert semana_de(dia) == (date(2026, 11, 23), date(2026, 11, 29))


def test_semana_que_cruza_o_ano():
    assert semana_de(date(2027, 1, 1)) == (date(2026, 12, 28), date(2027, 1, 3))
