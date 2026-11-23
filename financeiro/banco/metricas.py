"""Métricas de uso do app (issue [20]): o app está sendo usado de verdade?

Só números agregados: nenhuma consulta daqui devolve nome, descrição ou
valor de lançamento de ninguém.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro.banco.tabelas import LancamentoTabela, Usuario
from financeiro.periodos import semana_de

L = LancamentoTabela


@dataclass(frozen=True)
class SemanaDeUso:
    """Quantas pessoas usaram o app numa semana (segunda a domingo)."""

    inicio: date
    usuarios_ativos: int
    lancamentos: int


@dataclass(frozen=True)
class Metricas:
    """Retrato do uso do app."""

    usuarios: int
    usuarios_com_telegram: int
    lancamentos: int
    usuarios_com_lancamentos: int
    maximo_por_usuario: int
    semanas: list[SemanaDeUso]

    @property
    def media_por_usuario(self) -> float:
        """Lançamentos por usuário que já lançou algo."""
        if self.usuarios_com_lancamentos == 0:
            return 0.0
        return self.lancamentos / self.usuarios_com_lancamentos


def usuarios_ativos_por_semana(
    sessao: Session, hoje: date, semanas: int = 8
) -> list[SemanaDeUso]:
    """Usuários ativos (que gravaram algo) em cada uma das últimas semanas.

    Conta pela hora em que o lançamento foi gravado (criado_em), não pela
    data do gasto: importar um extrato antigo hoje é uso de hoje.

    SQL de cada semana:

        SELECT COUNT(DISTINCT usuario_id), COUNT(*)
        FROM lancamentos
        WHERE criado_em >= :segunda AND criado_em < :proxima_segunda
    """
    segunda_atual, _domingo = semana_de(hoje)
    resultado = []
    for atras in range(semanas - 1, -1, -1):
        inicio = segunda_atual - timedelta(weeks=atras)
        consulta = select(
            func.count(func.distinct(L.usuario_id)), func.count(L.id)
        ).where(
            L.criado_em >= datetime.combine(inicio, time.min),
            L.criado_em < datetime.combine(inicio + timedelta(weeks=1), time.min),
        )
        ativos, lancamentos = sessao.execute(consulta).one()
        resultado.append(SemanaDeUso(inicio, ativos, lancamentos))
    return resultado


def calcular_metricas(sessao: Session, hoje: date, semanas: int = 8) -> Metricas:
    """Totais gerais e a série de usuários ativos por semana."""
    por_usuario = (
        select(L.usuario_id, func.count(L.id).label("quantidade"))
        .group_by(L.usuario_id)
        .subquery()
    )
    com_lancamentos, maximo = sessao.execute(
        select(func.count(), func.coalesce(func.max(por_usuario.c.quantidade), 0))
    ).one()
    return Metricas(
        usuarios=sessao.scalar(select(func.count(Usuario.id))),
        usuarios_com_telegram=sessao.scalar(
            select(func.count(Usuario.id)).where(Usuario.telegram_id.is_not(None))
        ),
        lancamentos=sessao.scalar(select(func.count(L.id))),
        usuarios_com_lancamentos=com_lancamentos,
        maximo_por_usuario=maximo,
        semanas=usuarios_ativos_por_semana(sessao, hoje, semanas),
    )
