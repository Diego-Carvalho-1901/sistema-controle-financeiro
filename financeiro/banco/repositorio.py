"""Repositório: a única parte do código que lê e grava lançamentos no banco.

Ele recebe e devolve financeiro.modelos.Lancamento, então o resto do app
(cálculos, relatório) funciona igual, venham os dados de um CSV ou do banco.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro.banco.tabelas import (
    Categoria,
    LancamentoTabela,
    Meta,
    RegraCategoria,
    Usuario,
)
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

    def criar_usuario(self, nome: str, telegram_id: int | None = None) -> int:
        """Cadastra um usuário e devolve o id dele."""
        usuario = Usuario(nome=nome, telegram_id=telegram_id)
        self.sessao.add(usuario)
        self.sessao.flush()  # envia o INSERT para o banco preencher o id
        return usuario.id

    def obter_ou_criar_usuario(self, nome: str) -> int:
        """Devolve o id do usuário com esse nome, cadastrando-o se não existir.

        Se houver mais de um usuário com o mesmo nome, usa o mais antigo.
        """
        consulta = select(Usuario.id).where(Usuario.nome == nome).order_by(Usuario.id)
        usuario_id = self.sessao.scalars(consulta).first()
        if usuario_id is None:
            usuario_id = self.criar_usuario(nome)
        return usuario_id

    def buscar_usuario_por_telegram(self, telegram_id: int) -> Usuario | None:
        """Devolve o usuário ligado a essa conta do Telegram, se houver."""
        consulta = select(Usuario).where(Usuario.telegram_id == telegram_id)
        return self.sessao.scalars(consulta).first()

    def usuario_existe(self, usuario_id: int) -> bool:
        """Diz se há um usuário cadastrado com esse id."""
        return self.sessao.get(Usuario, usuario_id) is not None

    def adicionar(self, usuario_id: int, lancamento: Lancamento) -> int:
        """Grava um lançamento do usuário e devolve o id da linha criada.

        A categoria é criada na primeira vez que aparece para esse usuário.
        """
        linha = LancamentoTabela(usuario_id=usuario_id)
        self._preencher(linha, lancamento)
        self.sessao.add(linha)
        self.sessao.flush()
        return linha.id

    def listar(
        self,
        usuario_id: int,
        inicio: date | None = None,
        fim: date | None = None,
        conta: str | None = None,
        categoria: str | None = None,
    ) -> list[Lancamento]:
        """Devolve os lançamentos do usuário em ordem de data.

        Os filtros são opcionais: `inicio` e `fim` (inclusivos) limitam o
        período; `conta` e `categoria` só deixam passar os iguais.
        """
        registros = self.listar_com_ids(usuario_id, inicio, fim, conta, categoria)
        return [lancamento for _id, lancamento in registros]

    def listar_com_ids(
        self,
        usuario_id: int,
        inicio: date | None = None,
        fim: date | None = None,
        conta: str | None = None,
        categoria: str | None = None,
    ) -> list[tuple[int, Lancamento]]:
        """Igual a listar(), mas devolve pares (id, lançamento).

        O id é o que permite editar ou excluir um lançamento depois (a API
        precisa dele; os cálculos, não).
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
        if conta is not None:
            consulta = consulta.where(LancamentoTabela.conta == conta)
        if categoria is not None:
            consulta = consulta.where(Categoria.nome == categoria)
        return [
            (linha.id, _para_lancamento(linha))
            for linha in self.sessao.scalars(consulta)
        ]

    def buscar(self, usuario_id: int, lancamento_id: int) -> Lancamento | None:
        """Devolve o lançamento com esse id, ou None se não for do usuário."""
        linha = self._linha_do_usuario(usuario_id, lancamento_id)
        return None if linha is None else _para_lancamento(linha)

    def atualizar(
        self, usuario_id: int, lancamento_id: int, lancamento: Lancamento
    ) -> bool:
        """Troca todos os campos do lançamento; devolve False se ele não existir.

        Um lançamento de outro usuário conta como inexistente: assim ninguém
        descobre (nem altera) dados alheios só tentando ids.
        """
        linha = self._linha_do_usuario(usuario_id, lancamento_id)
        if linha is None:
            return False
        self._preencher(linha, lancamento)
        self.sessao.flush()
        return True

    def excluir(self, usuario_id: int, lancamento_id: int) -> bool:
        """Apaga o lançamento; devolve False se ele não existir para o usuário."""
        linha = self._linha_do_usuario(usuario_id, lancamento_id)
        if linha is None:
            return False
        self.sessao.delete(linha)
        self.sessao.flush()
        return True

    def excluir_ultimo(self, usuario_id: int) -> tuple[int, Lancamento] | None:
        """Apaga o lançamento gravado por último (o de maior id).

        Devolve (id, lançamento) do que foi apagado, ou None se o usuário
        não tiver nenhum. É o "desfazer" do bot: vale a ordem de gravação,
        não a data do lançamento.
        """
        ultimo = self.ultimo(usuario_id)
        if ultimo is not None:
            self.excluir(usuario_id, ultimo[0])
        return ultimo

    def definir_meta(self, usuario_id: int, categoria: str, valor: Decimal) -> None:
        """Cria ou troca a meta mensal de gastos de uma categoria."""
        categoria_ = self._obter_ou_criar_categoria(usuario_id, categoria)
        self.sessao.flush()  # garante o id da categoria, se ela for nova
        meta = self.sessao.scalars(
            select(Meta).where(Meta.categoria_id == categoria_.id)
        ).first()
        if meta is None:
            meta = Meta(usuario_id=usuario_id, categoria=categoria_)
            self.sessao.add(meta)
        meta.valor_centavos = reais_para_centavos(valor)
        self.sessao.flush()

    def ultimo(self, usuario_id: int) -> tuple[int, Lancamento] | None:
        """(id, lançamento) do último lançamento gravado, ou None."""
        consulta = select(func.max(LancamentoTabela.id)).where(
            LancamentoTabela.usuario_id == usuario_id
        )
        ultimo_id = self.sessao.scalar(consulta)
        if ultimo_id is None:
            return None
        return ultimo_id, self.buscar(usuario_id, ultimo_id)

    def regras_de_categoria(self, usuario_id: int) -> dict[str, str]:
        """Regras que o usuário ensinou: {palavra: categoria}."""
        consulta = select(RegraCategoria.palavra, RegraCategoria.categoria).where(
            RegraCategoria.usuario_id == usuario_id
        )
        return {
            palavra: categoria for palavra, categoria in self.sessao.execute(consulta)
        }

    def aprender_regra(self, usuario_id: int, palavra: str, categoria: str) -> None:
        """Grava (ou troca) a categoria ligada a uma palavra para o usuário."""
        regra = self.sessao.scalars(
            select(RegraCategoria).where(
                RegraCategoria.usuario_id == usuario_id,
                RegraCategoria.palavra == palavra,
            )
        ).first()
        if regra is None:
            regra = RegraCategoria(usuario_id=usuario_id, palavra=palavra)
            self.sessao.add(regra)
        regra.categoria = categoria
        self.sessao.flush()

    def _linha_do_usuario(
        self, usuario_id: int, lancamento_id: int
    ) -> LancamentoTabela | None:
        linha = self.sessao.get(LancamentoTabela, lancamento_id)
        if linha is None or linha.usuario_id != usuario_id:
            return None
        return linha

    def _preencher(self, linha: LancamentoTabela, lancamento: Lancamento) -> None:
        """Copia os campos do Lancamento para a linha do banco."""
        linha.categoria = self._obter_ou_criar_categoria(
            linha.usuario_id, lancamento.categoria
        )
        linha.data = lancamento.data
        linha.valor_centavos = reais_para_centavos(lancamento.valor)
        linha.tipo = lancamento.tipo
        linha.conta = lancamento.conta
        linha.descricao = lancamento.descricao
        linha.produto = lancamento.produto
        linha.quantidade = lancamento.quantidade

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
