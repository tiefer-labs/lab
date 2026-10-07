# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Commands run inside the locked uv environment. Override with RUN= to use
# an already activated environment, for example: make RUN= test
RUN ?= uv run --frozen

.PHONY: setup lint typecheck test coverage check smoke requirements shellcheck

# Packages that only torch needs. On CSC Roihu they come with the PyTorch
# module, so hpc/roihu/requirements.txt leaves them out.
TORCH_ONLY = torch triton cuda-bindings cuda-pathfinder cuda-toolkit filelock jinja2 \
	markupsafe mpmath networkx setuptools sympy nvidia-cublas nvidia-cuda-cupti \
	nvidia-cuda-nvrtc nvidia-cuda-runtime nvidia-cudnn-cu13 nvidia-cufft nvidia-cufile \
	nvidia-curand nvidia-cusolver nvidia-cusparse nvidia-cusparselt-cu13 nvidia-nccl-cu13 \
	nvidia-nvjitlink nvidia-nvshmem-cu13 nvidia-nvtx
REQUIREMENTS_ARGS = --frozen --no-dev --no-hashes --no-emit-project \
	$(foreach p,$(TORCH_ONLY),--no-emit-package $(p))

setup:
	uv sync --frozen

lint:
	$(RUN) ruff check .
	$(RUN) ruff format --check .

typecheck:
	$(RUN) mypy

test:
	$(RUN) pytest

# Tests under coverage; fails below the floor in pyproject.toml (fail_under).
coverage:
	$(RUN) coverage run -m pytest
	$(RUN) coverage report

check: lint typecheck test

# The full local smoke pipeline on a tiny subset. SMOKE_SOURCE: auto (real
# CloudSEN12+ patches when reachable, synthetic otherwise), cloudsen12 or synthetic.
SMOKE_SOURCE ?= auto
smoke:
	$(RUN) python -m tiefer_lab.smoke --source $(SMOKE_SOURCE)

requirements:
	uv export $(REQUIREMENTS_ARGS) --output-file hpc/roihu/requirements.txt

# Every shell script under hpc/ and jetson/, including the Slurm batch files.
# CI installs shellcheck from .github/ci-tools/requirements.txt.
SHELL_SCRIPTS = $(shell git ls-files 'hpc/*.sh' 'hpc/*.sbatch' 'jetson/*.sh')
SHELLCHECK ?= shellcheck
shellcheck:
	$(SHELLCHECK) --external-sources --shell=bash $(SHELL_SCRIPTS)
