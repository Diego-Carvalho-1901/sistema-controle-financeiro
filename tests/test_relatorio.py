"""Testes da montagem do relatório (financeiro/relatorio.py)."""

from datetime import date
from decimal import Decimal

from financeiro.modelos import Lancamento
from financeiro.relatorio import gerar_relatorio, nome_do_mes


def test_nome_do_mes_em_portugues():
    assert nome_do_mes(1) == "janeiro"
    assert nome_do_mes(3) == "março"
    assert nome_do_mes(9) == "setembro"
    assert nome_do_mes(12) == "dezembro"


def test_relatorio_sem_despesas_nao_quebra():
    lancamentos = [
        Lancamento(date(2026, 9, 1), Decimal("1800.00"), "receita", "salario", "x"),
    ]

    relatorio = gerar_relatorio(lancamentos)

    assert "Total de Despesas: R$ 0.00" in relatorio
    assert "Receita Comprometida: 0.00 %" in relatorio
    assert "Mês: setembro/2026" in relatorio


def test_relatorio_mostra_totais_com_duas_casas():
    lancamentos = [
        Lancamento(date(2026, 9, 1), Decimal(1000), "receita", "salario", "x"),
        Lancamento(date(2026, 9, 2), Decimal("0.10"), "despesa", "lazer", "y"),
        Lancamento(date(2026, 9, 3), Decimal("0.20"), "despesa", "lazer", "z"),
    ]

    relatorio = gerar_relatorio(lancamentos)

    assert "Total de Despesas: R$ 0.30" in relatorio
    assert "Saldo: R$ 999.70" in relatorio


def test_relatorio_separa_negocio_e_pessoal():
    lancamentos = [
        Lancamento(
            date(2026, 9, 5),
            Decimal(180),
            "venda",
            "bolos",
            "Bolo",
            "negocio",
            "Bolo",
            4,
        ),
        Lancamento(date(2026, 9, 6), Decimal(80), "despesa", "insumos", "x", "negocio"),
        Lancamento(date(2026, 9, 1), Decimal(1000), "receita", "salario", "y"),
        Lancamento(date(2026, 9, 2), Decimal(300), "despesa", "aluguel", "z"),
    ]

    relatorio = gerar_relatorio(lancamentos)

    assert "Faturamento do negócio: R$ 180.00" in relatorio
    assert "Custos do negócio: R$ 80.00" in relatorio
    assert "Lucro do negócio: R$ 100.00 (margem de 55.56 %)" in relatorio
    assert "Saldo pessoal: R$ 700.00" in relatorio
