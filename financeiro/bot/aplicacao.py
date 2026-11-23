"""Liga a conversa (conversa.py) aos comandos do Telegram.

Rode com `python -m financeiro.bot`. Precisa da variável TELEGRAM_TOKEN
(o token que o @BotFather entrega) e da API no ar (FINANCEIRO_API_URL,
padrão http://127.0.0.1:8000).
"""

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from financeiro.bot import agenda, comandos, conversa
from financeiro.bot.cliente_api import URL_PADRAO, ClienteAPI, ErroAPI

log = logging.getLogger(__name__)

ERRO_GENERICO = "Não consegui falar com o servidor agora. Tente de novo daqui a pouco."


def _api(contexto: ContextTypes.DEFAULT_TYPE) -> ClienteAPI:
    return contexto.application.bot_data["api"]


async def _responder(update: Update, funcao, *args) -> None:
    """Roda uma função da conversa e manda o texto devolvido.

    O cliente da API é síncrono (httpx.Client). asyncio.to_thread roda a
    chamada numa thread separada, para não travar o bot enquanto espera a
    API responder.
    """
    try:
        texto = await asyncio.to_thread(funcao, *args)
    except ErroAPI:
        log.exception("erro ao falar com a API")
        texto = ERRO_GENERICO
    await update.effective_message.reply_text(texto)


async def comando_start(update: Update, contexto: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    await _responder(
        update, conversa.responder_start, _api(contexto), usuario.id, usuario.first_name
    )


async def comando_ajuda(update: Update, _contexto: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(conversa.responder_ajuda())


async def comando_resumo(update: Update, contexto: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    await _responder(
        update,
        comandos.responder_resumo,
        _api(contexto),
        usuario.id,
        usuario.first_name,
        contexto.args or [],
    )


async def comando_desfazer(update: Update, contexto: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    await _responder(
        update,
        comandos.responder_desfazer,
        _api(contexto),
        usuario.id,
        usuario.first_name,
    )


async def comando_meta(update: Update, contexto: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    await _responder(
        update,
        comandos.responder_meta,
        _api(contexto),
        usuario.id,
        usuario.first_name,
        contexto.args or [],
    )


async def comando_corrigir(update: Update, contexto: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    await _responder(
        update,
        comandos.responder_corrigir,
        _api(contexto),
        usuario.id,
        usuario.first_name,
        contexto.args or [],
    )


async def mensagem_de_texto(
    update: Update, contexto: ContextTypes.DEFAULT_TYPE
) -> None:
    """Qualquer texto que não seja comando é lido como um lançamento."""
    usuario = update.effective_user
    await _responder(
        update,
        conversa.responder_frase,
        _api(contexto),
        usuario.id,
        usuario.first_name,
        update.effective_message.text,
    )


def criar_aplicacao(token: str, api: ClienteAPI) -> Application:
    """Monta o bot com os comandos registrados (não conecta ainda)."""
    aplicacao = Application.builder().token(token).build()
    aplicacao.bot_data["api"] = api
    aplicacao.add_handler(CommandHandler("start", comando_start))
    aplicacao.add_handler(CommandHandler("ajuda", comando_ajuda))
    aplicacao.add_handler(CommandHandler("resumo", comando_resumo))
    aplicacao.add_handler(CommandHandler("desfazer", comando_desfazer))
    aplicacao.add_handler(CommandHandler("meta", comando_meta))
    aplicacao.add_handler(CommandHandler("corrigir", comando_corrigir))
    aplicacao.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_de_texto)
    )
    agenda.agendar(aplicacao)
    return aplicacao


def main() -> None:
    """Lê a configuração do ambiente e deixa o bot rodando."""
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("Defina a variável TELEGRAM_TOKEN com o token do @BotFather.")
    logging.basicConfig(level=logging.INFO)
    api = ClienteAPI.conectar(os.environ.get("FINANCEIRO_API_URL", URL_PADRAO))
    criar_aplicacao(token, api).run_polling()
