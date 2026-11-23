"""Testes das consultas de métricas de uso."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, update

from financeiro.banco.conexao import criar_fabrica_de_sessoes
from financeiro.banco.metricas import (
    SemanaDeUso,
    calcular_metricas,
    usuarios_ativos_por_semana,
)
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.banco.tabelas import LancamentoTabela
from financeiro.modelos import Lancamento

HOJE = date(2026, 11, 25)  # quarta; semana atual começa em 23/11


@pytest.fixture
def repo(engine):
    with criar_fabrica_de_sessoes(engine)() as sessao:
        yield RepositorioLancamentos(sessao)


def gravar(repo, usuario: int, criado_em: str) -> None:
    """Grava um lançamento como se tivesse sido criado em `criado_em`."""
    lancamento = Lancamento(date(2026, 1, 1), Decimal(1), "despesa", "x", "x")
    id_ = repo.adicionar(usuario, lancamento)
    repo.sessao.execute(
        update(LancamentoTabela)
        .where(LancamentoTabela.id == id_)
        .values(criado_em=datetime.fromisoformat(criado_em))
    )


@pytest.fixture
def dados(repo):
    ana = repo.criar_usuario("Ana", telegram_id=1)
    bia = repo.criar_usuario("Bia", telegram_id=2)
    repo.criar_usuario("Caio")  # cadastrado, nunca lançou
    gravar(repo, ana, "2026-11-23 00:00:00")  # semana atual (limite exato)
    gravar(repo, ana, "2026-11-25 10:00:00")
    gravar(repo, bia, "2026-11-24 09:00:00")
    gravar(repo, ana, "2026-11-22 23:59:59")  # domingo da semana passada
    gravar(repo, bia, "2026-11-10 12:00:00")  # duas semanas atrás


def test_usuarios_ativos_por_semana(repo, dados):
    semanas = usuarios_ativos_por_semana(repo.sessao, HOJE, semanas=3)

    assert semanas == [
        SemanaDeUso(date(2026, 11, 9), usuarios_ativos=1, lancamentos=1),
        SemanaDeUso(date(2026, 11, 16), usuarios_ativos=1, lancamentos=1),
        SemanaDeUso(date(2026, 11, 23), usuarios_ativos=2, lancamentos=3),
    ]


def test_totais_e_lancamentos_por_usuario(repo, dados):
    metricas = calcular_metricas(repo.sessao, HOJE, semanas=2)

    assert (metricas.usuarios, metricas.usuarios_com_telegram) == (3, 2)
    assert (metricas.lancamentos, metricas.usuarios_com_lancamentos) == (5, 2)
    assert metricas.maximo_por_usuario == 3
    assert metricas.media_por_usuario == 2.5
    assert len(metricas.semanas) == 2


def test_banco_vazio(repo):
    metricas = calcular_metricas(repo.sessao, HOJE, semanas=1)

    assert metricas.lancamentos == metricas.maximo_por_usuario == 0
    assert metricas.media_por_usuario == 0
    assert metricas.semanas == [SemanaDeUso(date(2026, 11, 23), 0, 0)]


def test_lancamento_novo_ganha_criado_em_automatico(repo):
    usuario = repo.criar_usuario("Ana")
    repo.adicionar(
        usuario, Lancamento(date(2020, 1, 1), Decimal(1), "despesa", "x", "x")
    )

    criado_em = repo.sessao.scalar(select(LancamentoTabela.criado_em))
    assert criado_em.year >= 2026  # momento da gravação, não a data do gasto
