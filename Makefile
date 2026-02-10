.PHONY: up test-ci down

up:
\tdocker compose up -d --build db cortai_api

test-ci: up
\tdocker exec -i cortai_api sh -lc "alembic upgrade head"
\tdocker exec -i cortai_api sh -lc "pytest -q"

down:
\tdocker compose down -v
