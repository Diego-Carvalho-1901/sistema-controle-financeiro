"""Cliente HTTP da API REST, usado pelo bot.

O bot não acessa o banco diretamente: tudo passa pela API, que é o único
ponto de entrada para os dados (veja "Arquitetura" no README).
"""

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
    def conectar(cls, url_base: str = URL_PADRAO) -> "ClienteAPI":
        """Cria o cliente para a API em `url_base`."""
        return cls(httpx.Client(base_url=url_base, timeout=10))

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
        try:
            resposta = self.http.request(metodo, rota, json=dados)
        except httpx.HTTPError as erro:
            raise ErroAPI(f"a API não respondeu: {erro}") from erro
        _conferir(resposta)
        return resposta


def _conferir(resposta: httpx.Response) -> None:
    if resposta.is_error:
        raise ErroAPI(f"{resposta.status_code} em {resposta.url}: {resposta.text}")
