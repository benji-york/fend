SHELL := bash
.SHELLFLAGS := -eux -o pipefail -c
.DEFAULT_GOAL := build
.DELETE_ON_ERROR:  # If a recipe to build a file exits with an error, delete the file.
.SUFFIXES:  # Remove the default suffixes which are for compiling C projects.
.NOTPARALLEL:  # Disable use of parallel subprocesses.
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

export COLUMNS ?= 70
seperator ?= $(shell printf %${COLUMNS}s | tr " " "═")

package-version := $(shell \
	grep -m 1 version pyproject.toml \
	| tr -s ' ' \
	| tr -d '"' \
	| tr -d "'" \
	| cut -d' ' -f3)

platform := $(shell python -c 'import sys; print(sys.platform)')

PYTHON_VERSION ?= 3.10

export PIP_DISABLE_PIP_VERSION_CHECK=1
pip-install := ve/bin/pip --no-input install --constraint constraints.txt
pip-check := ve/bin/pip show -q

source_code := src

isort := ve/bin/isort --multi-line=VERTICAL_HANGING_INDENT --trailing-comma --no-sections

########################################################################################
# Build targets
#
# It is acceptable for other targets to implicitly depend on these targets having been
# run.  I.e., it is ok if "make lint" generates an error before "make" has been run.

.PHONY: build
build: ve development-utilities vendor/tree-sitter-make

ve:
	python$(PYTHON_VERSION) -m venv ve
	$(pip-install) -e .

ve/bin/genbadge:
	$(pip-install) genbadge[coverage]

ve/bin/%:
	# Install development utility "$*"
	$(pip-install) $*

# Utilities we use during development.
.PHONY: development-utilities
development-utilities: ve/bin/black
development-utilities: ve/bin/coverage
development-utilities: ve/bin/flake8
development-utilities: ve/bin/genbadge
development-utilities: ve/bin/isort
development-utilities: ve/bin/mypy
development-utilities: ve/bin/pydocstyle
development-utilities: ve/bin/pyinstaller
development-utilities: ve/bin/pylint
development-utilities: ve/bin/twine
development-utilities: ve/bin/wheel

vendor:
	mkdir vendor

vendor/tree-sitter-make: vendor
	git clone git@github.com:benji-york/tree-sitter-make.git vendor/tree-sitter-make
	cd vendor/tree-sitter-make; git switch benji/add-argument-parsing
	ve/bin/python scripts/build_tree_sitter.py

########################################################################################
# Distribution targets

.PHONY: assert-one-dist
assert-one-dist:
	@if [ $$(find dist -name 'manuel-*.tar.gz' | wc -l) != 1 ]; then \
	    echo There must be one and only one distribution file present.; \
	    exit 1; \
	fi

.PHONY: assert-no-unreleased-changes
assert-no-unreleased-changes:
	@if grep unreleased CHANGES.rst > /dev/null; then \
	    echo There must not be any unreleased changes in CHANGES.rst.; \
	    exit 1; \
	fi

.PHONY: assert-version-in-changelog
assert-version-in-changelog:
	@if ! grep $$(ve/bin/python setup.py --version) CHANGES.rst; then \
	    echo The current version number must be mentioned in CHANGES.rst.; \
	    exit 1; \
	fi

.PHONY: assert-matching-versions
assert-matching-versions:
	# verify that the top-most version in the change log matches what is in setup.py
	@env \
	    CHANGE_LOG_VERSION=$$(grep '^[^ ]\+ (20\d\d-\d\d-\d\d)' CHANGES.rst | head -n 1 | cut -d' ' -f1) \
	    SETUP_VERSION=$$(ve/bin/python setup.py --version) \
	    bash -c 'test $$CHANGE_LOG_VERSION = $$SETUP_VERSION'

.PHONY: assert-no-changes
assert-no-changes:
	@if ! output=$$(git status --porcelain) || [ -n "$$output" ]; then \
	    echo There must not be any ucomitted changes.; \
	    exit 1; \
	fi

.PHONY: dist
dist:
	ve/bin/python setup.py sdist

.PHONY: test-dist
test-dist:
	# check to see if the distribution passes the tests
	rm -rf tmp
	mkdir tmp
	tar xzvf $$(find dist -name 'manuel-*.tar.gz') -C tmp
	cd tmp/manuel-* && make && make check
	rm -rf tmp

.PHONY: upload
upload: assert-one-dist
	ve/bin/twine upload --repository=fend dist/fend-*tar.gz

.PHONY: badges
badges:
	ve/bin/python bin/genbadge coverage -i coverage.xml -o badges/coverage-badge.svg

.PHONY: release
ifeq '$(shell git rev-parse --abbrev-ref HEAD)' 'main'
release: clean-dist dist assert-one-dist assert-no-changes upload
	# now that a release has happened, tag the current HEAD as that release
	git tag $(package-version)
	git push origin
	git push origin --tags
else
release:
	@echo Error: must be on master branch to do a release.; exit 1
endif

########################################################################################
# Test and lint targets

.PHONY: pylint
pylint:
	ve/bin/pylint $(source_code) --output-format=colorized

.PHONY: flake8
flake8:
	ve/bin/flake8 $(source_code)

.PHONY: pydocstyle
pydocstyle:
	ve/bin/pydocstyle $(source_code)

.PHONY: mypy
mypy:
	ve/bin/mypy $(source_code) --strict

.PHONY: black-check
black-check:
	ve/bin/black -S $(source_code) --check

.PHONY: isort-check
isort-check:
	$(isort) $(source_code) --diff --check

.PHONY: lint
lint: black-check isort-check

.PHONY: test
test:
	ve/bin/python -m unittest discover src

.PHONY: check
check: test lint

########################################################################################
# Sorce code formatting targets

.PHONY: black
black:
	ve/bin/black -S $(source_code)

.PHONY: isort
isort:
	$(isort) $(source_code)

########################################################################################
# Cleanup targets

.PHONY: clean-%
clean-%:
	rm -rf $*

.PHONY: clean-pycache
clean-pycache:
	find . -name __pycache__ -delete

.PHONY: clean
clean: clean-ve clean-pycache clean-dist clean-vendor
