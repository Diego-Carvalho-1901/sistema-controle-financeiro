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


def test_main_junta_varios_csvs_no_mesmo_relatorio(capsys):
    pasta = CSV_PADRAO.parent
    arquivos = ["movimentacoes.csv", "vendas.csv", "negocio.csv"]

    assert main([str(pasta / nome) for nome in arquivos]) == 0

    saida = capsys.readouterr().out
    # vendas.csv: 4x45 + 100x2,50 + 3x55 + 60x2,50 = 745; negocio.csv: +350
    assert "Faturamento do negócio: R$ 1095.00" in saida
    assert "Custos do negócio: R$ 285.00" in saida
    assert "Lucro do negócio: R$ 810.00" in saida


def test_main_erro_indica_qual_arquivo(tmp_path, capsys):
    ruim = tmp_path / "ruim.csv"
    ruim.write_text("dia,quanto\n01/09/2026,10\n", encoding="utf-8")

    assert main([str(CSV_PADRAO), str(ruim)]) == 1
    assert "Erro em ruim.csv: Linha 1" in capsys.readouterr().err
