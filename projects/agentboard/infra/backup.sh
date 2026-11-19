#!/bin/sh
set -eu
umask 077

project_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
backup_dir="$project_dir/.local/backups"
mkdir -p "$backup_dir"
timestamp=$(date -u '+%Y%m%dT%H%M%SZ')
temp=$(mktemp "$backup_dir/.agentboard.XXXXXXXX")
trap 'rm -f "$temp"' EXIT HUP INT TERM

cd "$project_dir"
docker compose exec -T db pg_dump --username=agentboard --format=custom agentboard > "$temp"
test -s "$temp"
docker compose exec -T db pg_restore --list < "$temp" > /dev/null
destination="$backup_dir/agentboard-$timestamp.dump"
mv -n "$temp" "$destination"
find "$backup_dir" -type f -name 'agentboard-*.dump' -mtime +29 -delete
printf '%s\n' "$destination"
