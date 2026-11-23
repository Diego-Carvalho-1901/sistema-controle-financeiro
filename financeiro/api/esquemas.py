"""Esquemas Pydantic: o formato do JSON que entra e sai da API.

Eles validam a entrada antes de qualquer coisa chegar ao banco. Um JSON
inválido nunca vira um Lancamento: o FastAPI responde 422 dizendo qual
campo está errado.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from financeiro.modelos import Lancamento

# Precisam ser iguais a financeiro.modelos.TIPOS e CONTAS (há um teste
# conferindo). Com Literal, o Swagger mostra as opções válidas.
Tipo = Literal["receita", "despesa", "venda"]
Conta = Literal["negocio", "pessoal"]

# Dinheiro: positivo e com no máximo 2 casas decimais (centavos).
Valor = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]

CENTAVO = Decimal("0.01")


class UsuarioEntrada(BaseModel):
    """Dados para cadastrar um usuário."""

    nome: str = Field(min_length=1, max_length=100)
    telegram_id: int | None = None


class UsuarioSaida(UsuarioEntrada):
    """Usuário cadastrado, com o id gerado pelo banco."""

    id: int


class LancamentoCampos(BaseModel):
    """Campos de um lançamento, comuns à entrada e à saída."""

    data: date
    valor: Valor
    tipo: Tipo
    categoria: str = Field(min_length=1, max_length=50)
    descricao: str = Field(default="", max_length=200)
    conta: Conta = "pessoal"
    produto: str | None = Field(default=None, max_length=100)
    quantidade: int | None = Field(default=None, gt=0)


class LancamentoEntrada(LancamentoCampos):
    """Dados de um lançamento enviados para criar ou editar."""

    @model_validator(mode="after")
    def _aplicar_regras_do_modelo(self) -> "LancamentoEntrada":
        """Reaproveita as regras de Lancamento (ex.: venda só na conta negócio).

        O ValueError lançado pelo Lancamento vira um erro 422 na resposta, em
        vez de ser reescrito aqui (a regra fica num lugar só).
        """
        self.para_lancamento()
        return self

    def para_lancamento(self) -> Lancamento:
        """Converte no objeto usado pelo repositório e pelos cálculos."""
        return Lancamento(**self.model_dump())


class LancamentoSaida(LancamentoCampos):
    """Lançamento como a API devolve: os mesmos campos mais o id.

    Não repete a validação da entrada: o que sai já foi validado ao entrar.
    """

    id: int

    @classmethod
    def de_lancamento(cls, id_: int, lancamento: Lancamento) -> "LancamentoSaida":
        """Monta a resposta a partir do id e do Lancamento lido do banco."""
        return cls(
            id=id_,
            data=lancamento.data,
            # Sempre com 2 casas: 45.9 sai como "45.90".
            valor=lancamento.valor.quantize(CENTAVO),
            tipo=lancamento.tipo,
            categoria=lancamento.categoria,
            descricao=lancamento.descricao,
            conta=lancamento.conta,
            produto=lancamento.produto,
            quantidade=lancamento.quantidade,
        )


# --- Resumos (issue [10]) ---


class ResumoMesSaida(BaseModel):
    """Totais de um mês."""

    ano: int
    mes: int = Field(ge=1, le=12)
    receitas: Decimal
    despesas: Decimal
    vendas: Decimal
    saldo: Decimal


class CategoriaTotalSaida(BaseModel):
    """Total gasto (ou recebido) numa categoria."""

    categoria: str
    total: Decimal


class ResumoNegocioSaida(BaseModel):
    """Faturamento, custos, lucro e margem (%) da conta negócio."""

    faturamento: Decimal
    custos: Decimal
    lucro: Decimal
    margem: Decimal


class SaldoPessoalSaida(BaseModel):
    """Receitas menos despesas da conta pessoal."""

    saldo: Decimal


# --- Metas (issue [14]) ---


class MetaEntrada(BaseModel):
    """Valor da meta mensal de gastos de uma categoria."""

    valor: Valor


class MetaSaida(BaseModel):
    """Meta de uma categoria e quanto dela já foi gasto no mês."""

    categoria: str
    meta: Decimal
    gasto: Decimal
    percentual: Decimal
