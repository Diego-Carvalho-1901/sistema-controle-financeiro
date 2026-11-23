"""Testes dos resumos feitos em SQL, com um conjunto de dados conhecido."""

from datetime import date
from decimal import Decimal

import pytest

from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.banco.resumos import (
    ResumoMes,
    resumo_negocio,
    resumo_por_categoria,
    resumo_por_mes,
    saldo_pessoal,
)
from financeiro.banco.tabelas import Base
from financeiro.calculos import (
    calcular_saldo_pessoal,
    resumir_negocio,
    somar_por_categoria,
)
from financeiro.modelos import Lancamento


def lanc(dia: str, valor: str, tipo: str, categoria: str, conta: str = "pessoal"):
    venda = tipo == "venda"
    return Lancamento(
        date.fromisoformat(dia),
        Decimal(valor),
        tipo,
        categoria,
        "x",
        conta,
        produto="Bolo" if venda else None,
        quantidade=1 if venda else None,
    )


# Dados conhecidos: dá para conferir cada total de cabeça.
DADOS = [
    # setembro/2026
    lanc("2026-09-01", "1800.00", "receita", "salario"),
    lanc("2026-09-03", "120.50", "despesa", "mercado"),
    lanc("2026-09-10", "79.50", "despesa", "mercado"),
    lanc("2026-09-12", "60.00", "despesa", "transporte"),
    lanc("2026-09-05", "45.00", "venda", "bolos", "negocio"),
    lanc("2026-09-06", "30.00", "venda", "bolos", "negocio"),
    lanc("2026-09-07", "40.00", "despesa", "insumos", "negocio"),
    # outubro/2026
    lanc("2026-10-02", "200.00", "receita", "servico", "negocio"),
    lanc("2026-10-04", "15.25", "despesa", "insumos", "negocio"),
    lanc("2026-10-08", "60.00", "despesa", "transporte"),
    # janeiro/2027: mesmo mês de outro ano não pode se misturar
    lanc("2027-01-15", "10.00", "despesa", "mercado"),
]


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    with criar_fabrica_de_sessoes(engine)() as sessao:
        yield sessao
    engine.dispose()


@pytest.fixture
def usuario(sessao) -> int:
    repo = RepositorioLancamentos(sessao)
    usuario_id = repo.criar_usuario("Ana")
    for lancamento in DADOS:
        repo.adicionar(usuario_id, lancamento)
    # Outro usuário com dados próprios: não pode aparecer nos resumos da Ana.
    outro = repo.criar_usuario("Bia")
    repo.adicionar(outro, lanc("2026-09-01", "999.00", "despesa", "mercado"))
    return usuario_id


def test_resumo_por_mes(sessao, usuario):
    assert resumo_por_mes(sessao, usuario) == [
        ResumoMes(2026, 9, Decimal(1800), Decimal(300), Decimal(75)),
        ResumoMes(2026, 10, Decimal(200), Decimal("75.25"), Decimal(0)),
        ResumoMes(2027, 1, Decimal(0), Decimal(10), Decimal(0)),
    ]


def test_saldo_do_mes_soma_entradas_e_subtrai_saidas(sessao, usuario):
    setembro = resumo_por_mes(sessao, usuario)[0]

    assert setembro.saldo == Decimal(1575)


def test_resumo_por_mes_respeita_o_periodo(sessao, usuario):
    meses = resumo_por_mes(
        sessao, usuario, inicio=date(2026, 10, 1), fim=date(2026, 12, 31)
    )

    assert [(m.ano, m.mes) for m in meses] == [(2026, 10)]


def test_resumo_por_categoria_do_maior_para_o_menor(sessao, usuario):
    assert resumo_por_categoria(sessao, usuario) == [
        ("mercado", Decimal(210)),
        ("transporte", Decimal(120)),
        ("insumos", Decimal("55.25")),
    ]


def test_resumo_por_categoria_filtra_tipo_conta_e_periodo(sessao, usuario):
    vendas = resumo_por_categoria(sessao, usuario, tipo="venda")
    pessoais_out = resumo_por_categoria(
        sessao,
        usuario,
        conta="pessoal",
        inicio=date(2026, 10, 1),
        fim=date(2026, 10, 31),
    )

    assert vendas == [("bolos", Decimal(75))]
    assert pessoais_out == [("transporte", Decimal(60))]


def test_resumo_negocio(sessao, usuario):
    resumo = resumo_negocio(sessao, usuario)

    assert resumo.faturamento == Decimal(275)  # 45 + 30 + 200
    assert resumo.custos == Decimal("55.25")  # 40 + 15,25
    assert resumo.lucro == Decimal("219.75")


def test_saldo_pessoal(sessao, usuario):
    # 1800 - (120,50 + 79,50 + 60 + 60 + 10)
    assert saldo_pessoal(sessao, usuario) == Decimal(1470)


def test_usuario_sem_lancamentos_tem_resumos_zerados(sessao, usuario):
    vazio = RepositorioLancamentos(sessao).criar_usuario("Caio")

    assert resumo_por_mes(sessao, vazio) == []
    assert resumo_por_categoria(sessao, vazio) == []
    assert resumo_negocio(sessao, vazio).lucro == 0
    assert saldo_pessoal(sessao, vazio) == 0


def test_sql_e_python_chegam_ao_mesmo_resultado(sessao, usuario):
    """Os cálculos antigos (em Python) servem de gabarito para os novos."""
    lancamentos = RepositorioLancamentos(sessao).listar(usuario)

    assert resumo_negocio(sessao, usuario) == resumir_negocio(lancamentos)
    assert saldo_pessoal(sessao, usuario) == calcular_saldo_pessoal(lancamentos)
    assert dict(resumo_por_categoria(sessao, usuario)) == somar_por_categoria(
        lancamentos, "despesa"
    )
