"""Importa um ou mais CSVs para o banco de dados.

Uso:
    alembic upgrade head                       # cria o banco (uma vez)
    python importar.py dados/movimentacoes.csv --usuario Ana
    python importar.py dados/*.csv --usuario Ana

O banco é o de FINANCEIRO_DB_URL (ou o SQLite local financeiro.db). Cada
arquivo é gravado na sua própria transação: se um arquivo não puder ser
lido, os anteriores continuam gravados.
"""

import argparse
import sys
from pathlib import Path

from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.importacao import importar_csv
from financeiro.leitura import ErroLeitura


def criar_parser() -> argparse.ArgumentParser:
    """Define os argumentos aceitos na linha de comando."""
    parser = argparse.ArgumentParser(
        description="Importa CSVs de movimentações ou de vendas para o banco."
    )
    parser.add_argument("csvs", nargs="+", type=Path, metavar="csv")
    parser.add_argument(
        "--usuario",
        required=True,
        help="nome do usuário dono dos lançamentos (criado se não existir)",
    )
    parser.add_argument(
        "--banco",
        default=None,
        help="URL do banco (padrão: FINANCEIRO_DB_URL ou sqlite:///financeiro.db)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Importa os arquivos e devolve 0 se todas as linhas entraram sem erro."""
    argumentos = criar_parser().parse_args(argv)
    engine = criar_engine(argumentos.banco)
    Sessao = criar_fabrica_de_sessoes(engine)
    codigo = 0
    try:
        for caminho in argumentos.csvs:
            with Sessao() as sessao:
                repositorio = RepositorioLancamentos(sessao)
                usuario_id = repositorio.obter_ou_criar_usuario(argumentos.usuario)
                try:
                    relatorio = importar_csv(repositorio, usuario_id, caminho)
                except FileNotFoundError:
                    print(f"\n{caminho}: arquivo não encontrado.", file=sys.stderr)
                    codigo = 1
                    continue
                except ErroLeitura as erro:
                    print(f"\n{caminho}: {erro}", file=sys.stderr)
                    codigo = 1
                    continue
                sessao.commit()
            print(f"\n{caminho}\n{relatorio.texto()}")
            if relatorio.erros:
                codigo = 1
    finally:
        engine.dispose()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
