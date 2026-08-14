PYTHON ?= python3
export PYTHONPATH := src

SPECULATIVE_SOURCES := \
	src/forgellm_governance/__init__.py \
	src/forgellm_governance/exact_distribution.py \
	src/forgellm_governance/speculative_decoding.py \
	src/forgellm_governance/speculative_models.py \
	src/forgellm_governance/speculative_exhaustive.py \
	src/forgellm_governance/speculative_greedy.py \
	src/forgellm_governance/speculative_state.py \
	src/forgellm_governance/speculative_trace.py

SPECULATIVE_TESTS := \
	tests/test_exact_distribution.py \
	tests/test_speculative_sampling.py \
	tests/test_speculative_round.py \
	tests/test_target_law.py \
	tests/test_speculative_exhaustive.py \
	tests/test_speculative_greedy.py \
	tests/test_speculative_state.py \
	tests/test_speculative_trace.py \
	tests/test_speculative_adversarial.py

SPECULATIVE_FILES := $(SPECULATIVE_SOURCES) $(SPECULATIVE_TESTS)

.PHONY: validate test lint verify verify-speculative ci mobile-hashes simulate-cache-draft inventory snapshot clean

validate:
	$(PYTHON) scripts/validate_project_state.py --root .
	$(PYTHON) scripts/validate_research_catalog.py --root .
	$(PYTHON) scripts/validate_benchmark.py examples/benchmarks/valid-example.json --root .
	$(PYTHON) scripts/validate_task_packet.py examples/tasks/P0-T02.yaml --root .
	$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T03-repository-hardening.yaml --root .
	$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T04-first-hardware-inventory.yaml --root .
	$(PYTHON) scripts/validate_task_packet.py tasks/closed/P0-T07-cache-aware-placement-simulator.yaml --root .
	$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T08-exact-speculative-decoding.yaml --root .
	$(PYTHON) scripts/validate_topology.py examples/simulations/synthetic-cache-draft-topology.json --root .
	$(PYTHON) scripts/validate_component_profile.py examples/simulations/synthetic-cache-draft-components.json --root .
	$(PYTHON) scripts/hash_mobile_context.py --root .
	bash -n scripts/bootstrap_core_ubuntu.sh

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src scripts tests
	$(PYTHON) -m ruff format --check $(SPECULATIVE_FILES)

verify: validate test

verify-speculative:
	$(PYTHON) -m pytest -q $(SPECULATIVE_TESTS)

ci: lint verify verify-speculative simulate-cache-draft

mobile-hashes:
	$(PYTHON) scripts/hash_mobile_context.py --root .

simulate-cache-draft:
	$(PYTHON) scripts/simulate_placement.py --root . \
	  --topology examples/simulations/synthetic-cache-draft-topology.json \
	  --components examples/simulations/synthetic-cache-draft-components.json \
	  --output artifacts/simulations/synthetic-cache-draft-result.json
	sha256sum -c artifacts/simulations/P0-T07-evidence.sha256

inventory:
	$(PYTHON) scripts/hardware_inventory.py --output artifacts/hardware-local.json

snapshot:
	$(PYTHON) scripts/new_session_snapshot.py --root . --output artifacts/session-snapshot.md

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
