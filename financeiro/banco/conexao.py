"""Criação da conexão (engine) e das sessões com o banco."""

import os

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

# Sem a variável de ambiente, usa um arquivo SQLite local (ignorado pelo git).
URL_PADRAO = "sqlite:///financeiro.db"


def url_do_banco() -> str:
    """Lê a URL do banco da variável FINANCEIRO_DB_URL, ou usa o SQLite local."""
    return os.environ.get("FINANCEIRO_DB_URL", URL_PADRAO)


def criar_engine(url: str | None = None) -> Engine:
    """Cria o engine do SQLAlchemy para a `url` (ou a de url_do_banco()).

    No SQLite, as chaves estrangeiras vêm desligadas por padrão; aqui elas
    são ligadas em toda conexão nova, para o banco recusar, por exemplo, um
    lançamento de um usuário que não existe.
    """
    engine = create_engine(url or url_do_banco())
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _ligar_chaves_estrangeiras)
    return engine


def _ligar_chaves_estrangeiras(conexao_dbapi, _registro) -> None:
    cursor = conexao_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def criar_fabrica_de_sessoes(engine: Engine) -> sessionmaker:
    """Devolve uma fábrica de sessões: `with Sessao() as sessao: ...`."""
    return sessionmaker(engine, expire_on_commit=False)
