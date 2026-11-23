"""Rota das métricas de uso (issue [20]), protegida pela chave da API."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from financeiro.api.dependencias import Repositorio
from financeiro.banco.metricas import calcular_metricas

rotas = APIRouter(tags=["métricas"])


class SemanaSaida(BaseModel):
    """Uso numa semana (que começa na segunda-feira `inicio`)."""

    inicio: date
    usuarios_ativos: int
    lancamentos: int


class MetricasSaida(BaseModel):
    """Números agregados de uso; sem dado de nenhum usuário específico."""

    usuarios: int
    usuarios_com_telegram: int
    lancamentos: int
    usuarios_com_lancamentos: int
    media_por_usuario: float
    maximo_por_usuario: int
    semanas: list[SemanaSaida]


@rotas.get("/metricas")
def metricas(
    repo: Repositorio,
    dia: date | None = None,
    semanas: Annotated[int, Query(ge=1, le=52)] = 8,
) -> MetricasSaida:
    """Usuários ativos por semana e lançamentos por usuário."""
    resultado = calcular_metricas(repo.sessao, dia or date.today(), semanas)
    return MetricasSaida(
        usuarios=resultado.usuarios,
        usuarios_com_telegram=resultado.usuarios_com_telegram,
        lancamentos=resultado.lancamentos,
        usuarios_com_lancamentos=resultado.usuarios_com_lancamentos,
        media_por_usuario=round(resultado.media_por_usuario, 1),
        maximo_por_usuario=resultado.maximo_por_usuario,
        semanas=[
            SemanaSaida(
                inicio=s.inicio,
                usuarios_ativos=s.usuarios_ativos,
                lancamentos=s.lancamentos,
            )
            for s in resultado.semanas
        ],
    )
