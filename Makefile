.PHONY: test
test:
	uv run pytest -vv

.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .
