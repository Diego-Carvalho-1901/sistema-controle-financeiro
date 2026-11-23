"""Testes das métricas de uso: consultas, rota e comando /stats."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from financeiro.api.app import criar_app
from financeiro.banco.conexao import criar_fabrica_de_sessoes
from financeiro.banco.metricas import (
    SemanaDeUso,
    calcular_metricas,
    usuarios_ativos_por_semana,
)
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.banco.tabelas import LancamentoTabela
from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.comandos import COMANDO_RESTRITO, responder_stats
from financeiro.bot.conversa import responder_frase
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


# --- API e comando /stats ---

ADMIN = 999


@pytest.fixture
def api(engine):
    with TestClient(criar_app(engine)) as http:
        yield ClienteAPI(http)


def test_rota_de_metricas(api):
    responder_frase(api, 1, "Ana", "gastei 30 almoço")
    responder_frase(api, 2, "Bia", "vendi 2 bolos 40")
    responder_frase(api, 2, "Bia", "gastei 10 uber")

    dados = api.metricas(date.today())

    assert dados["usuarios"] == dados["usuarios_com_telegram"] == 2
    assert dados["lancamentos"] == 3
    assert dados["media_por_usuario"] == 1.5
    assert dados["semanas"][-1]["usuarios_ativos"] == 2
    assert len(dados["semanas"]) == 8


def test_metricas_nao_expoem_dados_pessoais(api):
    responder_frase(api, 1, "Ana Secreta", "gastei 30 remédio controlado")

    texto = str(api.metricas(date.today()))

    assert "Ana" not in texto and "remédio" not in texto


def test_stats_para_o_administrador(api):
    responder_frase(api, 1, "Ana", "gastei 30 almoço")

    resposta = responder_stats(api, ADMIN, admin_id=ADMIN)

    assert resposta.startswith("Métricas de uso\n\nUsuários: 1 (1 no Telegram)")
    assert "Média por usuário que lança: 1,0" in resposta
    assert resposta.count("\n• ") == 8  # uma linha por semana


@pytest.mark.parametrize(("quem", "admin"), [(1, ADMIN), (ADMIN, None)])
def test_stats_e_restrito(api, quem, admin):
    assert responder_stats(api, quem, admin_id=admin) == COMANDO_RESTRITO
