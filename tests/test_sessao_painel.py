"""Testes dos tokens assinados do painel."""

import pytest

from financeiro.painel.sessao import LINK, SESSAO, criar_token, ler_token

SEGREDO = "segredo-de-teste"
AGORA = 1_800_000_000.0


def test_token_valido_devolve_o_usuario():
    token = criar_token(SEGREDO, 42, LINK, agora=AGORA)

    assert ler_token(SEGREDO, token, LINK, agora=AGORA + 60) == 42


def test_link_vence_em_10_minutos_e_sessao_em_7_dias():
    link = criar_token(SEGREDO, 42, LINK, agora=AGORA)
    sessao = criar_token(SEGREDO, 42, SESSAO, agora=AGORA)

    assert ler_token(SEGREDO, link, LINK, agora=AGORA + 601) is None
    assert ler_token(SEGREDO, sessao, SESSAO, agora=AGORA + 6 * 86400) == 42
    assert ler_token(SEGREDO, sessao, SESSAO, agora=AGORA + 8 * 86400) is None


def test_token_de_um_proposito_nao_serve_para_outro():
    link = criar_token(SEGREDO, 42, LINK, agora=AGORA)

    assert ler_token(SEGREDO, link, SESSAO, agora=AGORA) is None


def test_outro_segredo_nao_valida():
    token = criar_token(SEGREDO, 42, LINK, agora=AGORA)

    assert ler_token("outro", token, LINK, agora=AGORA) is None


def test_trocar_o_usuario_invalida_a_assinatura():
    token = criar_token(SEGREDO, 42, LINK, agora=AGORA)
    _dados, assinatura = token.split(".")
    falso = criar_token(SEGREDO, 1, LINK, agora=AGORA).split(".")[0]

    assert ler_token(SEGREDO, f"{falso}.{assinatura}", LINK, agora=AGORA) is None


@pytest.mark.parametrize("lixo", ["", "abc", "a.b.c", "....", "@@@.123"])
def test_lixo_nao_quebra(lixo):
    assert ler_token(SEGREDO, lixo, LINK) is None
