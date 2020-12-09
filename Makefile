.PHONY: lint
## Run linting
lint:
	pre-commit run --all-files

.PHONY: test
## Run tests
test:
	python -m pytest tests/

install:
	pip install -r requirements/ci.txt
	pip install -e .
	pre-commit install

all: clean lint test
