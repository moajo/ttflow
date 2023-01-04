.PHONY: test
test:
	poetry run pytest -vv

.PHONY: fmt
fmt:
	poetry run pysen run format && poetry run pysen run lint
