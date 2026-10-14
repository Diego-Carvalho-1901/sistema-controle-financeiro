"""Montagem do texto do relatório financeiro.

`gerar_relatorio` devolve o relatório como string em vez de imprimir. Assim
quem chama decide o que fazer com ele (mostrar no terminal, salvar num
arquivo, comparar num teste).
"""

from decimal import Decimal

from financeiro import calculos
from financeiro.modelos import Lancamento

NOMES_MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def nome_do_mes(mes: int) -> str:
    """Devolve o nome do mês (1 a 12) em português.

    Não usa strftime("%B"), que depende do idioma (locale) configurado
    no sistema e mostraria "September" em vez de "setembro".
    """
    return NOMES_MESES[mes - 1]


def gerar_relatorio(lancamentos: list[Lancamento]) -> str:
    """Monta o relatório completo de uma lista (não vazia) de lançamentos."""
    receitas = calculos.filtrar_por_tipo(lancamentos, "receita")
    despesas = calculos.filtrar_por_tipo(lancamentos, "despesa")
    total_receitas = calculos.somar(receitas)
    total_despesas = calculos.somar(despesas)
    por_categoria_despesas = calculos.somar_por_categoria(lancamentos, "despesa")
    por_categoria_receitas = calculos.somar_por_categoria(lancamentos, "receita")
    maior, menor = calculos.encontrar_maior_e_menor(lancamentos)

    linhas: list[str] = []
    linhas += _secao_resumo(total_receitas, total_despesas)
    linhas += _secao_mensal(lancamentos)
    linhas += _secao_historico(lancamentos)
    linhas += _cabecalho("============= MAIOR MOVIMENTAÇÃO ==============")
    linhas.append(_detalhar(maior))
    linhas += _cabecalho("============= MENOR MOVIMENTAÇÃO ==============")
    linhas.append(_detalhar(menor))

    linhas += _cabecalho("============= MEDIAS DE MOVIMENTAÇÕES ==============")
    media_receitas = calculos.calcular_media(total_receitas, len(receitas))
    media_despesas = calculos.calcular_media(total_despesas, len(despesas))
    linhas.append(f"Média de Receitas: R$ {media_receitas:.2f}")
    linhas.append(f"Média de Despesas: R$ {media_despesas:.2f}")

    percentuais_despesas = {
        categoria: calculos.calcular_percentual(valor, total_despesas)
        for categoria, valor in por_categoria_despesas.items()
    }
    percentuais_receitas = {
        categoria: calculos.calcular_percentual(valor, total_receitas)
        for categoria, valor in por_categoria_receitas.items()
    }
    linhas += _cabecalho(
        "============= PERCENTUAIS DE DESPESAS POR CATEGORIA ============="
    )
    linhas += _tabela_percentuais(por_categoria_despesas, percentuais_despesas)
    linhas += _cabecalho(
        "============= PERCENTUAIS DE RECEITAS POR CATEGORIA ============="
    )
    linhas += _tabela_percentuais(por_categoria_receitas, percentuais_receitas)
    linhas += _secao_concentracao(percentuais_despesas)

    linhas += _cabecalho("============= DESPESAS POR CATEGORIA ===============")
    linhas += _listar_categorias(por_categoria_despesas)
    linhas += _cabecalho("========= CATEGORIA COM MAIOR DESPESA ==============")
    categoria, valor = calculos.maior_categoria(por_categoria_despesas)
    linhas.append(f"= > Categoria com maior despesa: {categoria}")
    linhas.append(f"= > Valor da maior despesa: R$ {valor:.2f}")

    linhas += _cabecalho("============== RECEITAS POR CATEGORIA ==============")
    linhas += _listar_categorias(por_categoria_receitas)
    linhas += _cabecalho("========= CATEGORIA COM MAIOR RECEITA ==============")
    categoria, valor = calculos.maior_categoria(por_categoria_receitas)
    linhas.append(f"= > Categoria com maior receita: {categoria}")
    linhas.append(f"= > Valor da maior receita: R$ {valor:.2f}")

    linhas += _cabecalho("================= RANKING DE DESPESAS =================")
    ranking = calculos.ranking_categorias(por_categoria_despesas)
    for posicao, (categoria, valor) in enumerate(ranking, start=1):
        percentual = percentuais_despesas[categoria]
        linhas.append(
            f"{posicao}º | Categoria: {categoria: <15} | Valor: R$ {valor: 10.2f} "
            f"| Percentual: {percentual: 10.2f} %"
        )

    linhas.append("\n" + "=" * 52 + "\n")
    return "\n".join(linhas)


