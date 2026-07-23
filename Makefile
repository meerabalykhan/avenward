.PHONY: install check test format lint typecheck build compose-check

install:
	cd backend && python -m pip install -e ".[dev]"
	cd frontend && pnpm install

format:
	cd backend && ruff format --check .
	cd frontend && pnpm format

lint:
	cd backend && ruff check .
	cd frontend && pnpm lint

typecheck:
	cd backend && mypy app tests
	cd frontend && pnpm exec tsc -b

test:
	cd backend && pytest
	cd frontend && pnpm test

build:
	cd frontend && pnpm build

compose-check:
	docker compose config --quiet

check: format lint typecheck test build compose-check
