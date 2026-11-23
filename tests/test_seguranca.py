"""Testes da chave da API e da rota de saúde."""

import pytest
from fastapi.testclient import TestClient

from financeiro.api.app import criar_app
from financeiro.bot.cliente_api import ClienteAPI

CHAVE = "chave-de-teste-123"


@pytest.fixture
def protegida(engine):
    with TestClient(criar_app(engine, chave_api=CHAVE)) as cliente:
        yield cliente


@pytest.mark.parametrize("cabecalhos", [{}, {"X-API-Key": "errada"}])
def test_sem_a_chave_certa_da_401(protegida, cabecalhos):
    resposta = protegida.post("/usuarios", json={"nome": "Ana"}, headers=cabecalhos)

    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "rota",
    ["/usuarios", "/usuarios/1/lancamentos", "/usuarios/1/resumos/mensal", "/metricas"],
)
def test_todas_as_rotas_de_dados_exigem_a_chave(protegida, rota):
    assert protegida.get(rota).status_code == 401


def test_com_a_chave_funciona(protegida):
    resposta = protegida.post(
        "/usuarios", json={"nome": "Ana"}, headers={"X-API-Key": CHAVE}
    )

    assert resposta.status_code == 201


def test_cliente_do_bot_manda_a_chave(engine):
    api = ClienteAPI.conectar("http://testserver", CHAVE)
    with TestClient(criar_app(engine, chave_api=CHAVE)) as http:
        http.headers.update(api.http.headers)  # usa os cabeçalhos do bot

        assert ClienteAPI(http).criar_usuario("Ana", 1)["nome"] == "Ana"


def test_saude_responde_sem_chave(protegida):
    resposta = protegida.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_sem_chave_configurada_a_api_fica_aberta(engine, monkeypatch):
    monkeypatch.delenv("FINANCEIRO_API_KEY", raising=False)
    with TestClient(criar_app(engine)) as cliente:
        assert cliente.post("/usuarios", json={"nome": "Ana"}).status_code == 201
