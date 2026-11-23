"""Testes de metas e do "desfazer" no repositório."""

from datetime import date
from decimal import Decimal

import pytest

from financeiro.banco.conexao import criar_fabrica_de_sessoes
from financeiro.banco.metas import SituacaoMeta, metas_com_gasto
from financeiro.banco.repositorio import RepositorioLancamentos
from financeiro.modelos import Lancamento

NOVEMBRO = (date(2026, 11, 1), date(2026, 11, 30))


def despesa(dia: str, valor: str, categoria: str) -> Lancamento:
    return Lancamento(
        date.fromisoformat(dia), Decimal(valor), "despesa", categoria, "x"
    )


@pytest.fixture
def repo(engine):
    with criar_fabrica_de_sessoes(engine)() as sessao:
        yield RepositorioLancamentos(sessao)


@pytest.fixture
def ana(repo) -> int:
    return repo.criar_usuario("Ana")


def test_meta_mostra_o_gasto_do_periodo(repo, ana):
    repo.definir_meta(ana, "mercado", Decimal(500))
    repo.adicionar(ana, despesa("2026-11-02", "120", "mercado"))
    repo.adicionar(ana, despesa("2026-11-20", "280", "mercado"))
    repo.adicionar(ana, despesa("2026-10-31", "999", "mercado"))  # fora do mês

    [situacao] = metas_com_gasto(repo.sessao, ana, *NOVEMBRO)

    assert situacao == SituacaoMeta("mercado", Decimal(500), Decimal(400))
    assert situacao.percentual == 80


def test_meta_sem_gasto_aparece_com_zero(repo, ana):
    repo.definir_meta(ana, "lazer", Decimal(100))

    assert metas_com_gasto(repo.sessao, ana, *NOVEMBRO) == [
        SituacaoMeta("lazer", Decimal(100), Decimal(0))
    ]


def test_definir_de_novo_troca_o_valor(repo, ana):
    repo.definir_meta(ana, "mercado", Decimal(500))
    repo.definir_meta(ana, "mercado", Decimal("650.50"))

    [situacao] = metas_com_gasto(repo.sessao, ana, *NOVEMBRO)
    assert situacao.meta == Decimal("650.50")


def test_metas_sao_de_cada_usuario(repo, ana):
    bia = repo.criar_usuario("Bia")
    repo.definir_meta(ana, "mercado", Decimal(500))
    repo.definir_meta(bia, "mercado", Decimal(300))
    repo.adicionar(bia, despesa("2026-11-02", "50", "mercado"))

    [da_ana] = metas_com_gasto(repo.sessao, ana, *NOVEMBRO)
    assert (da_ana.meta, da_ana.gasto) == (Decimal(500), Decimal(0))


def test_excluir_ultimo_apaga_o_gravado_por_ultimo(repo, ana):
    repo.adicionar(ana, despesa("2026-11-20", "10", "mercado"))
    id_ultimo = repo.adicionar(ana, despesa("2026-11-01", "20", "lazer"))

    apagado = repo.excluir_ultimo(ana)

    assert apagado == (id_ultimo, despesa("2026-11-01", "20", "lazer"))
    assert [lanc.valor for lanc in repo.listar(ana)] == [Decimal(10)]


def test_excluir_ultimo_sem_lancamentos_devolve_none(repo, ana):
    assert repo.excluir_ultimo(ana) is None


def test_excluir_ultimo_nao_mexe_em_outro_usuario(repo, ana):
    bia = repo.criar_usuario("Bia")
    repo.adicionar(ana, despesa("2026-11-01", "10", "mercado"))
    repo.adicionar(bia, despesa("2026-11-01", "20", "mercado"))

    repo.excluir_ultimo(ana)

    assert repo.listar(ana) == []
    assert len(repo.listar(bia)) == 1
