"""Testes do bot sem chamar o Telegram de verdade.

O bot conversa com uma API de verdade, ligada a um banco de testes, através
do TestClient do FastAPI (que é um httpx.Client). Só a parte do Telegram
fica de fora.
"""

from datetime import date
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from telegram.ext import CommandHandler, MessageHandler

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
    assert {"start", "ajuda", "resumo", "desfazer", "meta", "corrigir"} <= comandos
    assert any(isinstance(h, MessageHandler) for h in aplicacao.handlers[0])


def test_main_exige_o_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="TELEGRAM_TOKEN"):
        main()


# --- Frases livres (issue [13]) ---


def lancamentos_de(api, telegram_id: int = TELEGRAM_ID) -> list[dict]:
    usuario = api.buscar_usuario_do_telegram(telegram_id)
    return api.http.get(f"/usuarios/{usuario['id']}/lancamentos").json()


def test_frase_vira_lancamento_na_api(api):
    resposta = conversa.responder_frase(
        api, TELEGRAM_ID, "Ana", "vendi 3 bolos 45", hoje=date(2026, 11, 20)
    )

    assert resposta == (
        "Anotado: venda de 3 × bolos, R$ 45,00 (negócio). Errou? Use /desfazer."
    )
    [lancamento] = lancamentos_de(api)
    assert lancamento["valor"] == "45.00"
    assert lancamento["quantidade"] == 3
    assert lancamento["data"] == "2026-11-20"


def test_frase_de_quem_nunca_deu_start_cadastra_a_pessoa(api):
    conversa.responder_frase(api, TELEGRAM_ID, "Ana", "gastei 30 almoço")

    assert api.buscar_usuario_do_telegram(TELEGRAM_ID)["nome"] == "Ana"
    assert len(lancamentos_de(api)) == 1


def test_frase_nao_entendida_pede_para_reescrever_e_nao_grava(api):
    conversa.obter_ou_criar_usuario(api, TELEGRAM_ID, "Ana")

    resposta = conversa.responder_frase(api, TELEGRAM_ID, "Ana", "gastei 30 e 20")

    assert resposta.startswith("Não entendi: não sei qual número é o valor.")
    assert "vendi 3 bolos 45" in resposta
    assert lancamentos_de(api) == []


@pytest.mark.parametrize(
    ("valor", "texto"),
    [
        ("0.5", "R$ 0,50"),
        ("45", "R$ 45,00"),
        ("1800.5", "R$ 1.800,50"),
        ("1234567.89", "R$ 1.234.567,89"),
    ],
)
def test_formata_reais(valor, texto):
    assert conversa.formatar_reais(Decimal(valor)) == texto
