"""Aplicação FastAPI com o CRUD de lançamentos.

Ainda não há login: o usuário vem no caminho da URL
(/usuarios/{usuario_id}/lancamentos). A autenticação entra numa issue
futura; até lá, a API é para uso local.
"""

import logging
import os
import secrets
from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine, text

from financeiro.api import categorias, metas, resumos
from financeiro.api.dependencias import (
    Repositorio,
    exigir_chave_api,
    exigir_usuario,
)
from financeiro.api.esquemas import (
    Conta,
    LancamentoEntrada,
    LancamentoSaida,
    UsuarioEntrada,
    UsuarioSaida,
)
from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.painel import rotas as painel

ROTA_LANCAMENTOS = "/usuarios/{usuario_id}/lancamentos"


def _lancamento_nao_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "lançamento não encontrado")


rotas = APIRouter()


@rotas.post("/usuarios", status_code=status.HTTP_201_CREATED, tags=["usuários"])
def criar_usuario(dados: UsuarioEntrada, repo: Repositorio) -> UsuarioSaida:
    """Cadastra um usuário."""
    if dados.telegram_id is not None and repo.buscar_usuario_por_telegram(
        dados.telegram_id
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "já existe um usuário com esse telegram_id"
        )
    usuario_id = repo.criar_usuario(dados.nome, dados.telegram_id)
    repo.sessao.commit()
    return UsuarioSaida(id=usuario_id, **dados.model_dump())


@rotas.get("/usuarios", tags=["usuários"])
def listar_usuarios(repo: Repositorio) -> list[UsuarioSaida]:
    """Usuários com conta do Telegram (o bot usa no resumo semanal)."""
    return [
        UsuarioSaida(id=usuario.id, nome=usuario.nome, telegram_id=usuario.telegram_id)
        for usuario in repo.listar_usuarios_do_telegram()
    ]


@rotas.get("/usuarios/telegram/{telegram_id}", tags=["usuários"])
def obter_usuario_do_telegram(telegram_id: int, repo: Repositorio) -> UsuarioSaida:
    """Devolve o usuário ligado a uma conta do Telegram (usado pelo bot)."""
    usuario = repo.buscar_usuario_por_telegram(telegram_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "usuário não encontrado")
    return UsuarioSaida(
        id=usuario.id, nome=usuario.nome, telegram_id=usuario.telegram_id
    )


@rotas.post(ROTA_LANCAMENTOS, status_code=status.HTTP_201_CREATED, tags=["lançamentos"])
def criar_lancamento(
    usuario_id: int, dados: LancamentoEntrada, repo: Repositorio
) -> LancamentoSaida:
    """Cria um lançamento para o usuário."""
    exigir_usuario(repo, usuario_id)
    lancamento = dados.para_lancamento()
    id_ = repo.adicionar(usuario_id, lancamento)
    repo.sessao.commit()
    return LancamentoSaida.de_lancamento(id_, lancamento)


@rotas.get(ROTA_LANCAMENTOS, tags=["lançamentos"])
def listar_lancamentos(
    usuario_id: int,
    repo: Repositorio,
    inicio: date | None = None,
    fim: date | None = None,
    conta: Conta | None = None,
    categoria: str | None = None,
) -> list[LancamentoSaida]:
    """Lista os lançamentos em ordem de data, com filtros opcionais."""
    exigir_usuario(repo, usuario_id)
    registros = repo.listar_com_ids(usuario_id, inicio, fim, conta, categoria)
    return [LancamentoSaida.de_lancamento(id_, lanc) for id_, lanc in registros]


@rotas.delete(ROTA_LANCAMENTOS + "/ultimo", tags=["lançamentos"])
def excluir_ultimo_lancamento(usuario_id: int, repo: Repositorio) -> LancamentoSaida:
    """Exclui o lançamento gravado por último e devolve como ele era.

    Fica antes das rotas com /{lancamento_id}: o FastAPI testa as rotas na
    ordem em que foram registradas.
    """
    exigir_usuario(repo, usuario_id)
    apagado = repo.excluir_ultimo(usuario_id)
    if apagado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "nenhum lançamento para excluir")
    repo.sessao.commit()
    return LancamentoSaida.de_lancamento(*apagado)


