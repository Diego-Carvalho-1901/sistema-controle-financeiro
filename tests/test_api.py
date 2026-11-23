"""Testes da API com o TestClient do FastAPI e um banco SQLite temporário."""

from typing import get_args

import pytest
from fastapi.testclient import TestClient

from financeiro.api.app import criar_app
from financeiro.api.esquemas import Conta, Tipo
from financeiro.banco.conexao import criar_engine
from financeiro.banco.tabelas import Base
from financeiro.modelos import CONTAS, TIPOS


@pytest.fixture
def cliente(tmp_path):
    """Cliente HTTP falando com uma API ligada a um banco novo e vazio."""
    engine = criar_engine(f"sqlite:///{tmp_path / 'teste.db'}")
    Base.metadata.create_all(engine)
    with TestClient(criar_app(engine)) as cliente:
        yield cliente
    engine.dispose()


@pytest.fixture
def usuario(cliente) -> int:
    resposta = cliente.post("/usuarios", json={"nome": "Ana"})
    assert resposta.status_code == 201
    return resposta.json()["id"]


def url(usuario_id: int, lancamento_id: int | None = None) -> str:
    base = f"/usuarios/{usuario_id}/lancamentos"
    return base if lancamento_id is None else f"{base}/{lancamento_id}"


def despesa(**mudancas) -> dict:
    dados = {
        "data": "2026-09-01",
        "valor": "30.00",
        "tipo": "despesa",
        "categoria": "mercado",
        "descricao": "feira",
    }
    return dados | mudancas


