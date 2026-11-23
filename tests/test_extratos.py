"""Testes dos extratos de banco, um grupo por formato (dados fictícios)."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from financeiro.banco.conexao import criar_fabrica_de_sessoes
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.extratos import (
    INTER,
    NUBANK,
    converter_valor_do_extrato,
    detectar,
    ler_extrato,
)
from financeiro.importacao import importar_csv
from financeiro.leitura import ErroLeitura

EXEMPLOS = Path(__file__).resolve().parents[1] / "dados" / "extratos"
NUBANK_CSV = EXEMPLOS / "nubank_exemplo.csv"
INTER_CSV = EXEMPLOS / "inter_exemplo.csv"


def lancamentos(texto: str, **opcoes):
    return [resultado for _linha, resultado in ler_extrato(texto, **opcoes)]


# --- Detecção ---


def test_detecta_cada_banco_pelo_cabecalho():
    assert detectar(NUBANK_CSV.read_text("utf-8")) == (NUBANK, 0)
    # No Inter o cabeçalho vem depois de 5 linhas de apresentação.
    assert detectar(INTER_CSV.read_text("utf-8")) == (INTER, 5)


def test_csv_do_app_nao_e_extrato():
    assert detectar("data,valor,tipo,categoria,descricao\n") is None


# --- Nubank ---


def test_nubank_valor_negativo_e_despesa_e_positivo_e_receita():
    salario, mercado, *_ = lancamentos(NUBANK_CSV.read_text("utf-8"))

    assert (salario.tipo, salario.valor, salario.data) == (
        "receita",
        Decimal("1800.00"),
        date(2026, 11, 1),
    )
    assert (mercado.tipo, mercado.valor) == ("despesa", Decimal("45.90"))
    assert mercado.descricao == "Compra no débito - SUPERMERCADO EXEMPLO"


def test_nubank_le_todas_as_linhas_do_exemplo():
    assert len(lancamentos(NUBANK_CSV.read_text("utf-8"))) == 5


# --- Inter ---


def test_inter_pula_a_apresentacao_e_le_valores_com_virgula():
    pix, farinha, das, grafica = lancamentos(INTER_CSV.read_text("utf-8"))

    assert (pix.tipo, pix.valor) == ("receita", Decimal("350.00"))
    assert (farinha.tipo, farinha.valor) == ("despesa", Decimal("123.45"))
    assert grafica.valor == Decimal("1250.00")  # "-1.250,00"
    assert das.data == date(2026, 11, 6)


@pytest.mark.parametrize(
    ("texto", "virgula", "esperado"),
    [
        ("-45.90", False, "-45.90"),
        ("1800.00", False, "1800.00"),
        ("-1.234,56", True, "-1234.56"),
        ("R$ -45,90", True, "-45.90"),
        ("−45,90", True, "-45.90"),  # sinal de menos tipográfico
    ],
)
def test_converte_valores_dos_extratos(texto, virgula, esperado):
    assert converter_valor_do_extrato(texto, virgula) == Decimal(esperado)


# --- Regras comuns ---


def test_categoria_vem_da_funcao_de_categorizar_ou_outros():
    texto = NUBANK_CSV.read_text("utf-8")

    sem_regra = lancamentos(texto)
    com_regra = lancamentos(texto, categorizar=lambda d: "x" if "POSTO" in d else None)

    assert {lanc.categoria for lanc in sem_regra} == {"outros"}
    assert [lanc.categoria for lanc in com_regra].count("x") == 1


def test_conta_do_extrato_vale_para_todas_as_linhas():
    resultado = lancamentos(INTER_CSV.read_text("utf-8"), conta="negocio")

    assert {lanc.conta for lanc in resultado} == {"negocio"}


def test_linhas_invalidas_viram_erro_com_o_numero_da_linha():
    texto = (
        "Data,Valor,Identificador,Descrição\n"
        "31/02/2026,-10.00,id1,Data impossível\n"
        "01/11/2026,abc,id2,Valor inválido\n"
        "01/11/2026,0.00,id3,Zerado\n"
        "01/11/2026,-5.00,id4\n"
        "01/11/2026,-5.00,id5,Ok\n"
    )

    resultados = list(ler_extrato(texto))

    erros = [str(r) for _, r in resultados if isinstance(r, ErroLeitura)]
    assert erros == [
        "Linha 2: data inválida '31/02/2026'.",
        "Linha 3: valor inválido 'abc'.",
        "Linha 4: valor zerado.",
        (
            "Linha 5: esperadas 4 colunas no extrato Nubank (conta), "
            "mas foram encontradas 3."
        ),
    ]
    assert resultados[-1][0] == 6


# --- Importação para o banco ---


@pytest.fixture
def repo(engine):
    with criar_fabrica_de_sessoes(engine)() as sessao:
        yield RepositorioLancamentos(sessao)


@pytest.mark.parametrize(("arquivo", "quantidade"), [(NUBANK_CSV, 5), (INTER_CSV, 4)])
def test_importa_cada_extrato_e_nao_duplica_ao_reimportar(repo, arquivo, quantidade):
    usuario = repo.criar_usuario("Ana")

    primeira = importar_csv(repo, usuario, arquivo)
    segunda = importar_csv(repo, usuario, arquivo)

    assert (primeira.importadas, primeira.erros) == (quantidade, [])
    assert (segunda.importadas, len(segunda.ignoradas)) == (0, quantidade)


def test_importacao_usa_dicionario_e_regras_do_usuario(repo):
    usuario = repo.criar_usuario("Ana")
    repo.aprender_regra(usuario, "netflix", "assinaturas")

    importar_csv(repo, usuario, NUBANK_CSV)

    categorias = {
        lanc.descricao.split(" - ")[-1]: lanc.categoria for lanc in repo.listar(usuario)
    }
    assert categorias["POSTO EXEMPLO"] == "transporte"  # dicionário padrão
    assert categorias["NETFLIX"] == "assinaturas"  # regra da Ana vence


def test_aceita_extrato_em_windows_1252(repo, tmp_path):
    arquivo = tmp_path / "inter_ansi.csv"
    arquivo.write_bytes(INTER_CSV.read_text("utf-8").encode("cp1252"))
    usuario = repo.criar_usuario("Ana")

    assert importar_csv(repo, usuario, arquivo).importadas == 4
