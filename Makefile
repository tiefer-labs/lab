# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Commands run inside the locked uv environment. Override with RUN= to use
# an already activated environment, for example: make RUN= test
RUN ?= uv run --frozen

.PHONY: setup lint typecheck test check

setup:
	uv sync --frozen

lint:
	$(RUN) ruff check .
	$(RUN) ruff format --check .

typecheck:
	$(RUN) mypy

test:
	$(RUN) pytest

check: lint typecheck test
