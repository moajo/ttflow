# Run all checks (autofix + lint + test) — same as CI
.PHONY: all
all: fmt lint test

# Run tests with verbose output
.PHONY: test
test:
	uv run pytest -vv

# Run tests with coverage report
.PHONY: coverage
coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=xml

# Auto-format code and apply safe lint fixes
.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check --fix .

# Check for lint errors and formatting issues (no modifications)
.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .
