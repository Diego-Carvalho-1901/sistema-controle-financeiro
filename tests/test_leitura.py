"""Testes da leitura do CSV (financeiro/leitura.py)."""

from datetime import date
from decimal import Decimal

import pytest

from financeiro.leitura import ErroLeitura, carregar_csv, ler_lancamentos
from financeiro.modelos import Lancamento

CABECALHO = ["data", "valor", "tipo", "categoria", "descricao"]


def test_converte_data_e_valor():
    linhas = [CABECALHO, ["01/09/2026", "1800.00", "receita", "salario", "Salario"]]

    assert ler_lancamentos(linhas) == [
        Lancamento(
            date(2026, 9, 1), Decimal("1800.00"), "receita", "salario", "Salario"
        )
    ]


def test_valor_vira_decimal_exato():
    linhas = [CABECALHO, ["02/09/2026", "45.90", "despesa", "alimentacao", "Almoco"]]

    (lancamento,) = ler_lancamentos(linhas)

    assert isinstance(lancamento.valor, Decimal)
    assert lancamento.valor == Decimal("45.90")


def test_carregar_csv_le_arquivo_utf8(tmp_path):
    arquivo = tmp_path / "movimentacoes.csv"
    arquivo.write_text(
        "data,valor,tipo,categoria,descricao\n"
        "01/09/2026,10.00,despesa,alimentacao,Pão de queijo\n",
        encoding="utf-8",
    )

    (lancamento,) = carregar_csv(arquivo)

    assert lancamento.descricao == "Pão de queijo"


def test_carregar_csv_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar_csv(tmp_path / "nao_existe.csv")


# --- Erros de conteúdo (bugs da issue [01]) ---


def test_csv_totalmente_vazio():
    with pytest.raises(ErroLeitura, match="vazio"):
        ler_lancamentos([])


def test_csv_so_com_cabecalho():
    with pytest.raises(ErroLeitura, match="nenhuma movimentação"):
        ler_lancamentos([CABECALHO])


def test_linha_com_coluna_faltando_indica_o_numero_da_linha():
    linhas = [
        CABECALHO,
        ["01/09/2026", "1800.00", "receita", "salario", "Salario"],
        ["02/09/2026", "45.90", "despesa", "alimentacao"],
    ]

    with pytest.raises(ErroLeitura, match="Linha 3: esperadas 5 colunas"):
        ler_lancamentos(linhas)


@pytest.mark.parametrize("valor", ["abc", "NaN", "Infinity"])
def test_valor_invalido_indica_o_numero_da_linha(valor):
    linhas = [CABECALHO, ["01/09/2026", valor, "receita", "salario", "Salario"]]

    with pytest.raises(ErroLeitura, match=f"Linha 2: valor inválido '{valor}'"):
        ler_lancamentos(linhas)


def test_data_invalida_indica_o_numero_da_linha():
    linhas = [CABECALHO, ["31/02/2026", "10.00", "despesa", "lazer", "Cinema"]]

    with pytest.raises(ErroLeitura, match="Linha 2: data inválida"):
        ler_lancamentos(linhas)


def test_tipo_invalido_indica_o_numero_da_linha():
    linhas = [CABECALHO, ["01/09/2026", "10.00", "transferencia", "outros", "Pix"]]

    with pytest.raises(ErroLeitura, match="Linha 2: tipo inválido 'transferencia'"):
        ler_lancamentos(linhas)


def test_linhas_em_branco_sao_ignoradas():
    linhas = [CABECALHO, [], ["01/09/2026", "10.00", "despesa", "lazer", "Cinema"]]

    assert len(ler_lancamentos(linhas)) == 1


def test_valor_negativo_e_recusado():
    linhas = [CABECALHO, ["01/09/2026", "-10.00", "despesa", "lazer", "Cinema"]]

    with pytest.raises(ErroLeitura, match="Linha 2: valor inválido '-10.00'"):
        ler_lancamentos(linhas)


def test_cabecalho_desconhecido_e_recusado():
    linhas = [["dia", "quanto"], ["01/09/2026", "10.00"]]

    with pytest.raises(ErroLeitura, match="Linha 1: cabeçalho não reconhecido"):
        ler_lancamentos(linhas)


# --- Conta negócio/pessoal (issue [05]) ---


def test_sem_coluna_conta_tudo_e_pessoal():
    linhas = [CABECALHO, ["01/09/2026", "10.00", "despesa", "lazer", "Cinema"]]

    (lancamento,) = ler_lancamentos(linhas)

    assert lancamento.conta == "pessoal"


def test_coluna_conta_opcional():
    linhas = [
        [*CABECALHO, "conta"],
        ["01/09/2026", "300.00", "despesa", "insumos", "Farinha", "negocio"],
        ["02/09/2026", "50.00", "despesa", "lazer", "Cinema", "pessoal"],
    ]

    negocio, pessoal = ler_lancamentos(linhas)

    assert negocio.conta == "negocio"
    assert pessoal.conta == "pessoal"


def test_conta_invalida_indica_o_numero_da_linha():
    linhas = [
        [*CABECALHO, "conta"],
        ["01/09/2026", "10.00", "despesa", "lazer", "Cinema", "empresa"],
    ]

    with pytest.raises(ErroLeitura, match="Linha 2: conta inválida 'empresa'"):
        ler_lancamentos(linhas)


# --- CSV de vendas do analisador (issue [05]) ---

CSV_VENDAS = (
    "data da venda, produto, categoria, quantidade vendida, preco unitario\n"
    "2024-01-15, Bolo de cenoura, Bolos, 3, 15.00\n"
    "2024-01-16, Brigadeiro, Doces, 20, 2.50\n"
)


def test_csv_de_vendas_do_analisador(tmp_path):
    arquivo = tmp_path / "vendas.csv"
    arquivo.write_text(CSV_VENDAS, encoding="utf-8")

    bolo, brigadeiro = carregar_csv(arquivo)

    assert bolo == Lancamento(
        date(2024, 1, 15),
        Decimal("45.00"),
        "venda",
        "Bolos",
        "Bolo de cenoura",
        conta="negocio",
        produto="Bolo de cenoura",
        quantidade=3,
    )
    assert brigadeiro.valor == Decimal("50.00")


@pytest.mark.parametrize(
    ("linha", "mensagem"),
    [
        (["15/01/2024", "Bolo", "Bolos", "3", "15.00"], "data inválida"),
        (["2024-01-15", "Bolo", "Bolos", "0", "15.00"], "quantidade inválida '0'"),
        (["2024-01-15", "Bolo", "Bolos", "1.5", "15.00"], "quantidade inválida"),
        (["2024-01-15", "Bolo", "Bolos", "3", "abc"], "preço inválido 'abc'"),
        (["2024-01-15", "", "Bolos", "3", "15.00"], "produto em branco"),
    ],
)
def test_venda_invalida_indica_o_numero_da_linha(linha, mensagem):
    cabecalho = [
        "data da venda",
        "produto",
        "categoria",
        "quantidade vendida",
        "preco unitario",
    ]

    with pytest.raises(ErroLeitura, match=f"Linha 2: {mensagem}"):
        ler_lancamentos([cabecalho, linha])
