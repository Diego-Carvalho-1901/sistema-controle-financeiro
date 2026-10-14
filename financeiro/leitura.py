"""Leitura do CSV de movimentações e conversão em objetos Lancamento."""

import csv
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from financeiro.modelos import TIPOS, Lancamento

COLUNAS = ("data", "valor", "tipo", "categoria", "descricao")


class ErroLeitura(Exception):
    """Problema no CSV, com uma mensagem pronta para mostrar ao usuário."""


def carregar_csv(caminho: Path) -> list[Lancamento]:
    """Abre o arquivo CSV em `caminho` e devolve os lançamentos.

    Lança FileNotFoundError se o arquivo não existir e ErroLeitura se o
    conteúdo for inválido.
    """
    # newline="" é a forma recomendada pela documentação do módulo csv.
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return ler_lancamentos(csv.reader(arquivo))


def ler_lancamentos(linhas: Iterable[list[str]]) -> list[Lancamento]:
    """Converte as linhas do CSV (a primeira é o cabeçalho) em lançamentos.

    Linhas em branco são ignoradas. Lança ErroLeitura, indicando o número da
    linha no arquivo, quando o CSV está vazio, quando uma linha não tem 5
    colunas ou quando a data, o valor ou o tipo são inválidos.
    """
    linhas = iter(linhas)
    if next(linhas, None) is None:
        raise ErroLeitura("O arquivo CSV está vazio.")

    lancamentos = []
    # O cabeçalho é a linha 1, então os dados começam na linha 2.
    for numero_linha, linha in enumerate(linhas, start=2):
        if not linha:
            continue
        lancamentos.append(_converter_linha(linha, numero_linha))

    if not lancamentos:
        raise ErroLeitura("O arquivo CSV não contém nenhuma movimentação.")
    return lancamentos


def _converter_linha(linha: list[str], numero_linha: int) -> Lancamento:
    """Valida uma linha do CSV e a transforma em Lancamento."""
    if len(linha) != len(COLUNAS):
        raise ErroLeitura(
            f"Linha {numero_linha}: esperadas {len(COLUNAS)} colunas "
            f"({', '.join(COLUNAS)}), mas foram encontradas {len(linha)}."
        )

    data_texto, valor_texto, tipo, categoria, descricao = linha
    try:
        data = datetime.strptime(data_texto, "%d/%m/%Y").date()
    except ValueError:
        raise ErroLeitura(
            f"Linha {numero_linha}: data inválida '{data_texto}'. "
            "Use o formato DD/MM/AAAA."
        ) from None

    try:
        # Decimal a partir do texto guarda exatamente "45.90", sem o erro
        # de arredondamento que um float teria.
        valor = Decimal(valor_texto)
    except InvalidOperation:
        valor = None
    # Decimal aceita "NaN" e "Infinity", que não são valores de dinheiro.
    if valor is None or not valor.is_finite():
        raise ErroLeitura(f"Linha {numero_linha}: valor inválido '{valor_texto}'.")

    if tipo not in TIPOS:
        raise ErroLeitura(
            f"Linha {numero_linha}: tipo inválido '{tipo}'. Use {' ou '.join(TIPOS)}."
        )

    return Lancamento(data, valor, tipo, categoria, descricao)
