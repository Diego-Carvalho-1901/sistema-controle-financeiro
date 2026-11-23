"""Testes do leitor de frases livres (financeiro/bot/frases.py)."""

from datetime import date
from decimal import Decimal

import pytest

from financeiro.bot.frases import FraseNaoEntendida, converter_valor, interpretar

HOJE = date(2026, 11, 23)


def ler(frase: str):
    return interpretar(frase, hoje=HOJE)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("45", "45"),
        ("45,9", "45.9"),
        ("45,90", "45.90"),
        ("45.90", "45.90"),
        ("1.800", "1800"),
        ("1.800,50", "1800.50"),
        ("12.345.678,00", "12345678.00"),
        ("R$45", "45"),
        ("r$1.200,00", "1200.00"),
    ],
)
def test_converte_valores_no_formato_brasileiro(texto, esperado):
    assert converter_valor(texto) == Decimal(esperado)


# (frase, tipo, valor, conta, descrição)
SIMPLES = [
    ("gastei 30 almoço", "despesa", "30", "pessoal", "almoço"),
    ("Gastei 30 no almoço", "despesa", "30", "pessoal", "almoço"),
    ("gastei 30 reais com almoço", "despesa", "30", "pessoal", "almoço"),
    ("gastei R$ 30,50 almoço", "despesa", "30.50", "pessoal", "almoço"),
    ("gastei R$30 almoço", "despesa", "30", "pessoal", "almoço"),
    ("almoço gastei 30", "despesa", "30", "pessoal", "almoço"),
    ("paguei 120,50 na conta de luz", "despesa", "120.50", "pessoal", "conta de luz"),
    ("comprei farinha 18.90 pra loja", "despesa", "18.90", "negocio", "farinha"),
    ("gastei 1.200 aluguel da loja", "despesa", "1200", "negocio", "aluguel"),
    ("gastei 80 gasolina negócio", "despesa", "80", "negocio", "gasolina"),
    ("gastei 80 gasolina negocio", "despesa", "80", "negocio", "gasolina"),
    ("paguei 50 internet da empresa", "despesa", "50", "negocio", "internet"),
    ("gasto de 25 com uber", "despesa", "25", "pessoal", "uber"),
    ("gastei 60 mercado pessoal", "despesa", "60", "pessoal", "mercado"),
    ("GASTEI 10 PÃO", "despesa", "10", "pessoal", "PÃO"),
    ("gastei 30 almoço!", "despesa", "30", "pessoal", "almoço"),
    ("recebi 1800 salário", "receita", "1800", "pessoal", "salário"),
    ("recebi 1.800,00 de salário", "receita", "1800", "pessoal", "salário"),
    ("ganhei 200 freela", "receita", "200", "pessoal", "freela"),
    ("entrou 350 serviço na empresa", "receita", "350", "negocio", "serviço"),
    ("recebi 500 do cliente pelo trabalho", "receita", "500", "negocio", "cliente"),
]


@pytest.mark.parametrize(("frase", "tipo", "valor", "conta", "descricao"), SIMPLES)
def test_entende_gastos_e_recebimentos(frase, tipo, valor, conta, descricao):
    lido = ler(frase)

    assert (lido.tipo, lido.valor, lido.conta, lido.descricao) == (
        tipo,
        Decimal(valor),
        conta,
        descricao,
    )
    assert lido.data == HOJE
    assert lido.produto is None and lido.quantidade is None


# (frase, quantidade, valor total, produto)
VENDAS = [
    ("vendi 3 bolos 45", 3, "45", "bolos"),
    ("vendi bolo 45", 1, "45", "bolo"),
    ("vendi 3 bolos por 45 reais", 3, "45", "bolos"),
    ("vendi 3 bolos de cenoura 45", 3, "45", "bolos de cenoura"),
    ("vendi 3 bolos a 15 cada", 3, "45", "bolos"),
    ("vendi 3x brigadeiro 2,50 cada", 3, "7.50", "brigadeiro"),
    ("vendi x10 brigadeiro 25", 10, "25", "brigadeiro"),
    ("vendemos 2 tortas R$ 90,00", 2, "90", "tortas"),
    ("Vendi 1 kit festa 120", 1, "120", "kit festa"),
    ("vendi 3 bolos 45 na loja", 3, "45", "bolos"),
]


@pytest.mark.parametrize(("frase", "quantidade", "valor", "produto"), VENDAS)
def test_entende_vendas(frase, quantidade, valor, produto):
    lido = ler(frase)

    assert lido.tipo == "venda"
    assert lido.conta == "negocio"  # venda é sempre do negócio
    assert (lido.quantidade, lido.valor, lido.produto) == (
        quantidade,
        Decimal(valor),
        produto,
    )


def test_ontem_muda_a_data():
    assert ler("gastei 30 almoço ontem").data == date(2026, 11, 22)
    assert ler("ontem vendi 2 bolos 30").data == date(2026, 11, 22)


def test_categoria_provisoria_e_a_primeira_palavra_em_minusculas():
    assert ler("paguei 120 Conta de luz").categoria == "conta"


def test_converte_para_o_json_da_api():
    assert ler("vendi 3 bolos 45").para_json() == {
        "data": "2026-11-23",
        "valor": "45.00",
        "tipo": "venda",
        "categoria": "bolos",
        "descricao": "bolos",
        "conta": "negocio",
        "produto": "bolos",
        "quantidade": 3,
    }


AMBIGUAS = [
    ("", "vazia"),
    ("   ", "vazia"),
    ("almoço 30", "venda, gasto ou recebimento"),
    ("oi, tudo bem?", "venda, gasto ou recebimento"),
    ("gastei almoço", "faltou o valor"),
    ("gastei 30", "faltou dizer com o que foi"),
    ("gastei 30 e 20 no almoço", "qual número é o valor"),
    ("gastei 3x 20 almoço", "qual número é o valor"),
    ("vendi bolos", "faltou o valor"),
    ("vendi 45", "faltou dizer o que foi vendido"),
    ("vendi 3 bolos 15 e 2 tortas 40", "qual número é o valor"),
    ("vendi 2,5 bolos 30", "número inteiro"),
    ("vendi bolo 45 pessoal", "vendas sempre são do negócio"),
    ("gastei 30 almoço e recebi 50", "mais de um tipo"),
    ("gastei 30 almoço negócio pessoal", "negócio ou pessoal"),
    ("gastei 0 almoço", "maior que zero"),
    ("gastei 0,00 almoço", "maior que zero"),
]


@pytest.mark.parametrize(("frase", "motivo"), AMBIGUAS)
def test_frases_ambiguas_nao_viram_lancamento(frase, motivo):
    with pytest.raises(FraseNaoEntendida, match=motivo):
        ler(frase)
