"""Ponto de entrada do Alembic: diz qual banco usar e qual é o esquema."""

from logging.config import fileConfig

from alembic import context

from financeiro.banco.conexao import criar_engine, url_do_banco
from financeiro.banco.tabelas import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Esquema esperado; o `--autogenerate` compara com o banco para criar migrações.
target_metadata = Base.metadata


def _url() -> str:
    # Os testes passam a URL pela config; no uso normal vem do ambiente.
    return config.get_main_option("sqlalchemy.url") or url_do_banco()


def rodar_offline() -> None:
    """Gera o SQL das migrações sem conectar (`alembic upgrade head --sql`)."""
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    """Conecta no banco e aplica as migrações."""
    engine = criar_engine(_url())
    with engine.connect() as conexao:
        context.configure(
            connection=conexao,
            target_metadata=target_metadata,
            # O SQLite não altera colunas com ALTER TABLE; o modo "batch" recria
            # a tabela por baixo dos panos quando isso for necessário.
            render_as_batch=conexao.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
