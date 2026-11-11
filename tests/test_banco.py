"""Testes do repositório de lançamentos com SQLite em memória."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.banco.repositorio import (
    RepositorioLancamentos,
    centavos_para_reais,
    reais_para_centavos,
)
from financeiro.banco.tabelas import Base, Categoria, LancamentoTabela
from financeiro.calculos import resumir_negocio
from financeiro.modelos import Lancamento


@pytest.fixture
def sessao():
    """Banco novo e vazio em memória para cada teste."""
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    Sessao = criar_fabrica_de_sessoes(engine)
    with Sessao() as sessao:
        yield sessao
    engine.dispose()


@pytest.fixture
def repo(sessao):
    return RepositorioLancamentos(sessao)


def despesa(dia: int, valor: str, categoria: str = "mercado") -> Lancamento:
    return Lancamento(date(2026, 9, dia), Decimal(valor), "despesa", categoria, "x")


def test_grava_e_le_o_mesmo_lancamento(repo):
    usuario = repo.criar_usuario("Ana")
    venda = Lancamento(
        date(2026, 9, 1),
        Decimal("45.90"),
        "venda",
        "bolos",
        "Bolo",
        "negocio",
        "Bolo de cenoura",
        3,
    )

    repo.adicionar(usuario, venda)

    assert repo.listar(usuario) == [venda]


def test_cada_usuario_ve_so_os_proprios_lancamentos(repo):
    ana = repo.criar_usuario("Ana")
    bia = repo.criar_usuario("Bia")
    repo.adicionar(ana, despesa(1, "10"))
    repo.adicionar(bia, despesa(2, "20"))

    assert [lanc.valor for lanc in repo.listar(ana)] == [Decimal(10)]
    assert [lanc.valor for lanc in repo.listar(bia)] == [Decimal(20)]


def test_lista_em_ordem_de_data_e_filtra_periodo(repo):
    usuario = repo.criar_usuario("Ana")
    for dia in (20, 5, 12):
        repo.adicionar(usuario, despesa(dia, "1"))

    todos = repo.listar(usuario)
    meio = repo.listar(usuario, inicio=date(2026, 9, 6), fim=date(2026, 9, 20))

    assert [lanc.data.day for lanc in todos] == [5, 12, 20]
    assert [lanc.data.day for lanc in meio] == [12, 20]


def test_categoria_e_criada_uma_vez_por_usuario(repo, sessao):
    ana = repo.criar_usuario("Ana")
    bia = repo.criar_usuario("Bia")
    repo.adicionar(ana, despesa(1, "1", "mercado"))
    repo.adicionar(ana, despesa(2, "1", "mercado"))
    repo.adicionar(bia, despesa(3, "1", "mercado"))

    assert sessao.scalar(select(func.count()).select_from(Categoria)) == 2


def test_calculos_funcionam_com_dados_do_banco(repo):
    usuario = repo.criar_usuario("Ana")
    repo.adicionar(
        usuario,
        Lancamento(
            date(2026, 9, 1), Decimal("100.10"), "receita", "servico", "x", "negocio"
        ),
    )
    repo.adicionar(
        usuario,
        Lancamento(
            date(2026, 9, 2), Decimal("30.05"), "despesa", "insumos", "x", "negocio"
        ),
    )

    resumo = resumir_negocio(repo.listar(usuario))

    assert resumo.lucro == Decimal("70.05")


def test_banco_recusa_lancamento_de_usuario_inexistente(repo, sessao):
    with pytest.raises(IntegrityError):
        repo.adicionar(999, despesa(1, "10"))


def test_banco_recusa_valor_negativo_mesmo_sem_passar_pelo_modelo(repo, sessao):
    usuario = repo.criar_usuario("Ana")
    categoria = Categoria(usuario_id=usuario, nome="mercado")
    sessao.add(
        LancamentoTabela(
            usuario_id=usuario,
            categoria=categoria,
            data=date(2026, 9, 1),
            valor_centavos=-100,
            tipo="despesa",
            conta="pessoal",
            descricao="x",
        )
    )

    with pytest.raises(IntegrityError):
        sessao.flush()


@pytest.mark.parametrize(
    ("reais", "centavos"),
    [("12.34", 1234), ("0.01", 1), ("100", 10000), ("2.5", 250)],
)
def test_conversao_reais_centavos_ida_e_volta(reais, centavos):
    assert reais_para_centavos(Decimal(reais)) == centavos
    assert centavos_para_reais(centavos) == Decimal(reais)


def test_recusa_fracao_de_centavo():
    with pytest.raises(ValueError, match="2 casas"):
        reais_para_centavos(Decimal("1.005"))
