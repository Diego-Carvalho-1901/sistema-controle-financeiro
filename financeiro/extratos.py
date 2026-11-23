"""Leitura de extratos CSV exportados pelos bancos (issue [18]).

Cada banco exporta o extrato num formato diferente: separador, formato da
data e do valor, e às vezes umas linhas de apresentação antes do
cabeçalho. Cada formato é descrito por um FormatoBanco, e o formato certo
é escolhido pelo cabeçalho.

Num extrato, o sinal do valor diz o tipo: negativo é despesa (saiu
dinheiro) e positivo é receita. A categoria vem da categorização por
palavras-chave (issue [15]).

Os layouts seguem os modelos de exportação conhecidos de cada banco e
foram testados com arquivos de exemplo inventados (dados/extratos/).
Confira com um extrato real anonimizado antes de divulgar para usuários.
"""

import csv
import io
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from financeiro.categorizacao import normalizar
from financeiro.leitura import ErroLeitura, ResultadoLinha
from financeiro.modelos import Lancamento

# Quantas linhas do começo do arquivo olhar procurando o cabeçalho.
LINHAS_DE_APRESENTACAO = 15

CATEGORIA_PADRAO = "outros"


@dataclass(frozen=True)
class FormatoBanco:
    """Como ler o extrato de um banco."""

    nome: str
    separador: str
    cabecalho: tuple[str, ...]  # normalizado: minúsculo e sem acento
    coluna_data: str
    coluna_valor: str
    coluna_descricao: str
    formato_data: str
    decimal_com_virgula: bool


NUBANK = FormatoBanco(
    nome="Nubank (conta)",
    separador=",",
    cabecalho=("data", "valor", "identificador", "descricao"),
    coluna_data="data",
    coluna_valor="valor",
    coluna_descricao="descricao",
    formato_data="%d/%m/%Y",
    decimal_com_virgula=False,  # -45.90
)

INTER = FormatoBanco(
    nome="Inter (conta)",
    separador=";",
    cabecalho=("data lancamento", "descricao", "valor", "saldo"),
    coluna_data="data lancamento",
    coluna_valor="valor",
    coluna_descricao="descricao",
    formato_data="%d/%m/%Y",
    decimal_com_virgula=True,  # -1.234,56
)

FORMATOS = (NUBANK, INTER)


def detectar(texto: str) -> tuple[FormatoBanco, int] | None:
    """Acha o formato do extrato e a posição (0, 1, 2...) do cabeçalho.

    Devolve None se nenhuma das primeiras linhas for o cabeçalho de um
    banco conhecido (o arquivo pode ser um CSV do próprio app).
    """
    for posicao, linha in enumerate(texto.splitlines()[:LINHAS_DE_APRESENTACAO]):
        for formato in FORMATOS:
            colunas = linha.split(formato.separador)
            if tuple(normalizar(c.strip().strip('"')) for c in colunas) == (
                formato.cabecalho
            ):
                return formato, posicao
    return None


def ler_extrato(
    texto: str,
    conta: str = "pessoal",
    categorizar: Callable[[str], str | None] | None = None,
) -> Iterator[tuple[int, ResultadoLinha]]:
    """Converte o extrato linha a linha, sem parar no primeiro erro.

    Gera (número da linha no arquivo, Lancamento ou ErroLeitura), igual a
    financeiro.leitura.ler_linhas, para o importador tratar os dois do
    mesmo jeito. `conta` diz se a conta do banco é do negócio ou pessoal.
    """
    encontrado = detectar(texto)
    if encontrado is None:
        raise ErroLeitura("Extrato de banco não reconhecido.")
    formato, posicao = encontrado
    categorizar = categorizar or (lambda _descricao: None)

    leitor = csv.reader(io.StringIO(texto), delimiter=formato.separador)
    for numero_linha, linha in enumerate(leitor, start=1):
        if numero_linha <= posicao + 1 or not any(campo.strip() for campo in linha):
            continue  # apresentação, cabeçalho ou linha em branco
        if len(linha) != len(formato.cabecalho):
            yield (
                numero_linha,
                ErroLeitura(
                    f"Linha {numero_linha}: esperadas {len(formato.cabecalho)} "
                    f"colunas no extrato {formato.nome}, mas foram "
                    f"encontradas {len(linha)}."
                ),
            )
            continue
        campos = dict(zip(formato.cabecalho, (c.strip() for c in linha), strict=True))
        try:
            yield numero_linha, _converter(formato, campos, conta, categorizar)
        except ErroLeitura as erro:
            yield numero_linha, ErroLeitura(f"Linha {numero_linha}: {erro}")


def _converter(
    formato: FormatoBanco,
    campos: dict[str, str],
    conta: str,
    categorizar: Callable[[str], str | None],
) -> Lancamento:
    texto_data = campos[formato.coluna_data]
    try:
        data = datetime.strptime(texto_data, formato.formato_data).date()
    except ValueError:
        raise ErroLeitura(f"data inválida '{texto_data}'.") from None

    valor = converter_valor_do_extrato(
        campos[formato.coluna_valor], formato.decimal_com_virgula
    )
    if valor == 0:
        raise ErroLeitura("valor zerado.")
    descricao = campos[formato.coluna_descricao] or "sem descrição"
    return Lancamento(
        data=data,
        valor=abs(valor),
        tipo="despesa" if valor < 0 else "receita",
        categoria=categorizar(descricao) or CATEGORIA_PADRAO,
        descricao=descricao[:200],
        conta=conta,
    )


def converter_valor_do_extrato(texto: str, decimal_com_virgula: bool) -> Decimal:
    """'-1.234,56' (com vírgula) ou '-1234.56' (com ponto) -> Decimal."""
    limpo = texto.replace("R$", "").replace(" ", "").replace("−", "-")
    if decimal_com_virgula:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        raise ErroLeitura(f"valor inválido '{texto}'.") from None
    if not valor.is_finite():
        raise ErroLeitura(f"valor inválido '{texto}'.")
    return valor
