"""Testes do resumo semanal e do alerta de meta no bot, sem o Telegram."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from telegram.error import Forbidden

from financeiro.api.app import criar_app
from financeiro.bot import agenda, comandos
from financeiro.bot.aplicacao import criar_aplicacao
from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.conversa import responder_frase

ANA, BIA, CAIO = 101, 202, 303
SEGUNDA = date(2026, 11, 30)  # a semana passada vai de 23/11 a 29/11


@pytest.fixture
def api(engine):
    with TestClient(criar_app(engine)) as http:
        yield ClienteAPI(http)


def anotar(api, telegram_id: int, frase: str, dia: date) -> str:
    return responder_frase(api, telegram_id, "Fulano", frase, hoje=dia)


# --- Alerta de meta ---


def test_alerta_aparece_uma_vez_quando_passa_de_80_por_cento(api):
    comandos.responder_meta(api, ANA, "Ana", ["mercado", "100"], SEGUNDA)

    primeira = anotar(api, ANA, "gastei 50 mercado", SEGUNDA)
    segunda = anotar(api, ANA, "gastei 35 mercado", SEGUNDA)
    terceira = anotar(api, ANA, "gastei 10 mercado", SEGUNDA)

    assert "Atenção" not in primeira
    assert segunda.endswith(
        "\n\nAtenção: você já usou 85% da meta de mercado este mês "
        "(R$ 85,00 de R$ 100,00)."
    )
    assert "Atenção" not in terceira


def test_vendas_nao_disparam_alerta(api):
    comandos.responder_meta(api, ANA, "Ana", ["bolos", "10"], SEGUNDA)

    assert "Atenção" not in anotar(api, ANA, "vendi 2 bolos 90", SEGUNDA)


# --- Resumo semanal ---


def test_textos_do_resumo_semanal_so_para_quem_lancou_algo(api):
    anotar(api, ANA, "gastei 40 almoço", date(2026, 11, 25))
    anotar(api, BIA, "vendi 2 bolos 60", date(2026, 11, 29))
    anotar(api, CAIO, "gastei 10 pão", date(2026, 11, 30))  # já é desta semana

    mensagens = agenda.textos_do_resumo_semanal(api, SEGUNDA)

    assert [chat for chat, _ in mensagens] == [ANA, BIA]
    assert mensagens[0][1].startswith("Resumo da semana passada (23/11 a 29/11)")
    assert "Lucro: R$ 60,00" in mensagens[1][1]


class BotFalso:
    """Guarda as mensagens em vez de mandar; recusa um chat bloqueado."""

    def __init__(self, bloqueado: int | None = None) -> None:
        self.enviadas: list[tuple[int, str]] = []
        self.bloqueado = bloqueado

    async def send_message(self, chat_id: int, text: str) -> None:
        if chat_id == self.bloqueado:
            raise Forbidden("bot was blocked by the user")
        self.enviadas.append((chat_id, text))


def test_envio_continua_quando_um_usuario_bloqueou_o_bot(api, monkeypatch):
    anotar(api, ANA, "gastei 40 almoço", date(2026, 11, 25))
    anotar(api, BIA, "gastei 20 uber", date(2026, 11, 25))
    monkeypatch.setattr(
        agenda,
        "textos_do_resumo_semanal",
        lambda api_, _hoje: [(ANA, "resumo da Ana"), (BIA, "resumo da Bia")],
    )
    bot = BotFalso(bloqueado=ANA)
    contexto = SimpleNamespace(
        bot=bot, application=SimpleNamespace(bot_data={"api": api})
    )

    asyncio.run(agenda.enviar_resumo_semanal(contexto))

    assert bot.enviadas == [(BIA, "resumo da Bia")]


def test_resumo_fica_agendado_para_segunda_as_9h(api):
    aplicacao = criar_aplicacao("123:token-falso", api)

    [tarefa] = aplicacao.job_queue.jobs()  # agenda sem iniciar o bot
    assert tarefa.name == "resumo-semanal"
    assert tarefa.callback is agenda.enviar_resumo_semanal
