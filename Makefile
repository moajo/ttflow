.PHONY: test
test:
	uv run pytest -vv

.PHONY: coverage
coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=xml

.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .
