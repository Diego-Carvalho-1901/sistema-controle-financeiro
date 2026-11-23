"""Rotas de resumo: os números prontos para o bot e o painel.

Todas as somas acontecem no banco (financeiro/banco/resumos.py); as rotas
só validam os parâmetros e convertem o resultado em JSON.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import (
    CategoriaTotalSaida,
    Conta,
    ResumoMesSaida,
    ResumoNegocioSaida,
    SaldoPessoalSaida,
    Tipo,
)
from financeiro.banco import resumos

ROTA = "/usuarios/{usuario_id}/resumos"
CENTAVO = Decimal("0.01")

rotas = APIRouter(prefix=ROTA, tags=["resumos"])


def _reais(valor: Decimal) -> Decimal:
    """Arredonda para 2 casas, para o JSON sair sempre como "12.30"."""
    return valor.quantize(CENTAVO)


def _validar_periodo(inicio: date | None, fim: date | None) -> None:
    if inicio is not None and fim is not None and inicio > fim:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "inicio deve ser antes de fim"
        )


@rotas.get("/mensal")
def resumo_mensal(
    usuario_id: int,
    repo: Repositorio,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[ResumoMesSaida]:
    """Receitas, despesas, vendas e saldo de cada mês."""
    exigir_usuario(repo, usuario_id)
    _validar_periodo(inicio, fim)
    return [
        ResumoMesSaida(
            ano=mes.ano,
            mes=mes.mes,
            receitas=_reais(mes.receitas),
            despesas=_reais(mes.despesas),
            vendas=_reais(mes.vendas),
            saldo=_reais(mes.saldo),
        )
        for mes in resumos.resumo_por_mes(repo.sessao, usuario_id, inicio, fim)
    ]


@rotas.get("/categorias")
def resumo_categorias(
    usuario_id: int,
    repo: Repositorio,
    tipo: Tipo = "despesa",
    conta: Conta | None = None,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[CategoriaTotalSaida]:
    """Total por categoria, do maior para o menor."""
    exigir_usuario(repo, usuario_id)
    _validar_periodo(inicio, fim)
    totais = resumos.resumo_por_categoria(
        repo.sessao, usuario_id, tipo, conta, inicio, fim
    )
    return [
        CategoriaTotalSaida(categoria=nome, total=_reais(total))
        for nome, total in totais
    ]


@rotas.get("/negocio")
def resumo_negocio(
    usuario_id: int,
    repo: Repositorio,
    inicio: date | None = None,
    fim: date | None = None,
) -> ResumoNegocioSaida:
    """Faturamento, custos, lucro e margem da conta negócio."""
    exigir_usuario(repo, usuario_id)
    _validar_periodo(inicio, fim)
    resumo = resumos.resumo_negocio(repo.sessao, usuario_id, inicio, fim)
    return ResumoNegocioSaida(
        faturamento=_reais(resumo.faturamento),
        custos=_reais(resumo.custos),
        lucro=_reais(resumo.lucro),
        margem=_reais(resumo.margem),
    )


@rotas.get("/pessoal")
def resumo_pessoal(
    usuario_id: int,
    repo: Repositorio,
    inicio: date | None = None,
    fim: date | None = None,
) -> SaldoPessoalSaida:
    """Saldo da conta pessoal (receitas menos despesas)."""
    exigir_usuario(repo, usuario_id)
    _validar_periodo(inicio, fim)
    saldo = resumos.saldo_pessoal(repo.sessao, usuario_id, inicio, fim)
    return SaldoPessoalSaida(saldo=_reais(saldo))
