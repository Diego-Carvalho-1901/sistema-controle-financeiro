"""Testes do importador de CSV para o banco (financeiro/importacao.py)."""

from decimal import Decimal

import pytest

from financeiro.banco.conexao import criar_engine, criar_fabrica_de_sessoes
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.banco.tabelas import Base
from financeiro.importacao import importar_csv, importar_linhas
from financeiro.leitura import ErroLeitura

CABECALHO = ["data", "valor", "tipo", "categoria", "descricao"]
PAO = ["01/09/2026", "10.00", "despesa", "mercado", "Pão"]
CAFE = ["02/09/2026", "5.50", "despesa", "lazer", "Café"]


@pytest.fixture
def repo():
    """Repositório sobre um banco SQLite em memória, novo a cada teste."""
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    with criar_fabrica_de_sessoes(engine)() as sessao:
        yield RepositorioLancamentos(sessao)
    engine.dispose()


@pytest.fixture
def usuario(repo):
    return repo.criar_usuario("Ana")


def test_importa_linhas_validas(repo, usuario):
    relatorio = importar_linhas(repo, usuario, [CABECALHO, PAO, CAFE])

    assert relatorio.importadas == 2
    assert relatorio.ignoradas == []
    assert relatorio.erros == []
    assert [lanc.descricao for lanc in repo.listar(usuario)] == ["Pão", "Café"]


def test_linhas_invalidas_viram_erro_com_numero_e_as_validas_sao_gravadas(
    repo, usuario
):
    linhas = [
        CABECALHO,
        PAO,
        ["32/09/2026", "1.00", "despesa", "mercado", "Data errada"],
        ["03/09/2026", "1.00", "transferencia", "mercado", "Tipo errado"],
        ["04/09/2026", "1.00", "despesa"],
        CAFE,
    ]

    relatorio = importar_linhas(repo, usuario, linhas)

    assert relatorio.importadas == 2
    assert len(relatorio.erros) == 3
    assert relatorio.erros[0].startswith("Linha 3: data inválida")
    assert relatorio.erros[1].startswith("Linha 4: tipo inválido")
    assert relatorio.erros[2].startswith("Linha 5: esperadas 5 colunas")


def test_valor_com_fracao_de_centavo_vira_erro_em_vez_de_quebrar(repo, usuario):
    linhas = [CABECALHO, ["01/09/2026", "1.005", "despesa", "mercado", "x"], PAO]

    relatorio = importar_linhas(repo, usuario, linhas)

    assert relatorio.importadas == 1
    assert relatorio.erros == ["Linha 2: valor com mais de 2 casas decimais '1.005'."]


def test_reimportar_o_mesmo_arquivo_nao_duplica(repo, usuario):
    linhas = [CABECALHO, PAO, CAFE]
    importar_linhas(repo, usuario, linhas)

    relatorio = importar_linhas(repo, usuario, linhas)

    assert relatorio.importadas == 0
    assert relatorio.ignoradas == [2, 3]
    assert len(repo.listar(usuario)) == 2


def test_reimportacao_com_linha_nova_grava_so_a_nova(repo, usuario):
    importar_linhas(repo, usuario, [CABECALHO, PAO])

    relatorio = importar_linhas(repo, usuario, [CABECALHO, PAO, CAFE])

    assert relatorio.importadas == 1
    assert relatorio.ignoradas == [2]
    assert len(repo.listar(usuario)) == 2


def test_lancamentos_iguais_no_mesmo_arquivo_sao_todos_gravados(repo, usuario):
    # Dois cafés iguais no mesmo dia são dois gastos de verdade.
    relatorio = importar_linhas(repo, usuario, [CABECALHO, CAFE, CAFE])

    assert relatorio.importadas == 2
    assert len(repo.listar(usuario)) == 2


def test_reimportacao_compara_por_contagem(repo, usuario):
    importar_linhas(repo, usuario, [CABECALHO, CAFE])

    relatorio = importar_linhas(repo, usuario, [CABECALHO, CAFE, CAFE])

    assert relatorio.importadas == 1
    assert relatorio.ignoradas == [2]
    assert len(repo.listar(usuario)) == 2


def test_lancamento_de_outro_usuario_nao_conta_como_repetido(repo, usuario):
    bia = repo.criar_usuario("Bia")
    importar_linhas(repo, bia, [CABECALHO, PAO])

    relatorio = importar_linhas(repo, usuario, [CABECALHO, PAO])

    assert relatorio.importadas == 1


def test_reimportar_csv_de_vendas_nao_duplica(repo, usuario, tmp_path):
    arquivo = tmp_path / "vendas.csv"
    arquivo.write_text(
        "data da venda, produto, categoria, quantidade vendida, preco unitario\n"
        "2026-09-05, Bolo de cenoura, Bolos, 4, 45.00\n"
        "2026-09-12, Brigadeiro, Doces, 100, 2.50\n",
        encoding="utf-8",
    )

    primeira = importar_csv(repo, usuario, arquivo)
    segunda = importar_csv(repo, usuario, arquivo)

    assert (primeira.importadas, segunda.importadas) == (2, 0)
    assert segunda.ignoradas == [2, 3]
    valores = [lanc.valor for lanc in repo.listar(usuario)]
    assert valores == [Decimal("180.00"), Decimal("250.00")]


def test_cabecalho_desconhecido_impede_a_importacao(repo, usuario):
    with pytest.raises(ErroLeitura, match="cabeçalho"):
        importar_linhas(repo, usuario, [["nome", "idade"], ["Ana", "30"]])

    assert repo.listar(usuario) == []


def test_texto_do_relatorio(repo, usuario):
    importar_linhas(repo, usuario, [CABECALHO, PAO])
    linhas = [CABECALHO, PAO, ["x", "1", "despesa", "a", "b"], CAFE]

    texto = importar_linhas(repo, usuario, linhas).texto()

    assert texto == (
        "Linhas importadas: 1\n"
        "Linhas ignoradas (já estavam no banco): 1\n"
        "  2\n"
        "Linhas com erro: 1\n"
        "  Linha 3: data inválida 'x'. Use o formato DD/MM/AAAA."
    )
