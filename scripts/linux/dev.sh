#!/usr/bin/env sh
set -eu

action="${1:-up}"
project_root="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$project_root"

case "$action" in
  up)
    [ -f .env ] || cp .env.example .env
    docker compose up --build
    ;;
  down) docker compose down ;;
  format)
    docker run --rm -v "$project_root/backend:/workspace" -w /workspace \
      python:3.12-slim sh -c \
      "pip install -e '.[dev]' && ruff format . && ruff check . --fix"
    docker run --rm -e CI=true -v "$project_root/frontend:/workspace" \
      -w /workspace node:22-alpine sh -c \
      "corepack enable && pnpm install --no-frozen-lockfile \
       --store-dir /tmp/pnpm-store && pnpm format:write"
    ;;
  test)
    docker run --rm -v "$project_root/backend:/workspace" -w /workspace \
      python:3.12-slim sh -c "pip install -e '.[dev]' && pytest"
    docker build --target test --tag avenward-frontend-test \
      --file frontend/Dockerfile .
    docker run --rm -e CI=true avenward-frontend-test pnpm test
    ;;
  check)
    docker compose config --quiet
    docker run --rm -v "$project_root/backend:/workspace" -w /workspace \
      python:3.12-slim sh -c \
      "pip install -e '.[dev]' && ruff format --check . && ruff check . && \
       mypy app tests && pytest"
    docker build --target test --tag avenward-frontend-check \
      --file frontend/Dockerfile .
    docker run --rm -e CI=true avenward-frontend-check sh -c \
      "failures=0; pnpm format || failures=1; pnpm lint || failures=1; \
       pnpm exec tsc -b || failures=1; pnpm test || failures=1; \
       pnpm build || failures=1; exit \$failures"
    ;;
  *) echo "Usage: $0 {up|down|format|test|check}" >&2; exit 2 ;;
esac
