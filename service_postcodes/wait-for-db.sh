#!/bin/sh

echo "Esperando base de datos"

: "${DB_HOST:?Necesitas definir DB_HOST}"
: "${DB_PORT:?Necesitas definir DB_PORT}"
: "${DB_USER:?Necesitas definir DB_USER}"

MAX_TRIES=60
TRIES=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  TRIES=$((TRIES+1))
  if [ $TRIES -ge $MAX_TRIES ]; then
    echo "No se pudo conectar a la base de datos. $MAX_TRIES intentos."
    exit 1
  fi
  sleep 1
done

echo "Base de datos esta disponible. Iniciando!"

exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8001}"
