.PHONY: lint
## Run linting
lint:
	pre-commit run --all-files

.PHONY: test
## Run tests
test:
	python -m pytest tests/

.PHONY: install
## Install for development
install:
	pip install -r requirements/ci.txt
	pip install -e .
	pre-commit install || true  # not installed on older python versions

.PHONY: help
## Print Makefile documentation
help:
	@perl -0 -nle 'printf("%-25s - %s\n", "$$2", "$$1") while m/^##\s*([^\r\n]+)\n^([\w-]+):[^=]/gm' $(MAKEFILE_LIST) | sort
.DEFAULT_GOAL := help