def criar(cliente, usuario_id: int, dados: dict) -> dict:
    resposta = cliente.post(url(usuario_id), json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_esquemas_aceitam_os_mesmos_tipos_e_contas_do_modelo():
    assert get_args(Tipo) == TIPOS
    assert get_args(Conta) == CONTAS


def test_cria_e_devolve_o_lancamento_com_id(cliente, usuario):
    criado = criar(cliente, usuario, despesa(valor=45.9))

    assert criado["id"] > 0
    assert criado["valor"] == "45.90"  # dinheiro sai como texto, sem float
    assert criado["conta"] == "pessoal"  # valor padrão
    assert cliente.get(url(usuario, criado["id"])).json() == criado


def test_cria_venda_com_produto_e_quantidade(cliente, usuario):
    venda = despesa(
        tipo="venda", conta="negocio", produto="Bolo de cenoura", quantidade=3
    )

    criado = criar(cliente, usuario, venda)

    assert (criado["produto"], criado["quantidade"]) == ("Bolo de cenoura", 3)


@pytest.mark.parametrize(
    ("mudancas", "campo"),
    [
        ({"valor": "-5"}, "valor"),
        ({"valor": "1.005"}, "valor"),
        ({"tipo": "doacao"}, "tipo"),
        ({"conta": "empresa"}, "conta"),
        ({"data": "31/09/2026"}, "data"),
        ({"categoria": ""}, "categoria"),
    ],
)
def test_recusa_campo_invalido_com_422(cliente, usuario, mudancas, campo):
    resposta = cliente.post(url(usuario), json=despesa(**mudancas))

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"][-1] == campo


def test_aplica_as_regras_do_modelo_lancamento(cliente, usuario):
    venda_pessoal = despesa(tipo="venda", produto="Bolo", quantidade=1)

    resposta = cliente.post(url(usuario), json=venda_pessoal)

    assert resposta.status_code == 422
    assert "conta 'negocio'" in resposta.json()["detail"][0]["msg"]


def test_lista_em_ordem_de_data_com_filtros(cliente, usuario):
    criar(cliente, usuario, despesa(data="2026-09-20", categoria="mercado"))
    criar(cliente, usuario, despesa(data="2026-09-05", categoria="aluguel"))
    criar(
        cliente,
        usuario,
        despesa(data="2026-10-02", categoria="mercado", conta="negocio"),
    )

    def datas(**filtros) -> list[str]:
        resposta = cliente.get(url(usuario), params=filtros)
        assert resposta.status_code == 200
        return [lanc["data"] for lanc in resposta.json()]

    assert datas() == ["2026-09-05", "2026-09-20", "2026-10-02"]
    assert datas(inicio="2026-09-10", fim="2026-09-30") == ["2026-09-20"]
    assert datas(categoria="mercado") == ["2026-09-20", "2026-10-02"]
    assert datas(conta="negocio") == ["2026-10-02"]


def test_edita_substituindo_os_campos(cliente, usuario):
    criado = criar(cliente, usuario, despesa())

    resposta = cliente.put(
        url(usuario, criado["id"]), json=despesa(valor="12.50", categoria="feira")
    )

    assert resposta.status_code == 200
    lido = cliente.get(url(usuario, criado["id"])).json()
    assert (lido["valor"], lido["categoria"]) == ("12.50", "feira")


def test_exclui_e_depois_responde_404(cliente, usuario):
    criado = criar(cliente, usuario, despesa())

    assert cliente.delete(url(usuario, criado["id"])).status_code == 204
    assert cliente.get(url(usuario, criado["id"])).status_code == 404
    assert cliente.delete(url(usuario, criado["id"])).status_code == 404


def test_usuario_inexistente_responde_404(cliente):
    assert cliente.get(url(999)).status_code == 404
    assert cliente.post(url(999), json=despesa()).status_code == 404


def test_nao_ve_nem_altera_lancamento_de_outro_usuario(cliente, usuario):
    bia = cliente.post("/usuarios", json={"nome": "Bia"}).json()["id"]
    da_ana = criar(cliente, usuario, despesa())

    assert cliente.get(url(bia, da_ana["id"])).status_code == 404
    assert cliente.put(url(bia, da_ana["id"]), json=despesa()).status_code == 404
    assert cliente.delete(url(bia, da_ana["id"])).status_code == 404
    assert cliente.get(url(bia)).json() == []


def test_swagger_documenta_as_rotas(cliente):
    caminhos = cliente.get("/openapi.json").json()["paths"]

    assert "/usuarios/{usuario_id}/lancamentos" in caminhos
    assert cliente.get("/docs").status_code == 200


# --- Resumos (issue [10]) ---


def resumo(cliente, usuario_id: int, nome: str, **params):
    resposta = cliente.get(f"/usuarios/{usuario_id}/resumos/{nome}", params=params)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


@pytest.fixture
def com_dados(cliente, usuario) -> int:
    venda = {"tipo": "venda", "conta": "negocio", "produto": "Bolo", "quantidade": 2}
    for dados in [
        despesa(valor="100.00", tipo="receita", categoria="salario"),
        despesa(valor="30.00"),
        despesa(valor="12.50", data="2026-10-03"),
        despesa(valor="50.00", categoria="bolos", **venda),
        despesa(valor="20.00", categoria="insumos", conta="negocio"),
    ]:
        criar(cliente, usuario, dados)
    return usuario


def test_resumo_mensal(cliente, com_dados):
    assert resumo(cliente, com_dados, "mensal") == [
        {
            "ano": 2026,
            "mes": 9,
            "receitas": "100.00",
            "despesas": "50.00",
            "vendas": "50.00",
            "saldo": "100.00",
        },
        {
            "ano": 2026,
            "mes": 10,
            "receitas": "0.00",
            "despesas": "12.50",
            "vendas": "0.00",
            "saldo": "-12.50",
        },
    ]


def test_resumo_por_categoria_com_filtros(cliente, com_dados):
    todas = resumo(cliente, com_dados, "categorias")
    setembro_pessoal = resumo(
        cliente,
        com_dados,
        "categorias",
        conta="pessoal",
        inicio="2026-09-01",
        fim="2026-09-30",
    )

    assert todas == [
        {"categoria": "mercado", "total": "42.50"},
        {"categoria": "insumos", "total": "20.00"},
    ]
    assert setembro_pessoal == [{"categoria": "mercado", "total": "30.00"}]


def test_resumo_negocio_e_pessoal(cliente, com_dados):
    assert resumo(cliente, com_dados, "negocio") == {
        "faturamento": "50.00",
        "custos": "20.00",
        "lucro": "30.00",
        "margem": "60.00",
    }
    assert resumo(cliente, com_dados, "pessoal") == {"saldo": "57.50"}


def test_resumo_de_usuario_inexistente_da_404(cliente):
    assert cliente.get("/usuarios/999/resumos/negocio").status_code == 404


def test_resumo_recusa_periodo_invertido(cliente, usuario):
    params = {"inicio": "2026-10-01", "fim": "2026-09-01"}
    resposta = cliente.get(f"/usuarios/{usuario}/resumos/mensal", params=params)

    assert resposta.status_code == 422
