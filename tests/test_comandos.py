"""Testes dos comandos /resumo, /desfazer e /meta, sem o Telegram."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from financeiro.api.app import criar_app
from financeiro.bot import comandos
from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.conversa import responder_frase

TELEGRAM_ID = 777
HOJE = date(2026, 11, 26)  # quinta-feira; a semana vai de 23/11 a 29/11


@pytest.fixture
def api(engine):
    with TestClient(criar_app(engine)) as http:
        yield ClienteAPI(http)


def anotar(api, frase: str, dia: date = HOJE) -> None:
    resposta = responder_frase(api, TELEGRAM_ID, "Ana", frase, hoje=dia)
    assert resposta.startswith("Anotado"), resposta


def resumo(api, *argumentos: str) -> str:
    return comandos.responder_resumo(
        api, TELEGRAM_ID, "Ana", list(argumentos), hoje=HOJE
    )


def meta(api, *argumentos: str) -> str:
    return comandos.responder_meta(api, TELEGRAM_ID, "Ana", list(argumentos), HOJE)


# --- /resumo ---


RESUMO_ESPERADO = """Resumo do mês (01/11 a 30/11)

Negócio
Faturamento: R$ 90,00
Custos: R$ 30,00
Lucro: R$ 60,00 (margem de 67%)

Pessoal
Saldo: R$ 1.550,00

Maiores gastos
• mercado: R$ 200,00
• transporte: R$ 50,00
• insumos: R$ 30,00"""


def test_resumo_do_mes(api):
    anotar(api, "vendi 3 bolos 90")
    anotar(api, "gastei 30 farinha negócio")
    anotar(api, "recebi 1800 salário")
    anotar(api, "gastei 200 mercado")
    anotar(api, "gastei 50 uber", dia=date(2026, 11, 2))
    anotar(api, "gastei 999 mercado", dia=date(2026, 10, 31))  # outro mês

    assert resumo(api) == RESUMO_ESPERADO


def test_resumo_da_semana_ignora_o_resto_do_mes(api):
    anotar(api, "gastei 40 almoço", dia=date(2026, 11, 23))
    anotar(api, "gastei 50 uber", dia=date(2026, 11, 2))

    texto = resumo(api, "semana")

    assert texto.startswith("Resumo da semana (23/11 a 29/11)")
    assert "Saldo: R$ -40,00" in texto
    assert "uber" not in texto


def test_resumo_sem_lancamentos(api):
    assert resumo(api) == (
        "Resumo do mês (01/11 a 30/11)\n\nNenhum lançamento nesse período."
    )


def test_resumo_com_periodo_desconhecido_explica_o_uso(api):
    assert resumo(api, "ano") == "Use /resumo para o mês ou /resumo semana."


# --- /desfazer ---


def test_desfazer_apaga_o_ultimo_lancamento(api):
    anotar(api, "gastei 30 almoço")
    anotar(api, "vendi 2 bolos 60", dia=date(2026, 11, 20))

    resposta = comandos.responder_desfazer(api, TELEGRAM_ID, "Ana", hoje=HOJE)

    assert resposta == "Apaguei: venda de 2 × bolos, R$ 60,00 (negócio) em 20/11."
    assert "Lucro: R$ 0,00" in resumo(api)


def test_desfazer_sem_nada_para_apagar(api):
    resposta = comandos.responder_desfazer(api, TELEGRAM_ID, "Ana")

    assert resposta == "Não há nenhum lançamento para desfazer."


# --- /meta ---


def test_define_meta_e_mostra_o_quanto_ja_foi_gasto(api):
    anotar(api, "gastei 120 mercado")

    resposta = meta(api, "Mercado", "500")

    assert resposta == (
        "Meta de mercado definida: R$ 500,00 por mês.\n\n"
        "Metas do mês\n"
        "• mercado: R$ 120,00 de R$ 500,00 (24%)"
    )


def test_meta_aceita_valor_com_virgula_e_categoria_com_espacos(api):
    resposta = meta(api, "conta", "de", "luz", "150,50")

    assert resposta.startswith("Meta de conta de luz definida: R$ 150,50")


def test_meta_sem_argumentos_lista_as_metas(api):
    meta(api, "lazer", "100")

    assert meta(api) == "Metas do mês\n• lazer: R$ 0,00 de R$ 100,00 (0%)"


def test_meta_sem_metas_explica_como_criar(api):
    assert meta(api).startswith("Você ainda não tem metas.")


@pytest.mark.parametrize(
    "argumentos", [["mercado"], ["500"], ["mercado", "abc"], ["mercado", "0"]]
)
def test_meta_com_argumentos_errados_explica_o_uso(api, argumentos):
    assert meta(api, *argumentos) == comandos.USO_META


# --- Categorização e /corrigir (issue [15]) ---


def test_frase_ja_vem_com_a_categoria_sugerida(api):
    resposta = responder_frase(api, TELEGRAM_ID, "Ana", "gastei 80 posto", HOJE)

    assert resposta == (
        "Anotado: gasto com posto [transporte], R$ 80,00 (pessoal). "
        "Errou? Use /desfazer ou /corrigir <categoria>."
    )


def test_sem_sugestao_fica_a_primeira_palavra(api):
    anotar(api, "gastei 50 presente da Bia")

    assert "• presente: R$ 50,00" in resumo(api)


def test_corrigir_troca_a_categoria_e_aprende_para_a_proxima(api):
    anotar(api, "gastei 80 posto")

    resposta = comandos.responder_corrigir(
        api, TELEGRAM_ID, "Ana", ["Entregas"], hoje=HOJE
    )
    proxima = responder_frase(api, TELEGRAM_ID, "Ana", "gastei 60 posto", HOJE)

    assert resposta == (
        "Corrigido: gasto com posto [entregas], R$ 80,00 (pessoal).\n"
        'Aprendi: "posto" agora é entregas.'
    )
    assert "[entregas]" in proxima
    assert "• entregas: R$ 140,00" in resumo(api)


def test_corrigir_sem_lancamentos(api):
    resposta = comandos.responder_corrigir(api, TELEGRAM_ID, "Ana", ["lazer"])

    assert resposta == "Não há nenhum lançamento para corrigir."


def test_corrigir_sem_categoria_explica_o_uso(api):
    assert comandos.responder_corrigir(api, TELEGRAM_ID, "Ana", []) == (
        comandos.USO_CORRIGIR
    )
