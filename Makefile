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

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage, and Python file artifacts

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

docs: ## generate Sphinx HTML documentation, including API docs
	# TODO: Verify if this even works.
	rm -f docs/source/layabout.rst
	rm -f docs/source/module.rst
	sphinx-apidoc -f -o docs/source layabout.py
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

lint: ## check style with flake8
	flake8 $(SRC) tests

type-check: ## run static analysis with mypy
	mypy --ignore-missing-imports $(SRC)

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
	$(eval VERSION := "v$(shell sed -rn "s/__version__ = [\'\"](.*)[\'\"]/\1/p" $(VERSION_FILE))")
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push origin $(VERSION)

release: tag-release ## package and upload for public release
	# TODO: Use twine maybe?
	@echo Honestly, what should this do?

dist: clean ## build source and wheel packages
	python setup.py sdist bdist_wheel

install: clean ## install the package into the active Python's site-packages
	python setup.py install
