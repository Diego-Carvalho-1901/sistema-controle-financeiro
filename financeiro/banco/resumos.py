"""Resumos calculados pelo próprio banco, com SUM e GROUP BY.

O repositório (financeiro/banco/repositorio.py) devolve lançamentos um a um,
e os cálculos em financeiro/calculos.py somam em Python. Isso funciona, mas
traz todas as linhas do banco para a memória. Aqui o banco faz a soma e
devolve só o resultado: uma linha por mês ou por categoria.

Os valores continuam em centavos dentro do SQL (soma de inteiros é exata)
e só viram Decimal em reais no fim, com centavos_para_reais().
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, case, extract, func, select
from sqlalchemy.orm import Session

from financeiro.banco.repositorio import centavos_para_reais
from financeiro.banco.tabelas import Categoria, LancamentoTabela
from financeiro.calculos import ResumoNegocio

# Atalho para as colunas usadas em quase toda consulta.
L = LancamentoTabela


@dataclass(frozen=True)
class ResumoMes:
    """Totais de um mês, separados por tipo de lançamento."""

    ano: int
    mes: int
    receitas: Decimal
    despesas: Decimal
    vendas: Decimal

    @property
    def saldo(self) -> Decimal:
        """O que entrou (receitas + vendas) menos o que saiu (despesas)."""
        return self.receitas + self.vendas - self.despesas


def _soma_se(condicao) -> object:
    """SUM(CASE WHEN condicao THEN valor_centavos ELSE 0 END).

    É a "soma condicional": numa única passada pela tabela, cada coluna do
    resultado soma só as linhas que atendem à sua condição.
    """
    return func.coalesce(func.sum(case((condicao, L.valor_centavos), else_=0)), 0)


def _filtrar(
    consulta: Select,
    usuario_id: int,
    inicio: date | None,
    fim: date | None,
) -> Select:
    """Aplica o WHERE comum a todos os resumos: usuário e período."""
    consulta = consulta.where(L.usuario_id == usuario_id)
    if inicio is not None:
        consulta = consulta.where(L.data >= inicio)
    if fim is not None:
        consulta = consulta.where(L.data <= fim)
    return consulta


def resumo_por_mes(
    sessao: Session,
    usuario_id: int,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[ResumoMes]:
    """Receitas, despesas e vendas de cada mês, em ordem cronológica.

    SQL gerado (simplificado):

        SELECT EXTRACT(year FROM data), EXTRACT(month FROM data),
               SUM(CASE WHEN tipo = 'receita' THEN valor_centavos ELSE 0 END),
               ...
        FROM lancamentos WHERE usuario_id = :id
        GROUP BY 1, 2 ORDER BY 1, 2

    `extract` funciona igual no SQLite e no PostgreSQL (o SQLAlchemy traduz
    para o dialeto de cada banco). Meses sem lançamento não aparecem.
    """
    ano = extract("year", L.data).label("ano")
    mes = extract("month", L.data).label("mes")
    consulta = select(
        ano,
        mes,
        _soma_se(L.tipo == "receita"),
        _soma_se(L.tipo == "despesa"),
        _soma_se(L.tipo == "venda"),
    )
    consulta = _filtrar(consulta, usuario_id, inicio, fim)
    consulta = consulta.group_by(ano, mes).order_by(ano, mes)
    return [
        ResumoMes(
            ano=int(linha_ano),
            mes=int(linha_mes),
            receitas=centavos_para_reais(receitas),
            despesas=centavos_para_reais(despesas),
            vendas=centavos_para_reais(vendas),
        )
        for linha_ano, linha_mes, receitas, despesas, vendas in sessao.execute(consulta)
    ]


def resumo_por_categoria(
    sessao: Session,
    usuario_id: int,
    tipo: str = "despesa",
    conta: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[tuple[str, Decimal]]:
    """Total de cada categoria de um `tipo`, do maior para o menor.

    Usa JOIN com a tabela de categorias para devolver o nome, e GROUP BY no
    nome. Empates saem em ordem alfabética, para o resultado ser previsível.
    """
    total = func.sum(L.valor_centavos).label("total")
    consulta = select(Categoria.nome, total).join(L.categoria).where(L.tipo == tipo)
    if conta is not None:
        consulta = consulta.where(L.conta == conta)
    consulta = _filtrar(consulta, usuario_id, inicio, fim)
    consulta = consulta.group_by(Categoria.nome).order_by(total.desc(), Categoria.nome)
    return [
        (nome, centavos_para_reais(centavos))
        for nome, centavos in sessao.execute(consulta)
    ]


def resumo_negocio(
    sessao: Session,
    usuario_id: int,
    inicio: date | None = None,
    fim: date | None = None,
) -> ResumoNegocio:
    """Faturamento e custos da conta negócio, somados no banco.

    Faturamento = vendas + receitas do negócio; custos = despesas do
    negócio. Devolve o mesmo ResumoNegocio de financeiro.calculos, então o
    lucro e a margem são calculados do mesmo jeito nos dois caminhos.
    """
    consulta = select(
        _soma_se(L.tipo.in_(("venda", "receita"))),
        _soma_se(L.tipo == "despesa"),
    ).where(L.conta == "negocio")
    consulta = _filtrar(consulta, usuario_id, inicio, fim)
    faturamento, custos = sessao.execute(consulta).one()
    return ResumoNegocio(
        faturamento=centavos_para_reais(faturamento),
        custos=centavos_para_reais(custos),
    )


def saldo_pessoal(
    sessao: Session,
    usuario_id: int,
    inicio: date | None = None,
    fim: date | None = None,
) -> Decimal:
    """Receitas menos despesas da conta pessoal, numa só soma no banco.

    O CASE dá sinal ao valor: receita soma, despesa subtrai.
    """
    sinal = case((L.tipo == "receita", L.valor_centavos), else_=-L.valor_centavos)
    consulta = select(func.coalesce(func.sum(sinal), 0)).where(L.conta == "pessoal")
    consulta = _filtrar(consulta, usuario_id, inicio, fim)
    return centavos_para_reais(sessao.scalar(consulta))
