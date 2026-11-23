"""Leitor de frases livres: "vendi 3 bolos 45" vira um lançamento.

A ideia é simples e previsível, sem inteligência artificial:

1. Um verbo no começo diz o tipo ("vendi" -> venda, "gastei" -> despesa,
   "recebi" -> receita).
2. Os números da frase viram valor (e quantidade, nas vendas).
3. Palavras como "negócio" ou "pessoal" escolhem a conta.
4. O que sobra (tirando palavras de ligação) é a descrição.

Quando a frase é ambígua, o leitor não chuta: lança FraseNaoEntendida com
o motivo, e o bot pede para a pessoa escrever de outro jeito.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

# Verbo (sem acento, minúsculo) -> tipo do lançamento.
VERBOS = {
    "vendi": "venda",
    "vendemos": "venda",
    "vendido": "venda",
    "vendidos": "venda",
    "vendidas": "venda",
    "gastei": "despesa",
    "gasto": "despesa",
    "gastamos": "despesa",
    "paguei": "despesa",
    "pagamos": "despesa",
    "comprei": "despesa",
    "compramos": "despesa",
    "recebi": "receita",
    "recebemos": "receita",
    "ganhei": "receita",
    "entrou": "receita",
}

# Palavras que escolhem a conta (sem acento).
CONTA_NEGOCIO = {"negocio", "empresa", "loja", "trabalho", "mei"}
CONTA_PESSOAL = {"pessoal", "casa"}

# Palavras que nunca entram na descrição.
FORA_DA_DESCRICAO = {
    "reais", "real", "conto", "contos", "r$", "rs", "hoje", "ontem", "cada",
    "unidade", "un", "x", "eu",
}  # fmt: skip

# Palavras de ligação: saem só do começo e do fim da descrição, para
# "gastei 30 no almoço" virar "almoço", mas "conta de luz" continuar inteira.
LIGACAO = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "no",
    "na", "nos", "nas", "em", "com", "por", "pra", "pro", "para", "e", "que",
    "pelo", "pela", "pelos", "pelas", "foi", "foram", "total",
}  # fmt: skip

# Valor em dinheiro: "45", "45,90", "45.90", "1.800", "1.800,50", "R$45".
NUMERO = re.compile(
    r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
)

# "3x" ou "x3" colado ao número indica quantidade.
QUANTIDADE_X = re.compile(r"^(?:(\d+)x|x(\d+))$")

CENTAVO = Decimal("0.01")


class FraseNaoEntendida(ValueError):
    """A frase não tem informação suficiente ou é ambígua."""


@dataclass(frozen=True)
class Interpretacao:
    """O que o leitor entendeu da frase, pronto para virar um lançamento."""

    data: date
    tipo: str
    valor: Decimal
    conta: str
    categoria: str
    descricao: str
    produto: str | None = None
    quantidade: int | None = None

    def para_json(self) -> dict:
        """Formato aceito pela API em POST /usuarios/{id}/lancamentos."""
        return {
            "data": self.data.isoformat(),
            "valor": str(self.valor),
            "tipo": self.tipo,
            "categoria": self.categoria,
            "descricao": self.descricao,
            "conta": self.conta,
            "produto": self.produto,
            "quantidade": self.quantidade,
        }


def sem_acento(texto: str) -> str:
    """'Salário' -> 'salario' (usado só para comparar palavras)."""
    decomposto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def converter_valor(texto: str) -> Decimal:
    """Converte '1.800,50', '45,9' ou '45.90' em Decimal.

    Com vírgula, a vírgula é o decimal e os pontos separam milhares. Sem
    vírgula, um ponto seguido de 3 dígitos é milhar ("1.800") e seguido de
    1 ou 2 dígitos é decimal ("45.90").
    """
    texto = texto.lower().removeprefix("r$").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")
    try:
        return Decimal(texto)
    except InvalidOperation as erro:
        raise FraseNaoEntendida(f"não entendi o valor {texto!r}") from erro


def interpretar(frase: str, hoje: date | None = None) -> Interpretacao:
    """Transforma a frase num lançamento ou lança FraseNaoEntendida."""
    hoje = hoje or date.today()
    palavras = _separar_palavras(frase)
    if not palavras:
        raise FraseNaoEntendida("a mensagem está vazia")

    tipo = _encontrar_tipo(palavras)
    data = hoje - timedelta(days=1) if "ontem" in _chaves(palavras) else hoje
    conta = _encontrar_conta(palavras, tipo)
    numeros, quantidade_x, texto = _separar_numeros(palavras)
    descricao = " ".join(texto)

    if tipo == "venda":
        valor, quantidade = _valor_e_quantidade_da_venda(
            numeros, quantidade_x, unitario="cada" in _chaves(palavras)
        )
        if not descricao:
            raise FraseNaoEntendida("faltou dizer o que foi vendido")
        return Interpretacao(
            data=data,
            tipo=tipo,
            valor=_validar_valor(valor),
            conta="negocio",
            categoria=_categoria(texto),
            descricao=descricao,
            produto=descricao,
            quantidade=quantidade,
        )

    if quantidade_x is not None or len(numeros) != 1:
        raise FraseNaoEntendida(
            "não sei qual número é o valor" if numeros else "faltou o valor"
        )
    if not descricao:
        raise FraseNaoEntendida("faltou dizer com o que foi")
    return Interpretacao(
        data=data,
        tipo=tipo,
        valor=_validar_valor(numeros[0]),
        conta=conta,
        categoria=_categoria(texto),
        descricao=descricao,
    )


# --- etapas ---


def _separar_palavras(frase: str) -> list[str]:
    # Junta "R$ 45" em "R$45" e separa pontuação solta do fim das palavras.
    frase = re.sub(r"r\$\s+", "r$", frase.strip(), flags=re.IGNORECASE)
    return [p.strip("!?;:") for p in frase.split() if p.strip("!?;:")]


def _chaves(palavras: list[str]) -> set[str]:
    return {sem_acento(p) for p in palavras}


def _encontrar_tipo(palavras: list[str]) -> str:
    tipos = {VERBOS[c] for c in _chaves(palavras) if c in VERBOS}
    if not tipos:
        raise FraseNaoEntendida("não sei se foi venda, gasto ou recebimento")
    if len(tipos) > 1:
        raise FraseNaoEntendida("a frase fala de mais de um tipo de lançamento")
    return tipos.pop()


def _encontrar_conta(palavras: list[str], tipo: str) -> str:
    chaves = _chaves(palavras)
    negocio = bool(chaves & CONTA_NEGOCIO)
    pessoal = bool(chaves & CONTA_PESSOAL)
    if negocio and pessoal:
        raise FraseNaoEntendida("foi do negócio ou pessoal?")
    if tipo == "venda" and pessoal:
        raise FraseNaoEntendida("vendas sempre são do negócio")
    return "negocio" if negocio or tipo == "venda" else "pessoal"


def _separar_numeros(
    palavras: list[str],
) -> tuple[list[Decimal], int | None, list[str]]:
    """Separa números (valores), quantidade "3x" e as palavras do texto."""
    numeros: list[Decimal] = []
    quantidade_x: int | None = None
    texto: list[str] = []
    for palavra in palavras:
        limpa = palavra.lower().rstrip(".,")
        if casamento := QUANTIDADE_X.match(limpa):
            quantidade_x = int(casamento.group(1) or casamento.group(2))
        elif NUMERO.fullmatch(limpa):
            numeros.append(converter_valor(limpa))
        elif (chave := sem_acento(limpa)) and (
            chave not in VERBOS
            and chave not in FORA_DA_DESCRICAO
            and chave not in CONTA_NEGOCIO
            and chave not in CONTA_PESSOAL
        ):
            texto.append(palavra.rstrip(".,"))
    return numeros, quantidade_x, _aparar_ligacoes(texto)


def _aparar_ligacoes(texto: list[str]) -> list[str]:
    """Tira palavras de ligação do começo e do fim ("no almoço" -> "almoço")."""
    inicio, fim = 0, len(texto)
    while inicio < fim and sem_acento(texto[inicio]) in LIGACAO:
        inicio += 1
    while fim > inicio and sem_acento(texto[fim - 1]) in LIGACAO:
        fim -= 1
    return texto[inicio:fim]


def _valor_e_quantidade_da_venda(
    numeros: list[Decimal], quantidade_x: int | None, unitario: bool
) -> tuple[Decimal, int]:
    """Decide quantidade e valor total de uma venda.

    - "vendi bolo 45"          -> 1 unidade, total 45
    - "vendi 3 bolos 45"       -> 3 unidades, total 45
    - "vendi 3x bolo 15 cada"  -> 3 unidades, total 45 (preço unitário)
    """
    if quantidade_x is not None:
        if len(numeros) != 1:
            raise FraseNaoEntendida("não sei qual número é o valor")
        quantidade, valor = quantidade_x, numeros[0]
    elif len(numeros) == 1:
        quantidade, valor = 1, numeros[0]
    elif len(numeros) == 2:
        bruto, valor = numeros
        if bruto != bruto.to_integral_value() or bruto <= 0:
            raise FraseNaoEntendida("a quantidade precisa ser um número inteiro")
        quantidade = int(bruto)
    else:
        raise FraseNaoEntendida(
            "não sei qual número é o valor" if numeros else "faltou o valor"
        )
    if unitario:
        valor = valor * quantidade
    return valor, quantidade


def _categoria(texto: list[str]) -> str:
    """Categoria provisória: a primeira palavra da descrição, em minúsculas.

    A categorização por palavras-chave (issue [15]) troca isso por algo
    melhor ("posto" -> transporte).
    """
    return texto[0].lower()


def _validar_valor(valor: Decimal) -> Decimal:
    if valor <= 0:
        raise FraseNaoEntendida("o valor precisa ser maior que zero")
    if valor != valor.quantize(CENTAVO):
        raise FraseNaoEntendida("o valor tem mais de 2 casas decimais")
    return valor.quantize(CENTAVO)
