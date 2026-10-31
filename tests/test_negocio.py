"""Testes do cálculo de lucro do negócio e do saldo pessoal (issue [05])."""

from datetime import date
from decimal import Decimal

from financeiro.calculos import (
    ResumoNegocio,
    calcular_saldo_pessoal,
    filtrar_por_conta,
    resumir_negocio,
)
from financeiro.modelos import Lancamento

DATA = date(2026, 9, 1)


def venda(valor: str, quantidade: int = 1) -> Lancamento:
    return Lancamento(
        DATA, Decimal(valor), "venda", "bolos", "Bolo", "negocio", "Bolo", quantidade
    )


def mov(valor: str, tipo: str, conta: str) -> Lancamento:
    return Lancamento(DATA, Decimal(valor), tipo, "geral", "teste", conta)


# Uma confeiteira MEI num mês: vende bolos, faz uma encomenda avulsa,
# compra insumos para o negócio e tem as contas da casa.
MES = [
    venda("45.00", 3),
    venda("150.00", 10),
    mov("200.00", "receita", "negocio"),  # encomenda de festa
    mov("120.50", "despesa", "negocio"),  # farinha, açúcar, ovos
    mov("30.00", "despesa", "negocio"),  # embalagens
    mov("1500.00", "receita", "pessoal"),  # salário de outro emprego
    mov("900.00", "despesa", "pessoal"),  # aluguel
]


def test_lucro_do_negocio():
    resumo = resumir_negocio(MES)

    assert resumo.faturamento == Decimal("395.00")  # 45 + 150 + 200
    assert resumo.custos == Decimal("150.50")  # 120.50 + 30
    assert resumo.lucro == Decimal("244.50")


def test_conta_pessoal_nao_entra_no_lucro():
    so_negocio = [item for item in MES if item.conta == "negocio"]

    assert resumir_negocio(MES) == resumir_negocio(so_negocio)


def test_saldo_pessoal_nao_inclui_o_negocio():
    assert calcular_saldo_pessoal(MES) == Decimal("600.00")  # 1500 - 900


def test_prejuizo_da_lucro_negativo():
    resumo = resumir_negocio([venda("50.00"), mov("80.00", "despesa", "negocio")])

    assert resumo.lucro == Decimal("-30.00")
    assert resumo.margem == Decimal(-60)


def test_margem_de_lucro():
    assert ResumoNegocio(Decimal(400), Decimal(100)).margem == Decimal(75)


def test_sem_negocio_tudo_zero():
    pessoal = [mov("1500.00", "receita", "pessoal")]

    resumo = resumir_negocio(pessoal)

    assert resumo == ResumoNegocio(Decimal(0), Decimal(0))
    assert resumo.lucro == 0
    assert resumo.margem == 0


def test_filtrar_por_conta():
    assert len(filtrar_por_conta(MES, "negocio")) == 5
    assert len(filtrar_por_conta(MES, "pessoal")) == 2
