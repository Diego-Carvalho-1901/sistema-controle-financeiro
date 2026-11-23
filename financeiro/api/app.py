"""Aplicação FastAPI com o CRUD de lançamentos.

Ainda não há login: o usuário vem no caminho da URL
(/usuarios/{usuario_id}/lancamentos). A autenticação entra numa issue
futura; até lá, a API é para uso local.
"""

from datetime import date

from fastapi import APIRouter, FastAPI, HTTPException, Response, status
from sqlalchemy import Engine

from financeiro.api import resumos
from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import (
    Conta,
    LancamentoEntrada,
    LancamentoSaida,
    UsuarioEntrada,
    UsuarioSaida,
)
from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes

ROTA_LANCAMENTOS = "/usuarios/{usuario_id}/lancamentos"


def _lancamento_nao_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "lançamento não encontrado")


rotas = APIRouter()


@rotas.post("/usuarios", status_code=status.HTTP_201_CREATED, tags=["usuários"])
def criar_usuario(dados: UsuarioEntrada, repo: Repositorio) -> UsuarioSaida:
    """Cadastra um usuário."""
    usuario_id = repo.criar_usuario(dados.nome)
    repo.sessao.commit()
    return UsuarioSaida(id=usuario_id, nome=dados.nome)


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


def criar_app(engine: Engine | None = None) -> FastAPI:
    """Cria a aplicação ligada ao banco do `engine` (ou ao padrão).

    Receber o engine por parâmetro deixa os testes usarem um banco
    temporário sem mexer no financeiro.db.
    """
    app = FastAPI(
        title="Controle financeiro para autônomos",
        description="Lançamentos de receitas, despesas e vendas por usuário.",
    )
    app.state.fabrica_de_sessoes = criar_fabrica_de_sessoes(engine or criar_engine())
    app.include_router(rotas)
    app.include_router(resumos.rotas)
    return app


# Usado pelo uvicorn: `uvicorn financeiro.api.app:app --reload`.
app = criar_app()
