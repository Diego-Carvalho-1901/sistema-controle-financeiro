"""Funções de análise das movimentações financeiras.

Ficam separadas de main.py para poderem ser importadas e testadas sem
executar o relatório inteiro.
"""


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
