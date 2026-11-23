"""Categorização automática por palavras-chave (issue [15]).

Funções puras: recebem a descrição de um lançamento e as regras que o
usuário já ensinou, e sugerem uma categoria. Quem grava e lê as regras é o
repositório; quem chama isto é a API.
"""

import re
import unicodedata

# Dicionário inicial: palavra (sem acento, minúscula) -> categoria.
PALAVRAS_PADRAO: dict[str, str] = {
    # transporte
    "posto": "transporte",
    "gasolina": "transporte",
    "combustivel": "transporte",
    "etanol": "transporte",
    "uber": "transporte",
    "99": "transporte",
    "taxi": "transporte",
    "onibus": "transporte",
    "metro": "transporte",
    "estacionamento": "transporte",
    "pedagio": "transporte",
    # mercado
    "mercado": "mercado",
    "supermercado": "mercado",
    "feira": "mercado",
    "padaria": "mercado",
    "pao": "mercado",
    "acougue": "mercado",
    # alimentação fora de casa
    "almoco": "alimentacao",
    "jantar": "alimentacao",
    "lanche": "alimentacao",
    "cafe": "alimentacao",
    "restaurante": "alimentacao",
    "ifood": "alimentacao",
    "pizza": "alimentacao",
    # moradia e contas da casa
    "aluguel": "moradia",
    "condominio": "moradia",
    "luz": "contas",
    "energia": "contas",
    "agua": "contas",
    "internet": "contas",
    "celular": "contas",
    "telefone": "contas",
    "gas": "contas",
    # saúde
    "farmacia": "saude",
    "remedio": "saude",
    "consulta": "saude",
    "dentista": "saude",
    "plano": "saude",
    # lazer
    "cinema": "lazer",
    "netflix": "lazer",
    "spotify": "lazer",
    "show": "lazer",
    "bar": "lazer",
    # negócio
    "farinha": "insumos",
    "acucar": "insumos",
    "ovos": "insumos",
    "leite": "insumos",
    "embalagem": "embalagens",
    "embalagens": "embalagens",
    "caixa": "embalagens",
    "das": "impostos",
    "imposto": "impostos",
    "anuncio": "marketing",
    "instagram": "marketing",
    # entradas
    "salario": "salario",
    "freela": "servicos",
    "servico": "servicos",
    "pix": "transferencias",
}


# Palavras que nunca viram regra, mesmo com 3 letras ou mais.
NAO_APRENDER = {
    "pra", "pro", "para", "com", "dos", "das", "nas", "nos", "uma", "uns",
    "que", "ate", "por", "pelo", "pela", "sem", "meu", "minha", "seu", "sua",
}  # fmt: skip


def normalizar(palavra: str) -> str:
    """'Almoço' -> 'almoco' (minúsculas e sem acento)."""
    decomposta = unicodedata.normalize("NFD", palavra.lower())
    return "".join(c for c in decomposta if unicodedata.category(c) != "Mn")


def palavras_chave(descricao: str) -> list[str]:
    """Palavras da descrição, normalizadas e sem repetição, na ordem."""
    palavras = re.findall(r"\w+", normalizar(descricao))
    return list(dict.fromkeys(palavras))


def sugerir_categoria(descricao: str, regras_do_usuario: dict[str, str]) -> str | None:
    """Sugere a categoria a partir das palavras da descrição.

    As regras que o usuário ensinou vêm primeiro (vencem o dicionário
    padrão). Dentro de cada fonte, vale a primeira palavra que casar.
    Devolve None quando nenhuma palavra é conhecida.
    """
    palavras = palavras_chave(descricao)
    for regras in (regras_do_usuario, PALAVRAS_PADRAO):
        for palavra in palavras:
            if palavra in regras:
                return regras[palavra]
    return None


def palavra_para_aprender(descricao: str) -> str | None:
    """Qual palavra da descrição vira regra quando o usuário corrige.

    Usa a primeira palavra com pelo menos 3 letras que não seja de ligação,
    para não aprender regras com "de", "pra"...
    """
    for palavra in palavras_chave(descricao):
        if len(palavra) >= 3 and not palavra.isdigit() and palavra not in NAO_APRENDER:
            return palavra
    return None
