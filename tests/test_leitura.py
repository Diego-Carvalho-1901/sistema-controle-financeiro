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
