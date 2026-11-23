"""Rotas das metas mensais de gastos por categoria."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Path

from financeiro.alertas import metas_para_alertar
from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import MetaEntrada, MetaSaida
from financeiro.banco.metas import SituacaoMeta, metas_com_gasto
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
        _para_saida(situacao)
        for situacao in metas_com_gasto(repo.sessao, usuario_id, inicio, fim)
    ]


@rotas.post("/alertas")
def gerar_alertas(
    usuario_id: int, repo: Repositorio, dia: date | None = None
) -> list[MetaSaida]:
    """Metas que acabaram de chegar a 80% no mês de `dia`.

    Cada categoria aparece só na primeira chamada do mês: a resposta já
    marca o alerta como enviado. Por isso é POST (muda o estado), e chamar
    de novo devolve uma lista vazia.
    """
    exigir_usuario(repo, usuario_id)
    dia = dia or date.today()
    inicio, fim = mes_de(dia)
    situacoes = metas_com_gasto(repo.sessao, usuario_id, inicio, fim)
    ja_alertadas = repo.categorias_alertadas(usuario_id, dia.year, dia.month)
    novas = metas_para_alertar(situacoes, ja_alertadas)
    for situacao in novas:
        repo.registrar_alerta(usuario_id, situacao.categoria, dia.year, dia.month)
    repo.sessao.commit()
    return [_para_saida(situacao) for situacao in novas]


def _para_saida(situacao: SituacaoMeta) -> MetaSaida:
    return MetaSaida(
        categoria=situacao.categoria,
        meta=situacao.meta.quantize(CENTAVO),
        gasto=situacao.gasto.quantize(CENTAVO),
        percentual=situacao.percentual.quantize(CENTAVO),
    )
