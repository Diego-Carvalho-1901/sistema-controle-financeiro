"""Testes da categorização por palavras-chave."""

import pytest

from financeiro.categorizacao import (
    palavra_para_aprender,
    palavras_chave,
    sugerir_categoria,
)


@pytest.mark.parametrize(
    ("descricao", "categoria"),
    [
        ("posto", "transporte"),
        ("Posto Shell", "transporte"),
        ("uber pro centro", "transporte"),
        ("almoço", "alimentacao"),
        ("ALMOÇO com cliente", "alimentacao"),
        ("conta de luz", "contas"),
        ("farinha", "insumos"),
        ("salário", "salario"),
        ("remédio", "saude"),
    ],
)
def test_sugere_pelo_dicionario_padrao(descricao, categoria):
    assert sugerir_categoria(descricao, {}) == categoria


def test_palavra_desconhecida_nao_tem_sugestao():
    assert sugerir_categoria("presente da Bia", {}) is None


def test_regra_do_usuario_vence_o_dicionario():
    regras = {"posto": "negocio-entregas"}

    assert sugerir_categoria("posto", regras) == "negocio-entregas"


def test_regra_aprendida_vale_para_palavra_nova():
    assert sugerir_categoria("presente da Bia", {"presente": "presentes"}) == (
        "presentes"
    )


def test_vale_a_primeira_palavra_conhecida():
    assert sugerir_categoria("lanche no posto", {}) == "alimentacao"


def test_palavras_chave_normaliza_e_tira_repeticoes():
    assert palavras_chave("Pão, pão e Café!") == ["pao", "e", "cafe"]


@pytest.mark.parametrize(
    ("descricao", "palavra"),
    [
        ("presente da Bia", "presente"),
        ("de lá pra cá", None),
        ("pra 99 até casa", "casa"),
        ("Açaí", "acai"),
    ],
)
def test_palavra_para_aprender(descricao, palavra):
    assert palavra_para_aprender(descricao) == palavra
