"""Leitura dos CSVs e conversão em objetos Lancamento.

Três formatos são aceitos, reconhecidos pelo cabeçalho (primeira linha):

- movimentações:              data,valor,tipo,categoria,descricao
- movimentações com conta:    data,valor,tipo,categoria,descricao,conta
- vendas (do analisador):     data da venda,produto,categoria,quantidade vendida,
                              preco unitario
"""

import csv
from collections.abc import Callable, Iterable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from financeiro.modelos import CONTAS, Lancamento

COLUNAS = ("data", "valor", "tipo", "categoria", "descricao")
COLUNAS_COM_CONTA = (*COLUNAS, "conta")
COLUNAS_VENDAS = (
    "data da venda",
    "produto",
    "categoria",
    "quantidade vendida",
    "preco unitario",
)
# Vendas têm produto e quantidade, então chegam pelo CSV de vendas.
TIPOS_MOVIMENTACAO = ("receita", "despesa")


class ErroLeitura(Exception):
    """Problema no CSV, com uma mensagem pronta para mostrar ao usuário."""


def carregar_csv(caminho: Path) -> list[Lancamento]:
    """Abre o arquivo CSV em `caminho` e devolve os lançamentos.

    Lança FileNotFoundError se o arquivo não existir e ErroLeitura se o
    conteúdo for inválido.
    """
    # newline="" é a forma recomendada pela documentação do módulo csv.
    # skipinitialspace=True descarta o espaço depois de cada vírgula, que o
    # CSV de vendas do analisador usa ("2024-01-15, Notebook").
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return ler_lancamentos(csv.reader(arquivo, skipinitialspace=True))


def ler_lancamentos(linhas: Iterable[list[str]]) -> list[Lancamento]:
    """Converte as linhas do CSV (a primeira é o cabeçalho) em lançamentos.

    O formato é escolhido pelo cabeçalho. Linhas em branco são ignoradas.
    Lança ErroLeitura, indicando o número da linha no arquivo, quando o CSV
    está vazio, quando o cabeçalho não é reconhecido ou quando alguma linha
    é inválida.
    """
    linhas = iter(linhas)
    cabecalho = next(linhas, None)
    if cabecalho is None:
        raise ErroLeitura("O arquivo CSV está vazio.")

    colunas, converter = _escolher_formato(cabecalho)
    lancamentos = []
    # O cabeçalho é a linha 1, então os dados começam na linha 2.
    for numero_linha, linha in enumerate(linhas, start=2):
        if not linha:
            continue
        if len(linha) != len(colunas):
            raise ErroLeitura(
                f"Linha {numero_linha}: esperadas {len(colunas)} colunas "
                f"({', '.join(colunas)}), mas foram encontradas {len(linha)}."
            )
        lancamentos.append(converter([campo.strip() for campo in linha], numero_linha))

    if not lancamentos:
        raise ErroLeitura("O arquivo CSV não contém nenhuma movimentação.")
    return lancamentos


Conversor = Callable[[list[str], int], Lancamento]


def _escolher_formato(cabecalho: list[str]) -> tuple[tuple[str, ...], Conversor]:
    """Devolve as colunas esperadas e a função que converte cada linha."""
    normalizado = tuple(coluna.strip().lower() for coluna in cabecalho)
    formatos: dict[tuple[str, ...], Conversor] = {
        COLUNAS: _converter_movimentacao,
        COLUNAS_COM_CONTA: _converter_movimentacao,
        COLUNAS_VENDAS: _converter_venda,
    }
    if normalizado not in formatos:
        raise ErroLeitura(
            f"Linha 1: cabeçalho não reconhecido ({', '.join(normalizado)}). "
            f"Use {','.join(COLUNAS)}[,conta] ou o CSV de vendas "
            f"({','.join(COLUNAS_VENDAS)})."
        )
    return normalizado, formatos[normalizado]


def _converter_movimentacao(linha: list[str], numero_linha: int) -> Lancamento:
    """Transforma uma linha do CSV de movimentações em Lancamento."""
    data_texto, valor_texto, tipo, categoria, descricao, *resto = linha
    conta = resto[0] if resto else "pessoal"

    data = _converter_data(data_texto, "%d/%m/%Y", "DD/MM/AAAA", numero_linha)
    valor = _converter_decimal(valor_texto, "valor", numero_linha)
    if tipo not in TIPOS_MOVIMENTACAO:
        raise ErroLeitura(
            f"Linha {numero_linha}: tipo inválido '{tipo}'. "
            f"Use {' ou '.join(TIPOS_MOVIMENTACAO)}."
        )
    if conta not in CONTAS:
        raise ErroLeitura(
            f"Linha {numero_linha}: conta inválida '{conta}'. "
            f"Use {' ou '.join(CONTAS)}."
        )
    return Lancamento(data, valor, tipo, categoria, descricao, conta)


def _converter_venda(linha: list[str], numero_linha: int) -> Lancamento:
    """Transforma uma linha do CSV de vendas em Lancamento do tipo venda."""
    data_texto, produto, categoria, quantidade_texto, preco_texto = linha

    data = _converter_data(data_texto, "%Y-%m-%d", "AAAA-MM-DD", numero_linha)
    try:
        quantidade = int(quantidade_texto)
    except ValueError:
        quantidade = 0
    if quantidade <= 0:
        raise ErroLeitura(
            f"Linha {numero_linha}: quantidade inválida '{quantidade_texto}'. "
            "Use um número inteiro maior que zero."
        )
    if not produto:
        raise ErroLeitura(f"Linha {numero_linha}: produto em branco.")
    preco = _converter_decimal(preco_texto, "preço", numero_linha)

    return Lancamento(
        data,
        quantidade * preco,
        "venda",
        categoria,
        produto,
        conta="negocio",
        produto=produto,
        quantidade=quantidade,
    )


def _converter_data(texto: str, formato: str, exemplo: str, numero_linha: int) -> date:
    """Converte o texto em data ou lança ErroLeitura explicando o formato."""
    try:
        return datetime.strptime(texto, formato).date()
    except ValueError:
        raise ErroLeitura(
            f"Linha {numero_linha}: data inválida '{texto}'. Use o formato {exemplo}."
        ) from None


def _converter_decimal(texto: str, nome: str, numero_linha: int) -> Decimal:
    """Converte o texto em Decimal finito e não negativo."""
    try:
        # Decimal a partir do texto guarda exatamente "45.90", sem o erro
        # de arredondamento que um float teria.
        numero = Decimal(texto)
    except InvalidOperation:
        numero = None
    # Decimal aceita "NaN" e "Infinity", que não são valores de dinheiro.
    if numero is None or not numero.is_finite() or numero < 0:
        raise ErroLeitura(f"Linha {numero_linha}: {nome} inválido '{texto}'.")
    return numero
