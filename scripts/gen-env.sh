#!/usr/bin/env bash
# Creates .env from .env.example with a fresh random value for every __GENERATE__ placeholder.
# Does nothing if .env already exists.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  exit 0
fi
umask 077
while IFS= read -r line; do
  while [[ "$line" == *__GENERATE__* ]]; do
    secret="$(od -An -tx1 -N32 /dev/urandom | tr -d ' \n')"
    line="${line/__GENERATE__/$secret}"
  done
  printf '%s\n' "$line"
done < .env.example > .env
echo "Created .env with generated secrets."
