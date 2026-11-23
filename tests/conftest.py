"""Fixtures de banco compartilhadas pelos testes.

Por padrão, cada teste ganha um SQLite novo num arquivo temporário. Com a
variável FINANCEIRO_TEST_DB_URL apontando para um PostgreSQL (é o que o CI
faz), os mesmos testes rodam nesse banco, que é esvaziado antes e depois
de cada teste.
"""

import os

import pytest
from sqlalchemy import text

from financeiro.banco.conexao import criar_engine
from financeiro.banco.tabelas import Base

URL_TESTE = os.environ.get("FINANCEIRO_TEST_DB_URL")


def _esvaziar(url: str) -> None:
    """Apaga as tabelas do app e a tabela de controle do Alembic."""
    engine = criar_engine(url)
    Base.metadata.drop_all(engine)
    with engine.begin() as conexao:
        conexao.execute(text("DROP TABLE IF EXISTS alembic_version"))
    engine.dispose()


@pytest.fixture
def url_banco(tmp_path):
    """URL de um banco vazio, sem nenhuma tabela."""
    if URL_TESTE is None:
        yield f"sqlite:///{tmp_path / 'teste.db'}"
        return
    _esvaziar(URL_TESTE)
    yield URL_TESTE
    _esvaziar(URL_TESTE)


@pytest.fixture
def engine(url_banco):
    """Engine de um banco com as tabelas já criadas e vazias."""
    engine = criar_engine(url_banco)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
