# Controle financeiro para autônomos e MEIs

[![CI](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/actions/workflows/ci.yml/badge.svg)](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/actions/workflows/ci.yml)

App em Python que separa o dinheiro do negócio do dinheiro pessoal e mostra,
sem planilha, quanto o negócio realmente lucrou no mês.

> **Estado atual:** ferramenta de linha de comando que lê CSVs e gera um
> relatório, com banco de dados, importador de CSV e uma API REST local
> (FastAPI). Resumos pela API, Docker e bot de Telegram estão no
> [roteiro](#roteiro), em desenvolvimento.

## O problema

Quem trabalha por conta própria costuma usar a mesma conta para tudo: a
farinha do bolo, o aluguel e o cinema saem do mesmo lugar. No fim do mês fica
difícil responder perguntas simples:

- Quanto o negócio faturou e quanto gastou para produzir?
- O negócio deu lucro ou eu só estou trocando dinheiro de bolso?
- Quanto sobrou para mim, tirando o que é do negócio?

Planilhas resolvem, mas exigem disciplina que pouca gente mantém. A ideia do
projeto é registrar cada movimentação do jeito mais simples possível (no fim,
uma mensagem no Telegram como `vendi 3 bolos 45`) e deixar o app fazer as
contas.

## Para quem

- **Autônomos e MEIs** que vendem produtos ou serviços: confeiteiras,
  costureiras, técnicos, freelancers.
- Pessoas que **não querem aprender um sistema contábil**, só saber se estão
  ganhando dinheiro.

Os dados de exemplo em [`dados/`](dados/) seguem esse perfil: uma confeitaria
caseira que vende bolos e doces e também registra os gastos pessoais.

## O que já funciona

- **Leitura de CSV** em três formatos, reconhecidos pelo cabeçalho (veja
  [Formatos de CSV](#formatos-de-csv)), inclusive o CSV de vendas do projeto
  irmão [analisador-vendas-csv](https://github.com/Diego-Carvalho-1901/analisador-vendas-csv).
- **Vários arquivos no mesmo relatório**: `python main.py a.csv b.csv c.csv`.
- **Negócio x pessoal**: cada lançamento pertence a uma conta (`negocio` ou
  `pessoal`). O relatório mostra faturamento, custos, lucro e margem do
  negócio, e o saldo pessoal separado.
- **Análises gerais**: receitas, despesas e saldo; resumo por mês; totais,
  percentuais e ranking por categoria; maior e menor movimentação; médias;
  alerta de categorias com alta concentração de gastos.
- **Dinheiro com `Decimal`**, não `float`, para não perder centavos em somas.
- **Erros de dados com mensagem clara** (arquivo inexistente, valor, data,
  tipo ou conta inválidos), indicando a linha do problema.
- **Testes automatizados** com pytest e **CI** no GitHub Actions rodando ruff
  e pytest em todo pull request.

## O que vem por aí

O plano completo, com critérios de pronto, está nas [issues](#roteiro). Em
resumo:

| Fase | Entrega |
|---|---|
| 2 — Backend | Banco de dados (SQLAlchemy + Alembic), importador de CSV para o banco, API REST com FastAPI, resumos com agregações em SQL, Docker com PostgreSQL |
| 3 — Bot | Bot de Telegram que entende frases livres (`gastei 30 almoço`), comandos `/resumo`, `/desfazer` e `/meta`, categorização automática, resumo semanal e alerta de meta, deploy com backups |
| 4 — Produto | Importação de extratos de bancos reais, painel web com gráficos do mês, métricas de uso |

## Arquitetura

### Hoje

O código fica no pacote `financeiro/`, com uma responsabilidade por módulo. O
fluxo é linear: ler, calcular, formatar.

```text
CSV(s) ──► leitura.py ──► list[Lancamento] ──► calculos.py ──► relatorio.py ──► terminal
                              (modelos.py)
```

```text
sistema-controle-financeiro/
├── main.py                 # linha de comando (argparse): recebe os CSVs e imprime o relatório
├── importar.py             # linha de comando: grava CSVs no banco e mostra o relatório da importação
├── financeiro/
│   ├── modelos.py          # dataclass Lancamento: data, valor, tipo, categoria, descrição, conta
│   ├── leitura.py          # reconhece o formato do CSV e converte cada linha, validando os dados
│   ├── calculos.py         # funções puras: somas, médias, percentuais, lucro do negócio
│   ├── relatorio.py        # monta o texto do relatório a partir dos cálculos
│   ├── importacao.py       # importa CSVs para o banco sem duplicar e lista as linhas com erro
│   ├── api/                # API REST (FastAPI): esquemas Pydantic e rotas do CRUD de lançamentos
│   └── banco/              # tabelas (SQLAlchemy), conexão e repositório de lançamentos
├── migracoes/              # migrações do Alembic (alembic.ini fica na raiz)
├── dados/                  # CSVs de exemplo (pessoal, negócio e vendas)
├── tests/                  # testes com pytest (cálculos, leitura, relatório, linha de comando)
└── .github/workflows/ci.yml
```

As regras de negócio ficam em funções puras (`calculos.py`), que recebem
lançamentos e devolvem números, sem ler arquivo nem imprimir nada. Isso deixa
os testes simples e permite reaproveitar as mesmas funções quando a entrada
deixar de ser um CSV e passar a ser o banco de dados.

### Para onde vai

```mermaid
flowchart LR
    U[Usuário] -- mensagem --> T[Bot de Telegram]
    U -- navegador --> P[Painel web]
    C[CSV / extrato] --> I[Importador]
    T --> A[API FastAPI]
    P --> A
    I --> A
    A --> N[financeiro/<br>regras de negócio]
    A --> DB[(PostgreSQL)]
```

A API vira o único ponto de entrada para os dados: bot, painel e importador
falam com ela, e ela usa as mesmas regras de negócio que o relatório usa hoje.

## Stack

| | Hoje | Planejado |
|---|---|---|
| Linguagem | Python 3.12, só biblioteca padrão (`csv`, `decimal`, `datetime`, `argparse`, `dataclasses`) | |
| Qualidade | pytest, ruff (lint e formatação), GitHub Actions | |
| Dados | Arquivos CSV | SQLAlchemy, Alembic, SQLite (dev) e PostgreSQL (produção) |
| Interfaces | Linha de comando, API REST com FastAPI | Bot de Telegram, painel web |
| Infra | Docker e docker-compose (API + PostgreSQL) | Deploy com backups |

## Como rodar

Precisa de Python 3.10 ou mais novo (o CI usa 3.12). O relatório usa só a
biblioteca padrão; o banco de dados usa SQLAlchemy e Alembic.

```bash
git clone https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro.git
cd sistema-controle-financeiro
pip install -r requirements.txt

python main.py                       # usa dados/movimentacoes.csv
python main.py caminho/para/outro.csv
python main.py dados/movimentacoes.csv dados/vendas.csv dados/negocio.csv
```

O último comando junta os três arquivos de exemplo. No fim do relatório
aparece a parte que interessa ao autônomo:

```text
====================================================
================ NEGÓCIO x PESSOAL =================
====================================================

Faturamento do negócio: R$ 1095.00
Custos do negócio: R$ 285.00
Lucro do negócio: R$ 810.00 (margem de 73.97 %)
Saldo pessoal: R$ 5627.50
```

Antes dela vêm o resumo geral, a análise mensal, o histórico, as médias e as
análises por categoria. Se algum arquivo tiver problema, o programa mostra a
linha e o motivo e termina com código de saída 1.

### Banco de dados

O esquema (usuários, categorias e lançamentos) é criado pelas migrações do
Alembic. Sem configuração nenhuma, ele usa um arquivo SQLite local
(`financeiro.db`); para outro banco, defina a variável `FINANCEIRO_DB_URL`.

```bash
alembic upgrade head      # cria ou atualiza as tabelas
alembic current           # mostra em qual migração o banco está
alembic downgrade base    # apaga as tabelas
```

Para gravar CSVs no banco, use o `importar.py` (aceita os mesmos formatos do
relatório). Os lançamentos ficam ligados ao usuário informado, que é criado
na primeira importação:

```bash
python importar.py dados/movimentacoes.csv dados/vendas.csv --usuario Ana
```

```text
dados/vendas.csv
Linhas importadas: 0
Linhas ignoradas (já estavam no banco): 4
  2, 3, 4, 5
Linhas com erro: 0
```

As linhas válidas são gravadas e as inválidas aparecem com o número e o
motivo. Importar o mesmo arquivo de novo não duplica nada: uma linha é
ignorada quando o banco já tem um lançamento com todos os campos iguais. A
comparação é por contagem, então dois gastos idênticos no mesmo arquivo
(dois cafés iguais no mesmo dia) são gravados os dois. O relatório
(`main.py`) ainda lê dos CSVs.

### API REST

A API usa o mesmo banco (rode `alembic upgrade head` antes) e expõe o CRUD
de lançamentos. A documentação interativa (Swagger) fica em
<http://127.0.0.1:8000/docs>, onde dá para testar cada rota pelo navegador.

```bash
uvicorn financeiro.api.app:app --reload
```

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/usuarios` | cadastra um usuário |
| `POST` | `/usuarios/{usuario_id}/lancamentos` | cria um lançamento |
| `GET` | `/usuarios/{usuario_id}/lancamentos` | lista, com filtros opcionais `inicio`, `fim`, `conta` e `categoria` |
| `GET` | `/usuarios/{usuario_id}/lancamentos/{id}` | devolve um lançamento |
| `PUT` | `/usuarios/{usuario_id}/lancamentos/{id}` | substitui os campos de um lançamento |
| `DELETE` | `/usuarios/{usuario_id}/lancamentos/{id}` | exclui um lançamento |
| `GET` | `/usuarios/{usuario_id}/resumos/mensal` | receitas, despesas, vendas e saldo de cada mês |
| `GET` | `/usuarios/{usuario_id}/resumos/categorias` | total por categoria (filtros `tipo`, `conta`, `inicio`, `fim`) |
| `GET` | `/usuarios/{usuario_id}/resumos/negocio` | faturamento, custos, lucro e margem do negócio |
| `GET` | `/usuarios/{usuario_id}/resumos/pessoal` | saldo da conta pessoal |

```bash
curl -X POST http://127.0.0.1:8000/usuarios/1/lancamentos \
  -H "Content-Type: application/json" \
  -d '{"data": "2026-11-10", "valor": "45.90", "tipo": "venda",
       "categoria": "bolos", "descricao": "Bolo", "conta": "negocio",
       "produto": "Bolo de cenoura", "quantidade": 3}'
```

Os resumos aceitam `inicio` e `fim` para limitar o período, e as somas são
feitas pelo próprio banco com `SUM(...)` e `GROUP BY` (veja
`financeiro/banco/resumos.py`), em vez de trazer todas as linhas para o
Python:

```bash
curl "http://127.0.0.1:8000/usuarios/1/resumos/categorias?inicio=2026-11-01&fim=2026-11-30"
```

Datas vão no formato ISO (`aaaa-mm-dd`) e valores como texto (`"45.90"`),
para não passar por `float`. Dados inválidos são recusados com status 422 e
o nome do campo errado; usuário ou lançamento inexistente devolve 404. Ainda
não há login: o usuário vem na URL, então por enquanto a API é só para uso
local.

### Com Docker (API + PostgreSQL)

Com o [Docker](https://docs.docker.com/get-docker/) instalado, um comando
sobe o PostgreSQL, aplica as migrações e liga a API em
<http://127.0.0.1:8000/docs>:

```bash
docker compose up --build        # Ctrl+C para parar
docker compose down              # remove os containers (os dados ficam)
docker compose down -v           # remove também o volume com os dados
```

As senhas do `docker-compose.yml` são só para uso local. Para trocá-las,
copie o `.env.example` para `.env` e edite (o `.env` não vai para o git).
Para importar CSVs nesse banco, rode o importador dentro do container:

```bash
docker compose cp dados/movimentacoes.csv api:/tmp/
docker compose exec api python importar.py /tmp/movimentacoes.csv --usuario Ana
```

## Formatos de CSV

O formato é reconhecido pela primeira linha (cabeçalho). Arquivos em UTF-8.

**Movimentações** (data no formato `dd/mm/aaaa`, `tipo` é `receita` ou
`despesa`, `conta` é opcional e vale `pessoal` quando falta):

```csv
data,valor,tipo,categoria,descricao,conta
06/09/2026,180.00,despesa,insumos,Farinha acucar e ovos,negocio
01/09/2026,1800.00,receita,salario,Salario mensal,pessoal
```

**Vendas**, no mesmo formato do
[analisador-vendas-csv](https://github.com/Diego-Carvalho-1901/analisador-vendas-csv)
(data `aaaa-mm-dd`; cada linha vira um lançamento do tipo `venda` na conta
`negocio`, com valor = quantidade x preço):

```csv
data da venda, produto, categoria, quantidade vendida, preco unitario
2026-09-05, Bolo de cenoura, Bolos, 4, 45.00
```

## Como testar

Os testes usam [pytest](https://docs.pytest.org/) e o linter é o
[ruff](https://docs.astral.sh/ruff/). Recomenda-se um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

pytest                # roda todos os testes da pasta tests/
ruff check .          # procura erros e más práticas no código
ruff format --check . # confere a formatação (use "ruff format ." para corrigir)
```

Por padrão cada teste usa um SQLite temporário. Para rodar os mesmos
testes num PostgreSQL (o banco de produção), aponte a variável
`FINANCEIRO_TEST_DB_URL` para um banco **só de testes**, porque ele é
apagado a cada teste:

```bash
docker compose up -d banco
docker compose exec banco createdb -U financeiro financeiro_teste
FINANCEIRO_TEST_DB_URL=postgresql+psycopg://financeiro:financeiro@localhost:5432/financeiro_teste pytest
```

Os mesmos comandos rodam no GitHub Actions a cada push na `main` e em todo
pull request ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)),
uma vez com SQLite e outra com PostgreSQL, e a imagem Docker é construída. O selo
no topo deste README mostra se a última execução passou.

## Roteiro

O projeto evolui em itens numerados, cada um com uma issue que descreve o
objetivo, o que fazer, os critérios de pronto e as dependências. Lista
completa: [issues do repositório](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues).

| Item | Entrega | Status |
|---|---|---|
| [01](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/1) | Corrigir os bugs conhecidos do relatório | Concluído |
| [02](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/2) | Refatorar em pacote com `Decimal`, argparse e type hints | Concluído |
| [03](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/3) | CI com GitHub Actions, requirements e .gitignore | Concluído |
| [04](https://github.com/Diego-Carvalho-1901/analisador-vendas-csv/issues/1) | Refatorar e testar o analisador de vendas | Concluído |
| [05](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/4) | Vendas no núcleo: conta negócio/pessoal e lucro | Concluído |
| [06](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/5) | Reescrever o README com a visão do produto | Concluído |
| [07](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/6) | Banco de dados com SQLAlchemy, SQLite e Alembic | Concluído |
| [08](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/7) | Importador de CSV que grava no banco | Concluído |
| [09](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/8) | API FastAPI com CRUD de lançamentos | Concluído |
| [10](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/9) | Endpoints de resumo com agregações em SQL | Concluído |
| [11](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/10) | Testes da API, Dockerfile e docker-compose com PostgreSQL | Em revisão |
| [12](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/11) | Bot de Telegram básico com `/start` | |
| [13](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/12) | Leitor de frases livres | |
| [14](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/13) | Comandos `/resumo`, `/desfazer` e `/meta` | |
| [15](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/14) | Categorização automática por palavras-chave | |
| [16](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/15) | Resumo semanal automático e alerta de meta em 80% | |
| [17](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/16) | Colocar no ar com PostgreSQL e backups | |
| [18](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/17) | Importar extrato CSV de bancos reais | |
| [19](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/18) | Painel web simples com gráficos do mês | |
| [20](https://github.com/Diego-Carvalho-1901/sistema-controle-financeiro/issues/19) | Métricas de uso | |

## Projeto relacionado

[analisador-vendas-csv](https://github.com/Diego-Carvalho-1901/analisador-vendas-csv):
analisa um CSV de vendas (faturamento por produto e por categoria, produto mais vendido).
O CSV de vendas dele é aceito diretamente por este app.

## Autor

Diego Carvalho — estudante de Engenharia da Computação.
GitHub: [@Diego-Carvalho-1901](https://github.com/Diego-Carvalho-1901)
