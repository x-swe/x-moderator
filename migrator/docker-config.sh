#!/bin/sh

# Default variables
export NETWORK_NAME=${NETWORK_NAME:-xmod-net}
export IMAGE_NAME=${IMAGE_NAME:-xmod-migrator}
export DB_HOST=${DB_HOST:-xmod-mariadb-1}
export DB_PORT=${DB_PORT:-3306}
export DB_USER=${DB_USER:-xmod}
export DB_PASSWORD=${DB_PASSWORD:-password}
export DB_NAME=${DB_NAME:-xmod}

# Load from .env if present
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

# Validate variables
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo "Error: Missing required environment variables (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)" >&2
    exit 1
fi