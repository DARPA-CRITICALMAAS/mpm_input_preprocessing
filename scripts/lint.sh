#!/usr/bin/env bash

set -ex

# mypy --show-error-codes ${PACKAGE}
# black --line-length 119 --check ${PACKAGE}
# isort --line-length 119 --check-only ${PACKAGE}
# flake8

#mypy ${PACKAGE}
ruff check ${PACKAGE} migrations
ruff format ${PACKAGE} migrations --check
