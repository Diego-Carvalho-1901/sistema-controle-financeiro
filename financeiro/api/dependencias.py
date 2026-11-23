"""Dependências do FastAPI compartilhadas pelas rotas.

Ficam num módulo próprio para que cada grupo de rotas (lançamentos,
resumos...) possa usá-las sem um importar o outro.
"""

import secrets
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from financeiro.banco.repositorio import RepositorioLancamentos


def obter_sessao(request: Request) -> Iterator[Session]:
    """Abre uma sessão por requisição e a fecha no fim (dependência)."""
    with request.app.state.fabrica_de_sessoes() as sessao:
        yield sessao


def obter_repositorio(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> RepositorioLancamentos:
    """Entrega o repositório pronto para as rotas (dependência)."""
    return RepositorioLancamentos(sessao)


Repositorio = Annotated[RepositorioLancamentos, Depends(obter_repositorio)]


def exigir_usuario(repo: RepositorioLancamentos, usuario_id: int) -> None:
    """Responde 404 se o usuário não existir."""
    if not repo.usuario_existe(usuario_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "usuário não encontrado")


def exigir_chave_api(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Recusa (401) requisições sem a chave certa no cabeçalho X-API-Key.

    A chave vem de FINANCEIRO_API_KEY. Sem ela configurada (no seu
    computador, por exemplo), a API fica aberta, como antes. Em produção a
    chave é obrigatória: é ela que impede qualquer pessoa de ler os dados.
    """
    esperada = request.app.state.chave_api
    if esperada is None:
        return
    # compare_digest leva o mesmo tempo acerte ou erre, para não dar pistas
    # da chave a quem mede o tempo de resposta (ataque de temporização).
    if x_api_key is None or not secrets.compare_digest(x_api_key, esperada):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "chave da API inválida")
