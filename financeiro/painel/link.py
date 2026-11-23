"""Gera um link de login do painel pelo terminal, sem o bot.

Útil para testar o painel localmente:

    docker compose exec api python -m financeiro.painel.link --usuario Ana

Usa o mesmo FINANCEIRO_SEGREDO da API (senão o link não seria aceito).
"""

import argparse
import os

from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.painel.sessao import LINK, criar_token


def main(argv: list[str] | None = None) -> int:
    """Imprime o link de login do usuário informado."""
    parser = argparse.ArgumentParser(description="Gera um link de login do painel.")
    parser.add_argument("--usuario", required=True, help="nome do usuário")
    parser.add_argument(
        "--url", default="http://127.0.0.1:8000", help="endereço onde a API está"
    )
    argumentos = parser.parse_args(argv)

    segredo = os.environ.get("FINANCEIRO_SEGREDO")
    if not segredo:
        parser.error("defina FINANCEIRO_SEGREDO com o mesmo valor usado na API")

    engine = criar_engine()
    with criar_fabrica_de_sessoes(engine)() as sessao:
        repositorio = RepositorioLancamentos(sessao)
        usuario_id = repositorio.obter_ou_criar_usuario(argumentos.usuario)
        sessao.commit()
    engine.dispose()

    token = criar_token(segredo, usuario_id, LINK)
    print(f"{argumentos.url.rstrip('/')}/painel/entrar?token={token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
