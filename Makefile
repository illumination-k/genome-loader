.PHONY: fmt lint

fmt: ## fmt
	black . && isort . && dprint fmt

lint: ## lint
	black --check . && isort --check . && flake8 . && mypy . && dprint check
