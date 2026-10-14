"""Cálculos sobre os lançamentos.

Todas as funções aqui são puras: recebem dados, devolvem um resultado e não
imprimem nada nem leem arquivos. Por isso podem ser testadas isoladamente.
"""

from collections.abc import Iterable
from decimal import Decimal

from financeiro.modelos import Lancamento

ZERO = Decimal(0)

# A partir de quantos % do total de despesas uma categoria é considerada
# de alta concentração.
LIMITE_CONCENTRACAO = Decimal(20)


def filtrar_por_tipo(lancamentos: Iterable[Lancamento], tipo: str) -> list[Lancamento]:
    """Devolve só os lançamentos do `tipo` pedido ("receita" ou "despesa")."""
    return [lancamento for lancamento in lancamentos if lancamento.tipo == tipo]


def somar(lancamentos: Iterable[Lancamento]) -> Decimal:
    """Soma os valores dos lançamentos (0 se não houver nenhum)."""
    return sum((lancamento.valor for lancamento in lancamentos), ZERO)


def calcular_percentual(parte: Decimal, todo: Decimal) -> Decimal:
    """Devolve quanto `parte` representa de `todo`, em porcentagem.

    Quando `todo` é zero (por exemplo, um período sem nenhuma receita),
    devolve 0 em vez de lançar ZeroDivisionError.
    """
    if todo == 0:
        return ZERO
    return parte / todo * 100


def calcular_media(total: Decimal, quantidade: int) -> Decimal:
    """Devolve a média `total / quantidade`, ou 0 se não houver itens."""
    if quantidade == 0:
        return ZERO
    return total / quantidade


def encontrar_maior_e_menor(
    lancamentos: list[Lancamento],
) -> tuple[Lancamento, Lancamento]:
    """Devolve o lançamento de maior valor e o de menor valor.

    Em caso de empate, vale o que aparece primeiro na lista.
    """
    maior = max(lancamentos, key=lambda lancamento: lancamento.valor)
    menor = min(lancamentos, key=lambda lancamento: lancamento.valor)
    return maior, menor


def somar_por_mes(
    lancamentos: Iterable[Lancamento], tipo: str
) -> dict[tuple[int, int], Decimal]:
    """Soma os valores de um tipo em cada mês.

    A chave é a tupla (ano, mês), para que janeiro/2026 e janeiro/2027
    fiquem separados. Tuplas são ordenadas elemento a elemento, então
    sorted() nas chaves já devolve os meses em ordem cronológica.
    """
    totais: dict[tuple[int, int], Decimal] = {}
    for lancamento in filtrar_por_tipo(lancamentos, tipo):
        chave = (lancamento.data.year, lancamento.data.month)
        totais[chave] = totais.get(chave, ZERO) + lancamento.valor
    return totais


def somar_por_categoria(
    lancamentos: Iterable[Lancamento], tipo: str
) -> dict[str, Decimal]:
    """Soma os valores de um tipo em cada categoria.

    As categorias ficam na ordem em que aparecem pela primeira vez.
    """
    totais: dict[str, Decimal] = {}
    for lancamento in filtrar_por_tipo(lancamentos, tipo):
        categoria = lancamento.categoria
        totais[categoria] = totais.get(categoria, ZERO) + lancamento.valor
    return totais


def ranking_categorias(totais: dict[str, Decimal]) -> list[tuple[str, Decimal]]:
    """Devolve (categoria, total) do maior para o menor total.

    Empates mantêm a ordem original, porque sorted() é estável.
    """
    return sorted(totais.items(), key=lambda item: item[1], reverse=True)


def maior_categoria(totais: dict[str, Decimal]) -> tuple[str, Decimal]:
    """Devolve a categoria com maior total, ou ("", 0) se não houver nenhuma."""
    if not totais:
        return "", ZERO
    return ranking_categorias(totais)[0]


def tem_alta_concentracao(
    percentual: Decimal, limite: Decimal = LIMITE_CONCENTRACAO
) -> bool:
    """Diz se uma categoria concentra `limite`% ou mais das despesas."""
    return percentual >= limite
