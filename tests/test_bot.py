"""Testes do bot sem chamar o Telegram de verdade.

O bot conversa com uma API de verdade, ligada a um banco de testes, através
do TestClient do FastAPI (que é um httpx.Client). Só a parte do Telegram
fica de fora.
"""

import httpx
import pytest
from fastapi.testclient import TestClient
from telegram.ext import CommandHandler

from financeiro.api.app import criar_app
from financeiro.bot import conversa
from financeiro.bot.aplicacao import criar_aplicacao, main
from financeiro.bot.cliente_api import ClienteAPI, ErroAPI

TELEGRAM_ID = 5_123_456_789


@pytest.fixture
def api(engine):
    with TestClient(criar_app(engine)) as http:
        yield ClienteAPI(http)


def test_start_cadastra_usuario_novo(api):
    resposta = conversa.responder_start(api, TELEGRAM_ID, "Ana")

    assert "Olá, Ana! Seu cadastro está feito." in resposta
    assert "/ajuda" in resposta
    assert api.buscar_usuario_do_telegram(TELEGRAM_ID)["nome"] == "Ana"


def test_start_de_novo_nao_duplica_o_usuario(api):
    primeiro = conversa.obter_ou_criar_usuario(api, TELEGRAM_ID, "Ana")

    resposta = conversa.responder_start(api, TELEGRAM_ID, "Ana")

    assert "Você já está cadastrado" in resposta
    assert conversa.obter_ou_criar_usuario(api, TELEGRAM_ID, "Ana") == primeiro


def test_start_sem_nome_usa_um_nome_padrao(api):
    conversa.responder_start(api, TELEGRAM_ID, "")

    assert api.buscar_usuario_do_telegram(TELEGRAM_ID)["nome"] == "Sem nome"


def test_api_fora_do_ar_vira_erro_api():
    def recusar(_requisicao):
        raise httpx.ConnectError("conexão recusada")

    http = httpx.Client(base_url="http://api", transport=httpx.MockTransport(recusar))

    with pytest.raises(ErroAPI):
        ClienteAPI(http).buscar_usuario_do_telegram(TELEGRAM_ID)


def test_erro_da_api_vira_erro_api():
    http = httpx.Client(
        base_url="http://api",
        transport=httpx.MockTransport(lambda _req: httpx.Response(500)),
    )

    with pytest.raises(ErroAPI, match="500"):
        ClienteAPI(http).criar_usuario("Ana", TELEGRAM_ID)


def test_aplicacao_registra_os_comandos(api):
    aplicacao = criar_aplicacao("123:token-falso", api)

    comandos = {
        comando
        for handler in aplicacao.handlers[0]
        if isinstance(handler, CommandHandler)
        for comando in handler.commands
    }
    assert {"start", "ajuda"} <= comandos


def test_main_exige_o_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="TELEGRAM_TOKEN"):
        main()
