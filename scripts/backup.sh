#!/bin/sh
# Faz um backup do PostgreSQL e apaga os mais antigos que RETER_DIAS.
#
# Uso:
#   FINANCEIRO_DB_URL=postgresql://usuario:senha@host:5432/banco ./scripts/backup.sh
#
# Variáveis opcionais:
#   PASTA_BACKUPS  onde guardar os arquivos (padrão: ./backups)
#   RETER_DIAS     quantos dias de backups manter (padrão: 7)
#
# Para restaurar um backup (CUIDADO: substitui os dados do banco de destino):
#   pg_restore --clean --if-exists --no-owner -d "$URL_DO_BANCO" backups/financeiro-AAAAMMDD-HHMMSS.dump

set -eu

: "${FINANCEIRO_DB_URL:?defina FINANCEIRO_DB_URL com a URL do PostgreSQL}"
PASTA_BACKUPS="${PASTA_BACKUPS:-./backups}"
RETER_DIAS="${RETER_DIAS:-7}"

# O pg_dump não entende o "+psycopg" que o SQLAlchemy usa na URL.
URL=$(printf '%s' "$FINANCEIRO_DB_URL" | sed 's#^postgresql+psycopg://#postgresql://#')

mkdir -p "$PASTA_BACKUPS"
ARQUIVO="$PASTA_BACKUPS/financeiro-$(date -u +%Y%m%d-%H%M%S).dump"

# Formato "custom" (-Fc): comprimido e restaurável com pg_restore.
pg_dump --format=custom --no-owner --file="$ARQUIVO" "$URL"
echo "Backup criado: $ARQUIVO"

find "$PASTA_BACKUPS" -name 'financeiro-*.dump' -mtime +"$RETER_DIAS" -print -delete