def _cabecalho(titulo: str) -> list[str]:
    """Moldura de '=' do tamanho do título, com linhas em branco em volta."""
    borda = "=" * len(titulo)
    return [f"\n{borda}", titulo, f"{borda}\n"]


def _secao_resumo(total_receitas: Decimal, total_despesas: Decimal) -> list[str]:
    saldo = total_receitas - total_despesas
    comprometida = calculos.calcular_percentual(total_despesas, total_receitas)
    disponivel = calculos.calcular_percentual(saldo, total_receitas)
    return [
        *_cabecalho("================ ANALISE FINANCEIRA ================"),
        f"Total de Receitas: R$ {total_receitas:.2f}",
        f"Total de Despesas: R$ {total_despesas:.2f}",
        f"Saldo: R$ {saldo:.2f}",
        "\n >>> ANALISE PERCENTUAL DE RECEITA COMPROMETIDA E RECEITA DISPONIVEL <<< \n",
        f"Receita Comprometida: {comprometida:.2f} %",
        f"Receita Disponível: {disponivel:.2f} %",
    ]


def _secao_mensal(lancamentos: list[Lancamento]) -> list[str]:
    receitas_mes = calculos.somar_por_mes(lancamentos, "receita")
    despesas_mes = calculos.somar_por_mes(lancamentos, "despesa")
    linhas = _cabecalho("================== ANALISE MENSAL ==================")
    for ano, mes in sorted(receitas_mes.keys() | despesas_mes.keys()):
        receita = receitas_mes.get((ano, mes), calculos.ZERO)
        despesa = despesas_mes.get((ano, mes), calculos.ZERO)
        linhas += [
            f"\nMês: {nome_do_mes(mes)}/{ano}",
            f"Valor de receita: R$ {receita:.2f}",
            f"Valor de despesa: R$ {despesa:.2f}",
            f"Valor do saldo: R$ {receita - despesa:.2f}",
        ]
    return linhas


def _secao_historico(lancamentos: list[Lancamento]) -> list[str]:
    linhas = _cabecalho("=========== HISTÓRICO DE MOVIMENTAÇÕES =============")
    for lancamento in sorted(lancamentos, key=lambda item: item.data):
        linhas.append(
            f"data: {lancamento.data:%d/%m/%Y} | valor: {lancamento.valor:10.2f} "
            f"| Tipo: {lancamento.tipo: <10} | Categoria: {lancamento.categoria: <15} "
            f"| Descricao: {lancamento.descricao: <15}"
        )
    return linhas


def _detalhar(lancamento: Lancamento) -> str:
    return (
        f"= > Data: {lancamento.data:%d/%m/%Y} \n"
        f"= > Valor: R$ {lancamento.valor:.2f} \n"
        f"= > Tipo: {lancamento.tipo} \n"
        f"= > Categoria: {lancamento.categoria} \n"
        f"= > Descricao: {lancamento.descricao}"
    )


def _tabela_percentuais(
    totais: dict[str, Decimal], percentuais: dict[str, Decimal]
) -> list[str]:
    return [
        f"= > {categoria: <15} | R$ {valor:10.2f} | {percentuais[categoria]:10.2f} %"
        for categoria, valor in totais.items()
    ]


def _secao_concentracao(percentuais: dict[str, Decimal]) -> list[str]:
    linhas = _cabecalho(
        "============== ANÁLISE DE CONCENTRAÇÃO DAS DESPESAS ============="
    )
    for categoria, percentual in percentuais.items():
        if calculos.tem_alta_concentracao(percentual):
            nivel = "alta concentracao"
        else:
            nivel = "baixa concentracao"
        linhas.append(
            f"Categoria: {categoria:<15} | Percentual: {percentual:15.2f} % | {nivel}"
        )
    return linhas


def _listar_categorias(totais: dict[str, Decimal]) -> list[str]:
    return [f"= > {categoria} : R$ {valor:.2f}" for categoria, valor in totais.items()]
