"""Rotas da categorização automática: sugerir e aprender com correções."""

from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from financeiro.api.dependencias import Repositorio, exigir_usuario
from financeiro.api.esquemas import (
    CategoriaEntrada,
    CorrecaoSaida,
    LancamentoSaida,
    SugestaoSaida,
)
from financeiro.categorizacao import palavra_para_aprender, sugerir_categoria

rotas = APIRouter(prefix="/usuarios/{usuario_id}", tags=["categorias"])


@rotas.get("/categorias/sugestao")
def sugerir(
    usuario_id: int,
    descricao: Annotated[str, Query(min_length=1, max_length=200)],
    repo: Repositorio,
) -> SugestaoSaida:
    """Sugere a categoria de uma descrição (regras do usuário primeiro)."""
    exigir_usuario(repo, usuario_id)
    regras = repo.regras_de_categoria(usuario_id)
    return SugestaoSaida(categoria=sugerir_categoria(descricao, regras))


@rotas.put("/lancamentos/ultimo/categoria")
def corrigir_categoria_do_ultimo(
    usuario_id: int, dados: CategoriaEntrada, repo: Repositorio
) -> CorrecaoSaida:
    """Troca a categoria do último lançamento e aprende a regra.

    A palavra principal da descrição passa a apontar para a categoria
    informada, então o próximo lançamento parecido já vem certo.
    """
    exigir_usuario(repo, usuario_id)
    ultimo = repo.ultimo(usuario_id)
    if ultimo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "nenhum lançamento")
    lancamento_id, lancamento = ultimo
    categoria = dados.categoria.strip().lower()
    corrigido = replace(lancamento, categoria=categoria)
    repo.atualizar(usuario_id, lancamento_id, corrigido)

    palavra = palavra_para_aprender(lancamento.descricao)
    if palavra is not None:
        repo.aprender_regra(usuario_id, palavra, categoria)
    repo.sessao.commit()
    return CorrecaoSaida(
        lancamento=LancamentoSaida.de_lancamento(lancamento_id, corrigido),
        palavra_aprendida=palavra,
    )
