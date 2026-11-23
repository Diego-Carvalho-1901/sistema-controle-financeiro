"""Cliente HTTP da API REST, usado pelo bot.

O bot não acessa o banco diretamente: tudo passa pela API, que é o único
ponto de entrada para os dados (veja "Arquitetura" no README).
"""

from datetime import date
from decimal import Decimal

import httpx

URL_PADRAO = "http://127.0.0.1:8000"


class ErroAPI(Exception):
    """A API respondeu com um erro inesperado ou não respondeu."""


class ClienteAPI:
    """Métodos para cada rota que o bot usa.

    Recebe um httpx.Client pronto. Nos testes, entra no lugar dele o
    TestClient do FastAPI (que é um httpx.Client), e assim o bot conversa
    com uma API de verdade, mas sem rede.
    """

    def __init__(self, http: httpx.Client) -> None:
        self.http = http

    @classmethod
    def conectar(
        cls, url_base: str = URL_PADRAO, chave_api: str | None = None
    ) -> "ClienteAPI":
        """Cria o cliente para a API em `url_base`.

        Com `chave_api`, toda requisição leva o cabeçalho X-API-Key.
        """
        cabecalhos = {"X-API-Key": chave_api} if chave_api else {}
        return cls(httpx.Client(base_url=url_base, timeout=10, headers=cabecalhos))

    def buscar_usuario_do_telegram(self, telegram_id: int) -> dict | None:
        """Devolve o usuário ligado a essa conta do Telegram, ou None."""
        resposta = self._get(f"/usuarios/telegram/{telegram_id}", aceitar_404=True)
        return None if resposta is None else resposta.json()

    def criar_usuario(self, nome: str, telegram_id: int) -> dict:
        """Cadastra um usuário ligado à conta do Telegram."""
        return self._enviar(
            "POST", "/usuarios", {"nome": nome, "telegram_id": telegram_id}
        ).json()

    def criar_lancamento(self, usuario_id: int, dados: dict) -> dict:
        """Grava um lançamento e devolve como a API respondeu (com o id)."""
        rota = f"/usuarios/{usuario_id}/lancamentos"
        return self._enviar("POST", rota, dados).json()

    def excluir_ultimo_lancamento(self, usuario_id: int) -> dict | None:
        """Apaga o último lançamento gravado; None se não houver nenhum."""
        rota = f"/usuarios/{usuario_id}/lancamentos/ultimo"
        try:
            resposta = self.http.delete(rota)
        except httpx.HTTPError as erro:
            raise ErroAPI(f"a API não respondeu: {erro}") from erro
        if resposta.status_code == 404:
            return None
        _conferir(resposta)
        return resposta.json()

    def resumo(self, usuario_id: int, nome: str, inicio: date, fim: date):
        """Um dos resumos de /usuarios/{id}/resumos (negocio, pessoal...)."""
        params = {"inicio": inicio.isoformat(), "fim": fim.isoformat()}
        return self._get(f"/usuarios/{usuario_id}/resumos/{nome}", params).json()

    def definir_meta(self, usuario_id: int, categoria: str, valor: Decimal) -> list:
        """Cria ou troca a meta e devolve todas as metas do mês."""
        rota = f"/usuarios/{usuario_id}/metas/{categoria}"
        return self._enviar("PUT", rota, {"valor": str(valor)}).json()

    def listar_metas(self, usuario_id: int, dia: date) -> list[dict]:
        """Metas com o quanto já foi gasto no mês de `dia`."""
        rota = f"/usuarios/{usuario_id}/metas"
        return self._get(rota, {"dia": dia.isoformat()}).json()

    def sugerir_categoria(self, usuario_id: int, descricao: str) -> str | None:
        """Categoria sugerida pela API para a descrição (ou None)."""
        rota = f"/usuarios/{usuario_id}/categorias/sugestao"
        return self._get(rota, {"descricao": descricao}).json()["categoria"]

    def corrigir_categoria_do_ultimo(self, usuario_id: int, categoria: str):
        """Troca a categoria do último lançamento; None se não houver nenhum."""
        rota = f"/usuarios/{usuario_id}/lancamentos/ultimo/categoria"
        try:
            resposta = self.http.put(rota, json={"categoria": categoria})
        except httpx.HTTPError as erro:
            raise ErroAPI(f"a API não respondeu: {erro}") from erro
        if resposta.status_code == 404:
            return None
        _conferir(resposta)
        return resposta.json()

    def gerar_alertas(self, usuario_id: int, dia: date) -> list[dict]:
        """Metas que acabaram de passar de 80% no mês de `dia` (issue [16])."""
        rota = f"/usuarios/{usuario_id}/metas/alertas"
        return self._enviar_com_params("POST", rota, {"dia": dia.isoformat()}).json()

    def listar_usuarios(self) -> list[dict]:
        """Usuários ligados a uma conta do Telegram."""
        return self._get("/usuarios").json()

    def criar_link_do_painel(self, usuario_id: int) -> str:
        """Link de login do painel web, válido por 10 minutos (issue [19])."""
        return self._enviar("POST", f"/usuarios/{usuario_id}/painel/link").json()["url"]

    # --- detalhes de HTTP ---

    def _get(
        self, rota: str, params: dict | None = None, aceitar_404: bool = False
    ) -> httpx.Response | None:
        try:
            resposta = self.http.get(rota, params=params)
        except httpx.HTTPError as erro:
            raise ErroAPI(f"a API não respondeu: {erro}") from erro
        if aceitar_404 and resposta.status_code == 404:
            return None
        _conferir(resposta)
        return resposta

    def _enviar(self, metodo: str, rota: str, dados: dict | None = None):
        return self._enviar_com_params(metodo, rota, None, dados)

    def _enviar_com_params(
        self,
        metodo: str,
        rota: str,
        params: dict | None,
        dados: dict | None = None,
    ) -> httpx.Response:
        try:
            resposta = self.http.request(metodo, rota, params=params, json=dados)
        except httpx.HTTPError as erro:
            raise ErroAPI(f"a API não respondeu: {erro}") from erro
        _conferir(resposta)
        return resposta


def _conferir(resposta: httpx.Response) -> None:
    if resposta.is_error:
        raise ErroAPI(f"{resposta.status_code} em {resposta.url}: {resposta.text}")
