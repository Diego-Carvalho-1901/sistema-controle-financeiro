"""Comandos de consulta e correção: /resumo, /desfazer e /meta.

Como em conversa.py, são funções comuns que devolvem o texto da resposta.
"""

from datetime import date
from decimal import Decimal

from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.conversa import descrever, formatar_reais, obter_ou_criar_usuario
from financeiro.bot.frases import FraseNaoEntendida, converter_valor
from financeiro.periodos import mes_de, semana_de

# Quantas categorias aparecem em "Maiores gastos".
MAIORES_GASTOS = 3

USO_META = """Para definir uma meta mensal de gastos:
/meta mercado 500

Para ver as metas e quanto já foi gasto: /meta"""


def responder_resumo(
    api: ClienteAPI,
    telegram_id: int,
    nome: str,
    argumentos: list[str],
    hoje: date | None = None,
) -> str:
    """/resumo (mês atual) ou /resumo semana."""
    hoje = hoje or date.today()
    periodo = argumentos[0].lower() if argumentos else "mes"
    if periodo == "semana":
        inicio, fim = semana_de(hoje)
        titulo = "da semana"
    elif periodo in ("mes", "mês"):
        inicio, fim = mes_de(hoje)
        titulo = "do mês"
    else:
        return "Use /resumo para o mês ou /resumo semana."

    usuario = obter_ou_criar_usuario(api, telegram_id, nome)
    return montar_resumo(api, usuario["id"], titulo, inicio, fim)


def montar_resumo(
    api: ClienteAPI, usuario_id: int, titulo: str, inicio: date, fim: date
) -> str:
    """Texto do resumo de um período (usado também no resumo semanal)."""
    negocio = api.resumo(usuario_id, "negocio", inicio, fim)
    pessoal = api.resumo(usuario_id, "pessoal", inicio, fim)
    gastos = api.resumo(usuario_id, "categorias", inicio, fim)
    cabecalho = f"Resumo {titulo} ({inicio:%d/%m} a {fim:%d/%m})"

    faturamento = Decimal(negocio["faturamento"])
    custos = Decimal(negocio["custos"])
    saldo = Decimal(pessoal["saldo"])
    if not gastos and faturamento == custos == saldo == 0:
        return f"{cabecalho}\n\nNenhum lançamento nesse período."

    lucro = formatar_reais(Decimal(negocio["lucro"]))
    margem = Decimal(negocio["margem"])
    linhas = [
        cabecalho,
        "",
        "Negócio",
        f"Faturamento: {formatar_reais(faturamento)}",
        f"Custos: {formatar_reais(custos)}",
        f"Lucro: {lucro} (margem de {margem:.0f}%)",
        "",
        "Pessoal",
        f"Saldo: {formatar_reais(saldo)}",
    ]
    if gastos:
        linhas += ["", "Maiores gastos"]
        linhas += [
            f"• {item['categoria']}: {formatar_reais(Decimal(item['total']))}"
            for item in gastos[:MAIORES_GASTOS]
        ]
    return "\n".join(linhas)


def responder_desfazer(
    api: ClienteAPI, telegram_id: int, nome: str, hoje: date | None = None
) -> str:
    """/desfazer: apaga o último lançamento gravado."""
    usuario = obter_ou_criar_usuario(api, telegram_id, nome)
    apagado = api.excluir_ultimo_lancamento(usuario["id"])
    if apagado is None:
        return "Não há nenhum lançamento para desfazer."
    return f"Apaguei: {descrever(apagado, hoje)}."


def responder_meta(
    api: ClienteAPI,
    telegram_id: int,
    nome: str,
    argumentos: list[str],
    hoje: date | None = None,
) -> str:
    """/meta (lista) ou /meta categoria valor (define)."""
    hoje = hoje or date.today()
    usuario = obter_ou_criar_usuario(api, telegram_id, nome)
    if not argumentos:
        return _listar_metas(api.listar_metas(usuario["id"], hoje))
    if len(argumentos) < 2:
        return USO_META

    categoria = " ".join(argumentos[:-1]).lower()
    try:
        valor = converter_valor(argumentos[-1])
    except FraseNaoEntendida:
        return USO_META
    if valor <= 0 or len(categoria) > 50:
        return USO_META

    metas = api.definir_meta(usuario["id"], categoria, valor)
    return f"Meta de {categoria} definida: {formatar_reais(valor)} por mês.\n\n" + (
        _listar_metas(metas)
    )


def _listar_metas(metas: list[dict]) -> str:
    if not metas:
        return "Você ainda não tem metas.\n\n" + USO_META
    linhas = ["Metas do mês"]
    for meta in metas:
        gasto = formatar_reais(Decimal(meta["gasto"]))
        limite = formatar_reais(Decimal(meta["meta"]))
        percentual = Decimal(meta["percentual"])
        linhas.append(f"• {meta['categoria']}: {gasto} de {limite} ({percentual:.0f}%)")
    return "\n".join(linhas)