@rotas.get(ROTA_LANCAMENTOS + "/{lancamento_id}", tags=["lançamentos"])
def obter_lancamento(
    usuario_id: int, lancamento_id: int, repo: Repositorio
) -> LancamentoSaida:
    """Devolve um lançamento pelo id."""
    lancamento = repo.buscar(usuario_id, lancamento_id)
    if lancamento is None:
        raise _lancamento_nao_encontrado()
    return LancamentoSaida.de_lancamento(lancamento_id, lancamento)


@rotas.put(ROTA_LANCAMENTOS + "/{lancamento_id}", tags=["lançamentos"])
def editar_lancamento(
    usuario_id: int,
    lancamento_id: int,
    dados: LancamentoEntrada,
    repo: Repositorio,
) -> LancamentoSaida:
    """Substitui todos os campos de um lançamento."""
    lancamento = dados.para_lancamento()
    if not repo.atualizar(usuario_id, lancamento_id, lancamento):
        raise _lancamento_nao_encontrado()
    repo.sessao.commit()
    return LancamentoSaida.de_lancamento(lancamento_id, lancamento)


@rotas.delete(
    ROTA_LANCAMENTOS + "/{lancamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["lançamentos"],
)
def excluir_lancamento(
    usuario_id: int, lancamento_id: int, repo: Repositorio
) -> Response:
    """Exclui um lançamento."""
    if not repo.excluir(usuario_id, lancamento_id):
        raise _lancamento_nao_encontrado()
    repo.sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def verificar_saude(request: Request) -> dict:
    """Responde se a API e o banco estão no ar (para a hospedagem monitorar).

    Fica fora da chave da API e não devolve nenhum dado de usuário.
    """
    with request.app.state.fabrica_de_sessoes() as sessao:
        sessao.execute(text("SELECT 1"))
    return {"status": "ok"}


def criar_app(
    engine: Engine | None = None,
    chave_api: str | None = None,
    segredo: str | None = None,
) -> FastAPI:
    """Cria a aplicação ligada ao banco do `engine` (ou ao padrão).

    Receber o engine por parâmetro deixa os testes usarem um banco
    temporário sem mexer no financeiro.db. A `chave_api` (ou a variável
    FINANCEIRO_API_KEY) protege todas as rotas, menos a /saude e o painel,
    que usa login próprio. O `segredo` (ou FINANCEIRO_SEGREDO) assina os
    links e cookies do painel.
    """
    app = FastAPI(
        title="Controle financeiro para autônomos",
        description="Lançamentos de receitas, despesas e vendas por usuário.",
    )
    app.state.fabrica_de_sessoes = criar_fabrica_de_sessoes(engine or criar_engine())
    app.state.chave_api = chave_api or os.environ.get("FINANCEIRO_API_KEY") or None
    app.state.segredo = segredo or os.environ.get("FINANCEIRO_SEGREDO") or None
    if app.state.segredo is None:
        # Sem segredo fixo, cada reinício da API desloga todo mundo do
        # painel. Serve para desenvolver; em produção, defina a variável.
        logging.getLogger(__name__).warning("FINANCEIRO_SEGREDO não definido")
        app.state.segredo = secrets.token_urlsafe(32)
    app.state.cookie_seguro = os.environ.get("FINANCEIRO_COOKIE_SEGURO") == "1"

    protegidas = [Depends(exigir_chave_api)]
    for grupo in (
        rotas,
        resumos.rotas,
        metas.rotas,
        categorias.rotas,
        painel.rotas_link,
    ):
        app.include_router(grupo, dependencies=protegidas)
    app.include_router(painel.rotas_painel)
    app.mount(
        "/painel/estatico",
        StaticFiles(directory=painel.ESTATICO),
        name="painel-estatico",
    )
    app.add_api_route("/saude", verificar_saude, methods=["GET"], tags=["saúde"])
    return app


# Usado pelo uvicorn: `uvicorn financeiro.api.app:app --reload`.
app = criar_app()
