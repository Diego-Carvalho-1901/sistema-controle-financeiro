"""Repositório: a única parte do código que lê e grava lançamentos no banco.

Ele recebe e devolve financeiro.modelos.Lancamento, então o resto do app
(cálculos, relatório) funciona igual, venham os dados de um CSV ou do banco.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from financeiro.banco.tabelas import Categoria, LancamentoTabela, Usuario
from financeiro.modelos import Lancamento

CENTAVOS_POR_REAL = 100


def reais_para_centavos(valor: Decimal) -> int:
    """Converte R$ em centavos; recusa valores com mais de 2 casas decimais."""
    centavos = valor * CENTAVOS_POR_REAL
    if centavos != centavos.to_integral_value():
        raise ValueError(f"valor com mais de 2 casas decimais: {valor}")
    return int(centavos)


def centavos_para_reais(centavos: int) -> Decimal:
    """Converte centavos em R$ (1234 -> Decimal('12.34'))."""
    return Decimal(centavos) / CENTAVOS_POR_REAL


class RepositorioLancamentos:
    """Lê e grava lançamentos de usuários usando uma sessão do SQLAlchemy.

    O repositório não faz commit: quem chama decide quando confirmar a
    transação (`sessao.commit()`), o que permite gravar vários lançamentos
    de uma vez, ou nenhum se der erro no meio.
    """

    def __init__(self, sessao: Session) -> None:
        self.sessao = sessao

    def criar_usuario(self, nome: str) -> int:
        """Cadastra um usuário e devolve o id dele."""
        usuario = Usuario(nome=nome)
        self.sessao.add(usuario)
        self.sessao.flush()  # envia o INSERT para o banco preencher o id
        return usuario.id

    def adicionar(self, usuario_id: int, lancamento: Lancamento) -> int:
        """Grava um lançamento do usuário e devolve o id da linha criada.

        A categoria é criada na primeira vez que aparece para esse usuário.
        """
        linha = LancamentoTabela(
            usuario_id=usuario_id,
            categoria=self._obter_ou_criar_categoria(usuario_id, lancamento.categoria),
            data=lancamento.data,
            valor_centavos=reais_para_centavos(lancamento.valor),
            tipo=lancamento.tipo,
            conta=lancamento.conta,
            descricao=lancamento.descricao,
            produto=lancamento.produto,
            quantidade=lancamento.quantidade,
        )
        self.sessao.add(linha)
        self.sessao.flush()
        return linha.id

    def listar(
        self,
        usuario_id: int,
        inicio: date | None = None,
        fim: date | None = None,
    ) -> list[Lancamento]:
        """Devolve os lançamentos do usuário em ordem de data.

        `inicio` e `fim` (inclusivos) filtram o período, se informados.
        """
        consulta = (
            select(LancamentoTabela)
            .join(LancamentoTabela.categoria)
            .where(LancamentoTabela.usuario_id == usuario_id)
            .order_by(LancamentoTabela.data, LancamentoTabela.id)
        )
        if inicio is not None:
            consulta = consulta.where(LancamentoTabela.data >= inicio)
        if fim is not None:
            consulta = consulta.where(LancamentoTabela.data <= fim)
        return [_para_lancamento(linha) for linha in self.sessao.scalars(consulta)]

    def _obter_ou_criar_categoria(self, usuario_id: int, nome: str) -> Categoria:
        consulta = select(Categoria).where(
            Categoria.usuario_id == usuario_id, Categoria.nome == nome
        )
        categoria = self.sessao.scalars(consulta).first()
        if categoria is None:
            categoria = Categoria(usuario_id=usuario_id, nome=nome)
            self.sessao.add(categoria)
        return categoria


def _para_lancamento(linha: LancamentoTabela) -> Lancamento:
    """Converte uma linha do banco no objeto usado pelos cálculos."""
    return Lancamento(
        data=linha.data,
        valor=centavos_para_reais(linha.valor_centavos),
        tipo=linha.tipo,
        categoria=linha.categoria.nome,
        descricao=linha.descricao,
        conta=linha.conta,
        produto=linha.produto,
        quantidade=linha.quantidade,
    )
