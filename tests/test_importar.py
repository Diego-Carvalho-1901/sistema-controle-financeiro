"""Testes do comando de importação (importar.py)."""

import pytest

from importar import main
from main import CSV_PADRAO


@pytest.fixture
def banco(url_banco, engine):
    """URL de um banco já com as tabelas criadas (veja tests/conftest.py)."""
    return url_banco


def test_importa_e_reimporta_o_csv_de_exemplo(banco, capsys):
    argumentos = [str(CSV_PADRAO), "--usuario", "Ana", "--banco", banco]

    assert main(argumentos) == 0
    primeira = capsys.readouterr().out
    assert main(argumentos) == 0
    segunda = capsys.readouterr().out

    assert "Linhas importadas: 0" not in primeira
    assert "Linhas importadas: 0" in segunda
    assert "Linhas com erro: 0" in segunda


def test_linha_invalida_aparece_no_relatorio_e_sai_com_codigo_1(
    banco, tmp_path, capsys
):
    arquivo = tmp_path / "com_erro.csv"
    arquivo.write_text(
        "data,valor,tipo,categoria,descricao\n"
        "01/09/2026,10.00,despesa,mercado,Pão\n"
        "01/09/2026,dez,despesa,mercado,Leite\n",
        encoding="utf-8",
    )

    assert main([str(arquivo), "--usuario", "Ana", "--banco", banco]) == 1

    saida = capsys.readouterr().out
    assert "Linhas importadas: 1" in saida
    assert "Linha 3: valor inválido 'dez'." in saida


def test_arquivo_inexistente(banco, tmp_path, capsys):
    caminho = str(tmp_path / "nao_existe.csv")

    assert main([caminho, "--usuario", "Ana", "--banco", banco]) == 1
    assert "arquivo não encontrado" in capsys.readouterr().err
