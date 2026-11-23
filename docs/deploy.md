# Deploy: colocando o bot no ar

Guia para rodar a API e o bot 24 horas por dia, com PostgreSQL gerenciado e
backup diário. Ele usa o que já está no repositório (Dockerfile,
`docker-compose.prod.yml` e `scripts/backup.sh`). As contas e os custos são
seus, então os passos que dependem de um painel de provedor estão descritos
de forma genérica.

## Como fica em produção

```text
Telegram ──> bot (container) ──HTTP + X-API-Key──> API (container) ──> PostgreSQL gerenciado
                                                      ^
                                     /saude (monitoramento da hospedagem)
```

- **API e bot usam a mesma imagem Docker**. A API roda as migrações ao
  iniciar (`alembic upgrade head`) e depois sobe o uvicorn.
- **O bot usa *polling***: ele pergunta ao Telegram se há mensagens novas.
  Por isso não precisa de domínio nem de HTTPS. Só pode haver **um**
  processo do bot por token, senão o Telegram responde com erro de
  conflito.
- **A API não tem login de usuário.** Quem protege os dados é a
  `FINANCEIRO_API_KEY`: sem ela no cabeçalho `X-API-Key`, toda rota
  (menos `/saude`) responde 401. Em produção a chave é obrigatória, e o
  `docker-compose.prod.yml` nem sobe sem ela.

## Escolhendo a hospedagem

Qualquer opção que rode containers Docker serve. Confira os preços e os
limites atuais no site de cada uma antes de decidir.

| Opção | Bom para | Atenção |
|---|---|---|
| **VPS** (uma máquina Linux sua, em qualquer provedor) | controle total; o `docker-compose.prod.yml` funciona como está | você cuida de atualizações do sistema e do firewall |
| **PaaS com containers** (Railway, Render, Fly.io e parecidos) | deploy a cada push, logs e reinício automático | o bot precisa de um serviço sempre ligado (*worker*), não de um que "dorme" quando não recebe requisição HTTP |
| **PostgreSQL gerenciado** (Neon, Supabase, o do próprio PaaS...) | backups automáticos e atualizações feitas pelo provedor | use `sslmode=require` na URL; veja quantos dias de backup o plano guarda |

Sugestão para começar: **PostgreSQL gerenciado + uma VPS pequena** (ou um
PaaS) rodando os dois containers.

## Variáveis de ambiente

| Variável | Quem usa | O que é |
|---|---|---|
| `FINANCEIRO_DB_URL` | API | URL do PostgreSQL: `postgresql+psycopg://usuario:senha@host:5432/banco?sslmode=require` |
| `FINANCEIRO_API_KEY` | API e bot | chave compartilhada; gere com `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `TELEGRAM_TOKEN` | bot | token do bot de **produção** no @BotFather (use outro bot para testes) |
| `FINANCEIRO_API_URL` | bot | endereço da API; no compose de produção já é `http://api:8000` |
| `FINANCEIRO_SEGREDO` | API | assina os links e cookies do painel; gere como a chave da API |
| `FINANCEIRO_PAINEL_URL` | API | endereço público do painel com HTTPS, usado nos links do `/painel` |

Elas ficam **só** no servidor (no `.env.prod`) ou no painel de segredos do
PaaS, nunca no git. O `.gitignore` já ignora `.env` e `.env.prod`.

## Passo a passo numa VPS

1. **Crie o banco** no provedor de PostgreSQL e copie a URL de conexão.
2. **Prepare o servidor**: instale o Docker e libere no firewall só a
   porta do SSH. A API escuta apenas em `127.0.0.1`.
3. **Baixe o código e configure**:

   ```bash
   git clone https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro.git
   cd sistema-controle-financeiro
   cp .env.prod.example .env.prod
   nano .env.prod          # preencha as três variáveis
   chmod 600 .env.prod     # só o seu usuário lê
   ```

4. **Suba**:

   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
   docker compose -f docker-compose.prod.yml logs -f      # Ctrl+C sai dos logs
   curl http://127.0.0.1:8000/saude                       # {"status":"ok"}
   ```

5. **Teste no Telegram**: mande `/start` e `gastei 1 teste`, e depois
   `/desfazer`.
6. **Atualizar** depois de um merge na `main`:

   ```bash
   git pull
   docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
   ```

Num PaaS, os passos 2 a 4 viram: criar dois serviços a partir do
Dockerfile (a API com o comando padrão e o bot com
`python -m financeiro.bot`), cadastrar as variáveis no painel e apontar
`FINANCEIRO_API_URL` do bot para o endereço interno da API.

## Painel web com HTTPS

O painel roda na mesma API, em `/painel/`. Para abri-lo de fora do
servidor, coloque um proxy reverso com HTTPS (Caddy, Nginx com
Let's Encrypt, ou o domínio do próprio PaaS) apontando para a porta 8000.
Depois, preencha `FINANCEIRO_PAINEL_URL` com esse endereço. O compose de
produção já liga o `FINANCEIRO_COOKIE_SEGURO=1`, para o cookie de sessão
só trafegar por HTTPS.

## Backup diário

1. **O do provedor**: confira no painel do PostgreSQL gerenciado se os
   backups automáticos estão ligados e por quantos dias ficam guardados.
2. **Uma cópia sua**, fora do provedor, com o `scripts/backup.sh`. Ele roda
   o `pg_dump` em formato comprimido e apaga os backups com mais de 7 dias.
   Na VPS, agende com o `cron` (`crontab -e`) para as 3h:

   ```cron
   0 3 * * * cd /caminho/sistema-controle-financeiro && set -a && . ./.env.prod && set +a && docker run --rm -v "$PWD:/app" -w /app -e FINANCEIRO_DB_URL postgres:16 sh scripts/backup.sh >> backups.log 2>&1
   ```

   O container `postgres:16` só fornece o `pg_dump`: o seu servidor não
   precisa ter o PostgreSQL instalado.
3. **Teste a restauração** uma vez, num banco vazio. Backup que nunca foi
   restaurado não é backup:

   ```bash
   pg_restore --clean --if-exists --no-owner -d "postgresql://...banco-de-teste..." backups/financeiro-AAAAMMDD-HHMMSS.dump
   ```

Os backups têm dados financeiros de usuários. Guarde-os num lugar privado,
de preferência criptografado, e nunca no repositório (`backups/` está no
`.gitignore`).

## Checklist antes de chamar usuários

- [ ] `/saude` responde `ok` e a hospedagem está monitorando essa rota.
- [ ] `FINANCEIRO_API_KEY` forte, igual na API e no bot.
- [ ] Bot de produção diferente do bot de testes.
- [ ] Backup automático do provedor ligado e uma restauração testada.
- [ ] Só uma instância do bot rodando.
- [ ] Logs acessíveis (`docker compose logs` ou o painel do PaaS).
