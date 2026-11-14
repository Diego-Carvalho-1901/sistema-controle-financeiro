"""Importação de CSVs para o banco, com relatório do que aconteceu.

Diferente do relatório (main.py), que para no primeiro erro, o importador
lê o arquivo inteiro: grava as linhas válidas e lista as inválidas com o
número da linha, para a pessoa corrigir só o que deu errado.

Reimportar o mesmo arquivo não duplica nada. Um lançamento é considerado
repetido quando já existe no banco outro com todos os campos iguais (data,
valor, tipo, categoria, descrição, conta, produto e quantidade). A
comparação é por contagem: se o CSV tem dois cafés iguais no mesmo dia e o
banco já tem um, só o segundo é gravado. Assim dois gastos idênticos de
verdade não se perdem, e reimportar o arquivo grava zero linhas.
"""

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from financeiro.banco.repositorio import RepositorioLancamentos, reais_para_centavos
from financeiro.leitura import ErroLeitura, ler_linhas
from financeiro.modelos import Lancamento


@dataclass
class RelatorioImportacao:
    """Resumo de uma importação.

    `ignoradas` guarda os números das linhas que já estavam no banco e
    `erros` guarda as mensagens das linhas inválidas (cada mensagem já
    começa com "Linha N:").
    """

    importadas: int = 0
    ignoradas: list[int] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)

    def texto(self) -> str:
        """Monta o resumo para mostrar no terminal."""
        partes = [
            f"Linhas importadas: {self.importadas}",
            f"Linhas ignoradas (já estavam no banco): {len(self.ignoradas)}",
        ]
        if self.ignoradas:
            partes.append("  " + ", ".join(str(numero) for numero in self.ignoradas))
        partes.append(f"Linhas com erro: {len(self.erros)}")
        partes += [f"  {erro}" for erro in self.erros]
        return "\n".join(partes)


def importar_csv(
    repositorio: RepositorioLancamentos, usuario_id: int, caminho: Path
) -> RelatorioImportacao:
    """Abre o CSV em `caminho` e importa as linhas para o usuário.

    Lança FileNotFoundError se o arquivo não existir e ErroLeitura se o
    arquivo inteiro for inválido (vazio ou com cabeçalho desconhecido).
    """
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        linhas = csv.reader(arquivo, skipinitialspace=True)
        return importar_linhas(repositorio, usuario_id, linhas)


def importar_linhas(
    repositorio: RepositorioLancamentos, usuario_id: int, linhas: Iterable[list[str]]
) -> RelatorioImportacao:
    """Grava no banco as linhas válidas que ainda não estão lá.

    Não faz commit: quem chama confirma a transação (o comando de
    importação faz `sessao.commit()` no fim).
    """
    relatorio = RelatorioImportacao()
    validos: list[tuple[int, Lancamento]] = []
    for numero_linha, resultado in ler_linhas(linhas):
        if isinstance(resultado, ErroLeitura):
            relatorio.erros.append(str(resultado))
        elif not _cabe_em_centavos(resultado):
            relatorio.erros.append(
                f"Linha {numero_linha}: valor com mais de 2 casas decimais "
                f"'{resultado.valor}'."
            )
        else:
            validos.append((numero_linha, resultado))

    ja_no_banco = _contar_existentes(repositorio, usuario_id, validos)
    for numero_linha, lancamento in validos:
        if ja_no_banco[lancamento] > 0:
            ja_no_banco[lancamento] -= 1
            relatorio.ignoradas.append(numero_linha)
        else:
            repositorio.adicionar(usuario_id, lancamento)
            relatorio.importadas += 1
    return relatorio


def _cabe_em_centavos(lancamento: Lancamento) -> bool:
    """Diz se o valor pode ser gravado em centavos (no máximo 2 casas)."""
    try:
        reais_para_centavos(lancamento.valor)
    except ValueError:
        return False
    return True


def _contar_existentes(
    repositorio: RepositorioLancamentos,
    usuario_id: int,
    validos: list[tuple[int, Lancamento]],
) -> Counter[Lancamento]:
    """Conta quantas vezes cada lançamento já existe no banco.

    Só busca o período coberto pelo arquivo, para não carregar o histórico
    inteiro do usuário. Lancamento é uma dataclass congelada (frozen), por
    isso pode ser chave de dicionário e entrar num Counter.
    """
    if not validos:
        return Counter()
    datas = [lancamento.data for _, lancamento in validos]
    return Counter(repositorio.listar(usuario_id, inicio=min(datas), fim=max(datas)))
