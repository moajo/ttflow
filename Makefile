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

# Serve docs locally with live reload
.PHONY: docs
docs:
	uv run --group docs mkdocs serve

# Build docs for deployment
.PHONY: docs-build
docs-build:
	uv run --group docs mkdocs build --strict

# Regenerate CHANGELOG.md from git history (requires git-cliff: brew install git-cliff)
.PHONY: changelog
changelog:
	git-cliff -o CHANGELOG.md

# Cut a release: regenerate CHANGELOG, commit, and tag (usage: make release VERSION=v0.6.3)
# After this, push with: git push && git push origin <tag>
.PHONY: release
release:
	@test -n "$(VERSION)" || (echo "VERSION is required: make release VERSION=v0.6.3" && exit 1)
	@git diff --quiet && git diff --cached --quiet || (echo "working tree is dirty. commit or stash first." && exit 1)
	git-cliff --tag $(VERSION) -o CHANGELOG.md
	git add CHANGELOG.md
	git commit -m "$(VERSION)"
	git tag $(VERSION)
	@echo ""
	@echo "Tagged $(VERSION). Push with:"
	@echo "  git push && git push origin $(VERSION)"
