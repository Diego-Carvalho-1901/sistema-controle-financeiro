"""O que o bot responde a cada comando.

São funções comuns: recebem o cliente da API e os dados da mensagem e
devolvem o texto da resposta. Não sabem que o Telegram existe, então os
testes chamam essas funções direto.
"""

from financeiro.bot.cliente_api import ClienteAPI

AJUDA = """Eu anoto as finanças do seu negócio e as pessoais, separadas.

Comandos:
/start - cadastra você (ou confirma o cadastro)
/ajuda - mostra esta mensagem"""


def obter_ou_criar_usuario(api: ClienteAPI, telegram_id: int, nome: str) -> dict:
    """Devolve o usuário dessa conta do Telegram, cadastrando se for novo."""
    usuario = api.buscar_usuario_do_telegram(telegram_id)
    if usuario is None:
        usuario = api.criar_usuario(nome or "Sem nome", telegram_id)
    return usuario


def responder_start(api: ClienteAPI, telegram_id: int, nome: str) -> str:
    """Cadastra a pessoa na primeira vez e explica como usar o bot."""
    usuario = api.buscar_usuario_do_telegram(telegram_id)
    if usuario is None:
        usuario = api.criar_usuario(nome or "Sem nome", telegram_id)
        saudacao = f"Olá, {usuario['nome']}! Seu cadastro está feito."
    else:
        saudacao = f"Olá de novo, {usuario['nome']}! Você já está cadastrado."
    return f"{saudacao}\n\n{AJUDA}"


def responder_ajuda() -> str:
    """Lista os comandos disponíveis."""
    return AJUDA
