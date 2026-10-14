"""Testes do ponto de entrada (main.py)."""

from main import CSV_PADRAO, main


def test_csv_padrao_fica_na_pasta_dados_do_projeto():
    assert CSV_PADRAO.parts[-2:] == ("dados", "movimentacoes.csv")
    assert CSV_PADRAO.is_absolute()
    assert CSV_PADRAO.exists()


def test_main_com_csv_de_exemplo_imprime_relatorio(capsys):
    assert main([]) == 0
    assert "ANALISE FINANCEIRA" in capsys.readouterr().out


def test_main_com_arquivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "nao_existe.csv")]) == 1
    assert "não foi encontrado" in capsys.readouterr().err


def test_main_com_csv_invalido(tmp_path, capsys):
    arquivo = tmp_path / "vazio.csv"
    arquivo.write_text("", encoding="utf-8")

    assert main([str(arquivo)]) == 1
    assert "O arquivo CSV está vazio." in capsys.readouterr().err
