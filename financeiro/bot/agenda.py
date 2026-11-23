"""Mensagens que o bot manda sozinho: o resumo semanal (issue [16]).

O agendamento usa a JobQueue do python-telegram-bot. A parte que monta os
textos (textos_do_resumo_semanal) é uma função comum, testada sem Telegram.
"""

import asyncio
import logging
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

from telegram.error import TelegramError
from telegram.ext import Application, ContextTypes

from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.comandos import SEM_LANCAMENTOS, montar_resumo
from financeiro.periodos import semana_de

log = logging.getLogger(__name__)

FUSO = ZoneInfo("America/Sao_Paulo")
HORARIO_RESUMO = time(hour=9, tzinfo=FUSO)
SEGUNDA = 1  # na JobQueue, 0 = domingo ... 6 = sábado


def textos_do_resumo_semanal(api: ClienteAPI, hoje: date) -> list[tuple[int, str]]:
    """(telegram_id, texto) do resumo da semana passada de cada usuário.

    Quem não lançou nada na semana não recebe mensagem: um resumo vazio
    toda segunda vira spam.
    """
    inicio, fim = semana_de(hoje - timedelta(days=7))
    mensagens = []
    for usuario in api.listar_usuarios():
        texto = montar_resumo(api, usuario["id"], "da semana passada", inicio, fim)
        if not texto.endswith(SEM_LANCAMENTOS):
            mensagens.append((usuario["telegram_id"], texto))
    return mensagens


async def enviar_resumo_semanal(contexto: ContextTypes.DEFAULT_TYPE) -> None:
    """Tarefa agendada: manda o resumo para cada usuário."""
    api: ClienteAPI = contexto.application.bot_data["api"]
    hoje = date.today()
    mensagens = await asyncio.to_thread(textos_do_resumo_semanal, api, hoje)
    for chat_id, texto in mensagens:
        try:
            await contexto.bot.send_message(chat_id=chat_id, text=texto)
        except TelegramError:
            # Um usuário que bloqueou o bot não pode impedir os outros.
            log.exception("não consegui mandar o resumo para %s", chat_id)


def agendar(aplicacao: Application) -> None:
    """Agenda o resumo para toda segunda-feira às 9h (horário de Brasília)."""
    aplicacao.job_queue.run_daily(
        enviar_resumo_semanal,
        time=HORARIO_RESUMO,
        days=(SEGUNDA,),
        name="resumo-semanal",
    )
