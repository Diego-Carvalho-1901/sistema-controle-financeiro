"""Dependências do FastAPI compartilhadas pelas rotas.

Ficam num módulo próprio para que cada grupo de rotas (lançamentos,
resumos...) possa usá-las sem um importar o outro.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
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
