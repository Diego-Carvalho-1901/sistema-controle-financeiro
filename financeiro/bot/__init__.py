"""Bot de Telegram (issue [12] em diante).

Dividido em três partes, para a lógica ser testada sem o Telegram:

- cliente_api.py: fala com a API REST por HTTP;
- conversa.py: decide o que responder (funções comuns, sem Telegram);
- aplicacao.py: liga as funções da conversa aos comandos do Telegram.
"""
