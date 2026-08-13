PYTHON ?= python3
export PYTHONPATH := src

.PHONY: validate test lint verify ci mobile-hashes inventory snapshot clean

validate:
	$(PYTHON) scripts/validate_project_state.py --root .
	$(PYTHON) scripts/validate_research_catalog.py --root .
	$(PYTHON) scripts/validate_benchmark.py examples/benchmarks/valid-example.json --root .
	$(PYTHON) scripts/validate_task_packet.py examples/tasks/P0-T02.yaml --root .
	$(PYTHON) scripts/hash_mobile_context.py --root .
	bash -n scripts/bootstrap_core_ubuntu.sh

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src scripts tests

verify: validate test

ci: lint verify

mobile-hashes:
	$(PYTHON) scripts/hash_mobile_context.py --root .

inventory:
	$(PYTHON) scripts/hardware_inventory.py --output artifacts/hardware-local.json

snapshot:
	$(PYTHON) scripts/new_session_snapshot.py --root . --output artifacts/session-snapshot.md

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
