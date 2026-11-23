"""Consulta das metas mensais com quanto já foi gasto em cada categoria."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro.banco.repositorio import centavos_para_reais
from financeiro.banco.tabelas import Categoria, LancamentoTabela, Meta
from financeiro.calculos import calcular_percentual

L = LancamentoTabela


@dataclass(frozen=True)
class SituacaoMeta:
    """Uma meta e o quanto dela já foi usado no período."""

    categoria: str
    meta: Decimal
    gasto: Decimal

    @property
    def percentual(self) -> Decimal:
        """Quanto da meta já foi gasto, em % (pode passar de 100)."""
        return calcular_percentual(self.gasto, self.meta)


def metas_com_gasto(
    sessao: Session, usuario_id: int, inicio: date, fim: date
) -> list[SituacaoMeta]:
    """Cada meta do usuário com o total de despesas da categoria no período.

    SQL gerado (simplificado):

        SELECT c.nome, m.valor_centavos, COALESCE(g.gasto, 0)
        FROM metas m
        JOIN categorias c ON c.id = m.categoria_id
        LEFT JOIN (
            SELECT categoria_id, SUM(valor_centavos) AS gasto
            FROM lancamentos
            WHERE usuario_id = :id AND tipo = 'despesa'
              AND data BETWEEN :inicio AND :fim
            GROUP BY categoria_id
        ) g ON g.categoria_id = m.categoria_id
        WHERE m.usuario_id = :id

    O LEFT JOIN mantém as metas de categorias sem nenhum gasto no período
    (com um JOIN comum elas sumiriam do resultado).
    """
    gastos = (
        select(L.categoria_id, func.sum(L.valor_centavos).label("gasto"))
        .where(
            L.usuario_id == usuario_id,
            L.tipo == "despesa",
            L.data >= inicio,
            L.data <= fim,
        )
        .group_by(L.categoria_id)
        .subquery()
    )
    consulta = (
        select(
            Categoria.nome,
            Meta.valor_centavos,
            func.coalesce(gastos.c.gasto, 0),
        )
        .join(Meta.categoria)
        .outerjoin(gastos, gastos.c.categoria_id == Meta.categoria_id)
        .where(Meta.usuario_id == usuario_id)
        .order_by(Categoria.nome)
    )
    return [
        SituacaoMeta(nome, centavos_para_reais(meta), centavos_para_reais(gasto))
        for nome, meta, gasto in sessao.execute(consulta)
    ]
