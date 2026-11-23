"""Rotas das metas mensais de gastos por categoria."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Path

from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import MetaEntrada, MetaSaida
from financeiro.banco.metas import metas_com_gasto
from financeiro.periodos import mes_de

CENTAVO = Decimal("0.01")

# Mesmo limite de tamanho do nome de categoria nos lançamentos.
NomeCategoria = Annotated[str, Path(min_length=1, max_length=50)]

rotas = APIRouter(prefix="/usuarios/{usuario_id}/metas", tags=["metas"])


@rotas.put("/{categoria}")
def definir_meta(
    usuario_id: int,
    categoria: NomeCategoria,
    dados: MetaEntrada,
    repo: Repositorio,
) -> list[MetaSaida]:
    """Cria ou troca a meta da categoria; devolve todas as metas do mês."""
    exigir_usuario(repo, usuario_id)
    repo.definir_meta(usuario_id, categoria.lower(), dados.valor)
    repo.sessao.commit()
    return listar_metas(usuario_id, repo)


@rotas.get("")
def listar_metas(
    usuario_id: int, repo: Repositorio, dia: date | None = None
) -> list[MetaSaida]:
    """Metas com o gasto do mês de `dia` (padrão: o mês atual)."""
    exigir_usuario(repo, usuario_id)
    inicio, fim = mes_de(dia or date.today())
    return [
        MetaSaida(
            categoria=situacao.categoria,
            meta=situacao.meta.quantize(CENTAVO),
            gasto=situacao.gasto.quantize(CENTAVO),
            percentual=situacao.percentual.quantize(CENTAVO),
        )
        for situacao in metas_com_gasto(repo.sessao, usuario_id, inicio, fim)
    ]
