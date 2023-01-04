.PHONY: test
test:
	poetry run pytest -vv

.PHONY: fmt
fmt:
	poetry run pysen run format

.PHONY: lint
lint:
	poetry run pysen run lint
