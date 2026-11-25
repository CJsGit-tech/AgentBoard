#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p .local
if [ ! -s .local/db_password ]; then
  (set -C; openssl rand -hex 32 > .local/db_password)
fi
if [ -f .local/execution.compose.yaml ]; then
  docker compose -f compose.yaml -f .local/execution.compose.yaml up --build -d --wait
else
  docker compose -f compose.yaml up --build -d --wait
fi
