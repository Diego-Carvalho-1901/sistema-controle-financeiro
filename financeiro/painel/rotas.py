"""Rotas do painel: login pelo link do bot, sessão em cookie e os dados.

Dois grupos de rotas:

- rotas_link: o bot pede um link de login para um usuário. Fica atrás da
  chave da API, como as outras rotas que o bot usa.
- rotas_painel: o que o navegador acessa. Quem identifica o usuário é o
  cookie de sessão, não a URL: ninguém vê os dados de outra pessoa
  trocando um número no endereço.
"""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel

from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import CategoriaTotalSaida, ResumoNegocioSaida
from financeiro.banco import resumos
from financeiro.calculos import ZERO, ResumoNegocio
from financeiro.painel.sessao import LINK, SESSAO, VALIDADE, criar_token, ler_token
from financeiro.periodos import mes_de

COOKIE = "sessao_painel"
ESTATICO = Path(__file__).parent / "estatico"
CENTAVO = Decimal("0.01")

LINK_INVALIDO = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Link inválido</title><body style="font-family:sans-serif;padding:2rem">
<h1>Link inválido ou vencido</h1>
<p>Peça um link novo mandando <b>/painel</b> para o bot no Telegram.</p></body></html>"""


class LinkSaida(BaseModel):
    """Link de login do painel, válido por 10 minutos."""

    url: str


class EuSaida(BaseModel):
    """Quem está logado."""

    nome: str


class MesSaida(BaseModel):
    """Os números de um mês para os cartões e o gráfico de categorias."""

    inicio: date
    fim: date
    negocio: ResumoNegocioSaida
    saldo_pessoal: Decimal
    gastos_por_categoria: list[CategoriaTotalSaida]


class LucroMesSaida(BaseModel):
    """Um ponto do gráfico de evolução do lucro."""

    ano: int
    mes: int
    faturamento: Decimal
    custos: Decimal
    lucro: Decimal


def _reais(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO)


# --- Link de login (usado pelo bot, protegido pela chave da API) ---

rotas_link = APIRouter(tags=["painel"])


@rotas_link.post("/usuarios/{usuario_id}/painel/link")
def criar_link(usuario_id: int, request: Request, repo: Repositorio) -> LinkSaida:
    """Gera o link de login do painel para o usuário."""
    exigir_usuario(repo, usuario_id)
    token = criar_token(request.app.state.segredo, usuario_id, LINK)
    base = os.environ.get("FINANCEIRO_PAINEL_URL") or str(request.base_url)
    return LinkSaida(url=f"{base.rstrip('/')}/painel/entrar?token={token}")


# --- Navegador (identificado pelo cookie) ---

rotas_painel = APIRouter(prefix="/painel", tags=["painel"])


def usuario_logado(request: Request, repo: Repositorio) -> int:
    """Lê o cookie de sessão e devolve o id do usuário (ou responde 401)."""
    token = request.cookies.get(COOKIE)
    usuario_id = token and ler_token(request.app.state.segredo, token, SESSAO)
    if not usuario_id or not repo.usuario_existe(usuario_id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "faça login pelo bot")
    return usuario_id


UsuarioLogado = Annotated[int, Depends(usuario_logado)]


@rotas_painel.get("/", include_in_schema=False)
def pagina() -> FileResponse:
    """A página do painel (o JavaScript dela busca os dados)."""
    return FileResponse(ESTATICO / "index.html")


@rotas_painel.get("/entrar", include_in_schema=False, response_model=None)
def entrar(request: Request, token: str = "") -> RedirectResponse | HTMLResponse:
    """Troca o token do link por um cookie de sessão e abre o painel."""
    usuario_id = ler_token(request.app.state.segredo, token, LINK)
    if usuario_id is None:
        return HTMLResponse(LINK_INVALIDO, status_code=status.HTTP_401_UNAUTHORIZED)
    # 303: depois do login o navegador abre /painel/ com GET, e o token
    # some da barra de endereços (e do histórico).
    resposta = RedirectResponse("/painel/", status_code=status.HTTP_303_SEE_OTHER)
    resposta.set_cookie(
        COOKIE,
        criar_token(request.app.state.segredo, usuario_id, SESSAO),
        max_age=VALIDADE[SESSAO],
        httponly=True,  # o JavaScript da página não consegue ler o cookie
        samesite="lax",  # outros sites não mandam o cookie em POSTs
        secure=request.app.state.cookie_seguro,  # só por HTTPS em produção
    )
    return resposta


@rotas_painel.post("/sair", include_in_schema=False)
def sair() -> RedirectResponse:
    """Apaga o cookie de sessão."""
    resposta = RedirectResponse("/painel/", status_code=status.HTTP_303_SEE_OTHER)
    resposta.delete_cookie(COOKIE)
    return resposta


@rotas_painel.get("/api/eu")
def eu(usuario_id: UsuarioLogado, repo: Repositorio) -> EuSaida:
    """Nome de quem está logado."""
    return EuSaida(nome=repo.nome_do_usuario(usuario_id))


@rotas_painel.get("/api/mes")
def dados_do_mes(
    usuario_id: UsuarioLogado, repo: Repositorio, dia: date | None = None
) -> MesSaida:
    """Negócio, saldo pessoal e gastos por categoria do mês de `dia`."""
    inicio, fim = mes_de(dia or date.today())
    sessao = repo.sessao
    negocio = resumos.resumo_negocio(sessao, usuario_id, inicio, fim)
    gastos = resumos.resumo_por_categoria(
        sessao, usuario_id, "despesa", inicio=inicio, fim=fim
    )
    return MesSaida(
        inicio=inicio,
        fim=fim,
        negocio=ResumoNegocioSaida(
            faturamento=_reais(negocio.faturamento),
            custos=_reais(negocio.custos),
            lucro=_reais(negocio.lucro),
            margem=_reais(negocio.margem),
        ),
        saldo_pessoal=_reais(resumos.saldo_pessoal(sessao, usuario_id, inicio, fim)),
        gastos_por_categoria=[
            CategoriaTotalSaida(categoria=nome, total=_reais(total))
            for nome, total in gastos
        ],
    )


@rotas_painel.get("/api/lucro")
def evolucao_do_lucro(
    usuario_id: UsuarioLogado,
    repo: Repositorio,
    ate: date | None = None,
    meses: Annotated[int, Query(ge=1, le=36)] = 12,
) -> list[LucroMesSaida]:
    """Lucro do negócio em cada um dos últimos `meses` meses até `ate`.

    Meses sem lançamento entram com zero, para o gráfico ter um ponto por
    mês (e não ligar setembro direto a novembro).
    """
    ate = ate or date.today()
    _inicio_ultimo, fim = mes_de(ate)
    ano, mes = divmod(ate.year * 12 + ate.month - 1 - (meses - 1), 12)
    inicio = date(ano, mes + 1, 1)
    por_mes = {
        (ano_, mes_): resumo
        for ano_, mes_, resumo in resumos.lucro_por_mes(
            repo.sessao, usuario_id, inicio, fim
        )
    }
    pontos = []
    for indice in range(meses):
        ano_, mes_ = divmod(inicio.year * 12 + inicio.month - 1 + indice, 12)
        resumo = por_mes.get((ano_, mes_ + 1), ResumoNegocio(ZERO, ZERO))
        pontos.append(
            LucroMesSaida(
                ano=ano_,
                mes=mes_ + 1,
                faturamento=_reais(resumo.faturamento),
                custos=_reais(resumo.custos),
                lucro=_reais(resumo.lucro),
            )
        )
    return pontos
