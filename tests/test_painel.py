"""Testes do painel: login pelo link, cookie de sessão e dados."""

from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from financeiro.api.app import criar_app
from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.comandos import responder_painel
from financeiro.painel import link
from financeiro.painel.rotas import COOKIE
from financeiro.painel.sessao import LINK, SESSAO, criar_token

SEGREDO = "segredo-de-teste"
CHAVE = "chave"


@pytest.fixture
def cliente(engine):
    app = criar_app(engine, chave_api=CHAVE, segredo=SEGREDO)
    with TestClient(app, headers={"X-API-Key": CHAVE}) as cliente:
        yield cliente


@pytest.fixture
def ana(cliente) -> int:
    ana = cliente.post("/usuarios", json={"nome": "Ana"}).json()["id"]
    venda = {"tipo": "venda", "conta": "negocio", "produto": "Bolo", "quantidade": 1}
    for dados in [
        {"data": "2026-10-05", "valor": "300", "categoria": "bolos", **venda},
        {"data": "2026-11-05", "valor": "500", "categoria": "bolos", **venda},
        {"data": "2026-11-06", "valor": "120", "tipo": "despesa",
         "categoria": "insumos", "conta": "negocio"},
        {"data": "2026-11-07", "valor": "80", "tipo": "despesa", "categoria": "mercado"},
        {"data": "2026-11-08", "valor": "1000", "tipo": "receita", "categoria": "salario"},
    ]:  # fmt: skip
        assert cliente.post(f"/usuarios/{ana}/lancamentos", json=dados).is_success
    return ana


def entrar(cliente, usuario_id: int) -> None:
    """Faz o caminho completo: link pelo bot -> abrir no navegador."""
    link = cliente.post(f"/usuarios/{usuario_id}/painel/link").json()["url"]
    url = urlparse(link)
    resposta = cliente.get(f"{url.path}?{url.query}", follow_redirects=False)
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/painel/"


def test_link_exige_a_chave_da_api(engine, ana):
    with TestClient(criar_app(engine, chave_api=CHAVE, segredo=SEGREDO)) as sem_chave:
        assert sem_chave.post(f"/usuarios/{ana}/painel/link").status_code == 401


def test_link_cria_cookie_de_sessao_protegido(cliente, ana):
    entrar(cliente, ana)

    cookie = next(c for c in cliente.cookies.jar if c.name == COOKIE)
    assert cookie.has_nonstandard_attr("HttpOnly")
    assert cliente.get("/painel/api/eu").json() == {"nome": "Ana"}


@pytest.mark.parametrize(
    "token",
    [
        "lixo",
        criar_token("outro-segredo", 1, LINK),
        criar_token(SEGREDO, 1, SESSAO),  # cookie não serve como link
        criar_token(SEGREDO, 1, LINK, agora=0),  # vencido
    ],
)
def test_link_invalido_nao_loga(cliente, ana, token):
    resposta = cliente.get("/painel/entrar", params={"token": token})

    assert resposta.status_code == 401
    assert "Link inválido ou vencido" in resposta.text
    assert cliente.get("/painel/api/eu").status_code == 401


@pytest.mark.parametrize(
    "rota", ["/painel/api/eu", "/painel/api/mes", "/painel/api/lucro"]
)
def test_dados_exigem_login(cliente, rota):
    assert cliente.get(rota).status_code == 401


def test_dados_do_mes(cliente, ana):
    entrar(cliente, ana)

    dados = cliente.get("/painel/api/mes", params={"dia": "2026-11-15"}).json()

    assert dados == {
        "inicio": "2026-11-01",
        "fim": "2026-11-30",
        "negocio": {
            "faturamento": "500.00",
            "custos": "120.00",
            "lucro": "380.00",
            "margem": "76.00",
        },
        "saldo_pessoal": "920.00",
        "gastos_por_categoria": [
            {"categoria": "insumos", "total": "120.00"},
            {"categoria": "mercado", "total": "80.00"},
        ],
    }


def test_evolucao_do_lucro(cliente, ana):
    entrar(cliente, ana)

    pontos = cliente.get(
        "/painel/api/lucro", params={"ate": "2026-11-30", "meses": 12}
    ).json()

    assert len(pontos) == 12  # um ponto por mês, de dez/2025 a nov/2026
    assert (pontos[0]["ano"], pontos[0]["mes"], pontos[0]["lucro"]) == (
        2025,
        12,
        "0.00",
    )
    assert [(p["mes"], p["lucro"]) for p in pontos[-2:]] == [
        (10, "300.00"),
        (11, "380.00"),
    ]


def test_janela_de_meses_respeita_o_limite(cliente, ana):
    entrar(cliente, ana)

    so_novembro = cliente.get(
        "/painel/api/lucro", params={"ate": "2026-11-30", "meses": 1}
    ).json()

    assert [p["mes"] for p in so_novembro] == [11]
    assert cliente.get("/painel/api/lucro", params={"meses": 0}).status_code == 422


def test_cada_um_ve_so_os_proprios_dados(cliente, ana):
    bia = cliente.post("/usuarios", json={"nome": "Bia"}).json()["id"]
    entrar(cliente, bia)

    dados = cliente.get("/painel/api/mes", params={"dia": "2026-11-15"}).json()

    assert cliente.get("/painel/api/eu").json() == {"nome": "Bia"}
    assert dados["negocio"]["faturamento"] == "0.00"


def test_sair_apaga_a_sessao(cliente, ana):
    entrar(cliente, ana)

    cliente.post("/painel/sair")

    assert cliente.get("/painel/api/eu").status_code == 401


def test_pagina_e_arquivos_estaticos(cliente):
    assert "Painel financeiro" in cliente.get("/painel/").text
    assert cliente.get("/painel/estatico/painel.js").status_code == 200


# --- Bot e linha de comando ---


def test_comando_painel_do_bot_manda_um_link_que_funciona(cliente):
    resposta = responder_painel(ClienteAPI(cliente), 555, "Ana")

    link = next(linha for linha in resposta.splitlines() if "/painel/entrar" in linha)
    url = urlparse(link)
    cliente.get(f"{url.path}?{url.query}")
    assert cliente.get("/painel/api/eu").json() == {"nome": "Ana"}


def test_link_pela_linha_de_comando(url_banco, engine, monkeypatch, capsys, cliente):
    monkeypatch.setenv("FINANCEIRO_SEGREDO", SEGREDO)
    monkeypatch.setenv("FINANCEIRO_DB_URL", url_banco)

    assert link.main(["--usuario", "Caio"]) == 0

    url = urlparse(capsys.readouterr().out.strip())
    cliente.get(f"{url.path}?{url.query}")
    assert cliente.get("/painel/api/eu").json() == {"nome": "Caio"}
