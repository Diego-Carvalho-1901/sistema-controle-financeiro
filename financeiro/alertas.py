"""Regra do alerta de meta (issue [16]).

Uma categoria gera alerta quando o gasto do mês chega a 80% da meta. O
alerta sai uma vez por mês por categoria: quem decide se já saiu é a
tabela alertas_meta, e esta função só aplica a regra.
"""

from collections.abc import Iterable
from decimal import Decimal

from financeiro.banco.metas import SituacaoMeta

LIMITE_ALERTA = Decimal(80)


def metas_para_alertar(
    situacoes: Iterable[SituacaoMeta],
    ja_alertadas: set[str],
    limite: Decimal = LIMITE_ALERTA,
) -> list[SituacaoMeta]:
    """Metas que chegaram ao `limite`% e ainda não foram avisadas no mês."""
    return [
        situacao
        for situacao in situacoes
        if situacao.percentual >= limite and situacao.categoria not in ja_alertadas
    ]
