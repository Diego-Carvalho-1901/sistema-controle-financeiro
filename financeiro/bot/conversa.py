"""O que o bot responde a cada comando.

São funções comuns: recebem o cliente da API e os dados da mensagem e
devolvem o texto da resposta. Não sabem que o Telegram existe, então os
testes chamam essas funções direto.
"""

from dataclasses import replace
from datetime import date
from decimal import Decimal

from financeiro.bot.cliente_api import ClienteAPI
from financeiro.bot.frases import FraseNaoEntendida, interpretar

EXEMPLOS = """Escreva do seu jeito, por exemplo:
• vendi 3 bolos 45
• gastei 30 almoço
• paguei 120,50 conta de luz da loja
• recebi 1800 salário"""

AJUDA = f"""Eu anoto as finanças do seu negócio e as pessoais, separadas.

{EXEMPLOS}

Vendas vão para a conta do negócio. Gastos e recebimentos vão para a
pessoal, a não ser que você diga "negócio", "loja" ou "empresa".

Comandos:
/resumo - resumo do mês (ou /resumo semana)
/desfazer - apaga o último lançamento
/meta mercado 500 - define a meta mensal de gastos de uma categoria
/meta - mostra as metas e quanto já foi gasto
/corrigir transporte - troca a categoria do último lançamento e aprende
/start - cadastra você (ou confirma o cadastro)
/ajuda - mostra esta mensagem"""


def obter_ou_criar_usuario(api: ClienteAPI, telegram_id: int, nome: str) -> dict:
    """Devolve o usuário dessa conta do Telegram, cadastrando se for novo."""
    usuario = api.buscar_usuario_do_telegram(telegram_id)
    if usuario is None:
        usuario = api.criar_usuario(nome or "Sem nome", telegram_id)
    return usuario


def responder_start(api: ClienteAPI, telegram_id: int, nome: str) -> str:
    """Cadastra a pessoa na primeira vez e explica como usar o bot."""
    usuario = api.buscar_usuario_do_telegram(telegram_id)
    if usuario is None:
        usuario = api.criar_usuario(nome or "Sem nome", telegram_id)
        saudacao = f"Olá, {usuario['nome']}! Seu cadastro está feito."
    else:
        saudacao = f"Olá de novo, {usuario['nome']}! Você já está cadastrado."
    return f"{saudacao}\n\n{AJUDA}"


def responder_ajuda() -> str:
    """Lista os comandos disponíveis."""
    return AJUDA


def responder_frase(
    api: ClienteAPI,
    telegram_id: int,
    nome: str,
    frase: str,
    hoje: date | None = None,
) -> str:
    """Anota o lançamento descrito na frase, ou pede para reescrever."""
    try:
        lido = interpretar(frase, hoje)
    except FraseNaoEntendida as erro:
        return f"Não entendi: {erro}.\n\n{EXEMPLOS}"
    usuario = obter_ou_criar_usuario(api, telegram_id, nome)
    if lido.tipo != "venda":
        # Em vendas a categoria é o produto; nos outros casos, a API sugere
        # uma pelas palavras-chave (issue [15]).
        sugerida = api.sugerir_categoria(usuario["id"], lido.descricao)
        if sugerida:
            lido = replace(lido, categoria=sugerida)
    criado = api.criar_lancamento(usuario["id"], lido.para_json())
    dica = "Errou? Use /desfazer"
    if lido.tipo != "venda":
        dica += " ou /corrigir <categoria>"
    return f"Anotado: {descrever(criado, hoje)}. {dica}."


def descrever(lancamento: dict, hoje: date | None = None) -> str:
    """Resumo de um lançamento (no formato JSON da API) em uma linha."""
    conta = "negócio" if lancamento["conta"] == "negocio" else "pessoal"
    if lancamento["tipo"] == "venda":
        o_que = f"venda de {lancamento['quantidade']} × {lancamento['produto']}"
    elif lancamento["tipo"] == "despesa":
        o_que = f"gasto com {lancamento['descricao']} [{lancamento['categoria']}]"
    else:
        o_que = f"recebimento de {lancamento['descricao']} [{lancamento['categoria']}]"
    data = date.fromisoformat(lancamento["data"])
    quando = "" if data == (hoje or date.today()) else f" em {data:%d/%m}"
    valor = formatar_reais(Decimal(lancamento["valor"]))
    return f"{o_que}, {valor} ({conta}){quando}"


def formatar_reais(valor: Decimal) -> str:
    """Decimal('1800.5') -> 'R$ 1.800,50' (formato brasileiro)."""
    texto = f"{valor:,.2f}"  # '1,800.50' no formato americano
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")
