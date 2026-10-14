"""Sistema de Controle Financeiro — ponto de entrada pela linha de comando.

Autor: Diego Carvalho Louzada Viveiros

Uso:
    python main.py                      # usa dados/movimentacoes.csv
    python main.py caminho/para/arquivo.csv
"""

import argparse
import sys
from pathlib import Path

from financeiro.leitura import ErroLeitura, carregar_csv
from financeiro.relatorio import gerar_relatorio

# Resolvido a partir deste arquivo, e não do diretório atual, para o programa
# funcionar mesmo quando é chamado de outra pasta.
CSV_PADRAO = Path(__file__).resolve().parent / "dados" / "movimentacoes.csv"


def criar_parser() -> argparse.ArgumentParser:
    """Define os argumentos aceitos na linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gera um relatório financeiro a partir de um CSV de movimentações."
    )
    parser.add_argument(
        "csv",
        nargs="?",
        type=Path,
        default=CSV_PADRAO,
        help="arquivo CSV com as colunas data,valor,tipo,categoria,descricao "
        "(padrão: dados/movimentacoes.csv)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Lê o CSV, imprime o relatório e devolve o código de saída do programa."""
    argumentos = criar_parser().parse_args(argv)
    try:
        lancamentos = carregar_csv(argumentos.csv)
    except FileNotFoundError:
        print(
            f"\nErro: O arquivo {argumentos.csv} não foi encontrado!!\n",
            file=sys.stderr,
        )
        return 1
    except ErroLeitura as erro:
        print(f"\nErro: {erro}\n", file=sys.stderr)
        return 1

    print(gerar_relatorio(lancamentos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
