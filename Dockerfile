# Imagem da API. Uso: docker compose up (veja docker-compose.yml e o README).
FROM python:3.12-slim

# Não gera arquivos .pyc e mostra os logs na hora, sem buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copia só os requirements primeiro: enquanto eles não mudarem, o Docker
# reaproveita esta camada e não reinstala as dependências a cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini importar.py main.py ./
COPY financeiro ./financeiro
COPY migracoes ./migracoes

# Roda como um usuário comum, não como root.
RUN useradd --create-home app
USER app

EXPOSE 8000

# Aplica as migrações pendentes e sobe a API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn financeiro.api.app:app --host 0.0.0.0 --port 8000"]
