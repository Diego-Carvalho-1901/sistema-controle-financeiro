"""Funções de análise das movimentações financeiras.

Ficam separadas de main.py para poderem ser importadas e testadas sem
executar o relatório inteiro.
"""

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
