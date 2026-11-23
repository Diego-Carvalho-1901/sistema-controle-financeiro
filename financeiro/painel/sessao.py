"""Tokens assinados com HMAC para o link de login e o cookie de sessão.

Um token é "dados.assinatura". Os dados (id do usuário, validade e para
que o token serve) ficam visíveis, mas não dá para alterá-los: a
assinatura é um HMAC-SHA256 dos dados com um segredo que só o servidor
conhece. Mudou um caractere, a assinatura não bate.
"""

import base64
import hashlib
import hmac
import time

LINK = "link"  # vem no link do bot; vale pouco tempo
SESSAO = "sessao"  # fica no cookie do navegador

VALIDADE = {LINK: 10 * 60, SESSAO: 7 * 24 * 60 * 60}  # em segundos


def criar_token(
    segredo: str, usuario_id: int, proposito: str, agora: float | None = None
) -> str:
    """Gera um token para o usuário que vence em VALIDADE[proposito]."""
    expira = int((agora or time.time()) + VALIDADE[proposito])
    dados = f"{usuario_id}:{expira}:{proposito}".encode()
    return f"{_b64(dados)}.{_assinar(segredo, dados)}"


def ler_token(
    segredo: str, token: str, proposito: str, agora: float | None = None
) -> int | None:
    """Devolve o id do usuário se o token for válido; senão, None.

    Inválido é: assinatura errada, formato estranho, vencido ou de outro
    propósito (um cookie de sessão não serve como link e vice-versa).
    """
    try:
        dados_b64, assinatura = token.split(".")
        dados = base64.urlsafe_b64decode(dados_b64 + "=" * (-len(dados_b64) % 4))
    except ValueError:
        return None
    if not hmac.compare_digest(assinatura, _assinar(segredo, dados)):
        return None
    try:
        usuario_id, expira, proposito_token = dados.decode().split(":")
        usuario_id, expira = int(usuario_id), int(expira)
    except ValueError:
        return None
    if proposito_token != proposito or (agora or time.time()) > expira:
        return None
    return usuario_id


def _assinar(segredo: str, dados: bytes) -> str:
    return hmac.new(segredo.encode(), dados, hashlib.sha256).hexdigest()


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).decode().rstrip("=")
