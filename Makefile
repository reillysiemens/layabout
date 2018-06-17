# This Makefile owes most of its targets and structure to @audreyr's
# cookiecutter-pypackage project. The source can be found at
# https://github.com/audreyr/cookiecutter-pypackage.

.PHONY: clean clean-build clean-pyc clean-test docs lint type-check test
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([0-9a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print(f"{target:20} {help}")
endef
export PRINT_HELP_PYSCRIPT

SRC = layabout.py

help: ## show Makefile help (default target)
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-docs ## remove all build, test, coverage, docs, and Python file artifacts

clean-build: ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage

clean-docs:  ## remove docs artifacts
	$(MAKE) -C docs clean

docs: clean-docs ## generate Sphinx HTML documentation, including API docs
	$(MAKE) -C docs html

lint: ## check style with flake8
	flake8 $(SRC) tests

type-check: ## run static analysis with mypy
	mypy --ignore-missing-imports --disallow-untyped-defs $(SRC)

test: ## run tests with pytest
	pytest

coverage: ## check code coverage
	coverage run --source layabout.py -m pytest
	coverage report -m
	coverage html

check-origin-remote:
	# A remote named origin MUST exist.
	@git remote show origin

tag-release: check-origin-remote
	# This doesn't have help text because it's intended to be a release helper.
	$(eval VERSION := "v$(shell sed -rn "s/__version__ = [\'\"](.*)[\'\"]/\1/p" $(SRC))")
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push origin $(VERSION)

release: dist tag-release ## package and upload for public release
	gpg --detach-sign -a dist/layabout-*.tar.gz
	twine upload dist/*

dist: clean ## build source and wheel packages
	python3 setup.py sdist bdist_wheel

install: clean ## install the package into the active Python's site-packages
	python3 setup.py install
