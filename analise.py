"""Funções de análise das movimentações financeiras.

Ficam separadas de main.py para poderem ser importadas e testadas sem
executar o relatório inteiro.
"""

from collections.abc import Iterable
from datetime import datetime

COLUNAS = ("data", "valor", "tipo", "categoria", "descricao")

NOMES_MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def calcular_percentual(parte: float, todo: float) -> float:
    """Devolve quanto `parte` representa de `todo`, em porcentagem.

    Quando `todo` é zero (por exemplo, um período sem nenhuma receita),
    devolve 0.0 em vez de lançar ZeroDivisionError.
    """
    if todo == 0:
        return 0.0
    return (parte / todo) * 100


def calcular_media(total: float, quantidade: int) -> float:
    """Devolve a média `total / quantidade`, ou 0.0 se não houver itens."""
    if quantidade == 0:
        return 0.0
    return total / quantidade


def encontrar_maior_e_menor(movimentacoes: list[list]) -> tuple[list, list]:
    """Devolve a movimentação de maior valor e a de menor valor.

    Cada movimentação é uma lista [data, valor, tipo, categoria, descricao].
    Em caso de empate, vale a que aparece primeiro na lista.
    """
    maior = max(movimentacoes, key=lambda movimentacao: movimentacao[1])
    menor = min(movimentacoes, key=lambda movimentacao: movimentacao[1])
    return maior, menor


def nome_do_mes(mes: int) -> str:
    """Devolve o nome do mês (1 a 12) em português.

    Não usa strftime("%B"), que depende do idioma (locale) configurado
    no sistema e por isso mostrava "September" em vez de "setembro".
    """
    return NOMES_MESES[mes - 1]


def somar_por_mes(movimentacoes: list[list], tipo: str) -> dict[tuple[int, int], float]:
    """Soma os valores de um tipo ("receita" ou "despesa") em cada mês.

    A chave é a tupla (ano, mês), para que janeiro/2026 e janeiro/2027
    fiquem separados. Tuplas são ordenadas elemento a elemento, então
    sorted() nas chaves já devolve os meses em ordem cronológica.
    """
    totais: dict[tuple[int, int], float] = {}
    for data, valor, tipo_movimentacao, _categoria, _descricao in movimentacoes:
        if tipo_movimentacao != tipo:
            continue
        chave = (data.year, data.month)
        totais[chave] = totais.get(chave, 0) + valor
    return totais


class ErroLeitura(Exception):
    """Problema no CSV, com uma mensagem pronta para mostrar ao usuário."""


def ler_movimentacoes(linhas: Iterable[list[str]]) -> list[list]:
    """Converte as linhas do CSV (a primeira é o cabeçalho) em movimentações.

    Cada movimentação vira [data (datetime), valor (float), tipo, categoria,
    descricao]. Linhas em branco são ignoradas.

    Lança ErroLeitura, indicando o número da linha no arquivo, quando o CSV
    está vazio, quando uma linha não tem 5 colunas ou quando a data ou o
    valor são inválidos.
    """
    linhas = iter(linhas)
    if next(linhas, None) is None:
        raise ErroLeitura("O arquivo CSV está vazio.")

    movimentacoes = []
    # O cabeçalho é a linha 1, então os dados começam na linha 2.
    for numero_linha, linha in enumerate(linhas, start=2):
        if not linha:
            continue
        if len(linha) != len(COLUNAS):
            raise ErroLeitura(
                f"Linha {numero_linha}: esperadas {len(COLUNAS)} colunas "
                f"({', '.join(COLUNAS)}), mas foram encontradas {len(linha)}."
            )

        data_texto, valor_texto, tipo, categoria, descricao = linha
        try:
            data = datetime.strptime(data_texto, "%d/%m/%Y")
        except ValueError:
            raise ErroLeitura(
                f"Linha {numero_linha}: data inválida '{data_texto}'. "
                "Use o formato DD/MM/AAAA."
            ) from None
        try:
            valor = float(valor_texto)
        except ValueError:
            raise ErroLeitura(
                f"Linha {numero_linha}: valor inválido '{valor_texto}'."
            ) from None

        movimentacoes.append([data, valor, tipo, categoria, descricao])

    if not movimentacoes:
        raise ErroLeitura("O arquivo CSV não contém nenhuma movimentação.")
    return movimentacoes
