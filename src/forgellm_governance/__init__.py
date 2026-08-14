"""Governance and reproducibility utilities for the ForgeLLM project."""

from .components import ComponentProfileDocument, load_component_document
from .exact_distribution import (
    DistributionValidationError,
    ExactDistribution,
    RandomSourceError,
    RandomTape,
    UnreachableResidualError,
)
from .simulation import run_simulation
from .speculative_decoding import (
    OneTokenDecision,
    ProposalValidationError,
    SampledRoundRequest,
    SampledRoundResult,
    acceptance_probability,
    decide_one_token,
    exact_bernoulli,
    sample_speculative_round,
)
from .speculative_exhaustive import (
    ExactSequenceLaw,
    LawNormalizationError,
    enumerate_speculative_law,
    enumerate_speculative_round_law,
    enumerate_target_law,
)
from .speculative_greedy import (
    GreedyDecodeError,
    greedy_speculative_decode,
    greedy_target_decode,
)
from .speculative_models import FiniteTableModel, ModelTableError
from .speculative_state import (
    DecoderState,
    RoundTransaction,
    StateInvariantError,
    TransactionStateError,
    begin_round,
    cancel_round,
    commit_round,
    synchronize_pending,
)
from .speculative_trace import build_trace_document, canonical_trace_bytes
from .topology import TopologySnapshot, load_topology
from .validation import (
    ValidationIssue,
    validate_benchmark_file,
    validate_project,
    validate_research_catalogs,
    validate_task_packet_file,
)

__all__ = [
    "ComponentProfileDocument",
    "DecoderState",
    "DistributionValidationError",
    "ExactDistribution",
    "ExactSequenceLaw",
    "FiniteTableModel",
    "GreedyDecodeError",
    "LawNormalizationError",
    "ModelTableError",
    "OneTokenDecision",
    "ProposalValidationError",
    "RandomSourceError",
    "RandomTape",
    "RoundTransaction",
    "SampledRoundRequest",
    "SampledRoundResult",
    "StateInvariantError",
    "TopologySnapshot",
    "TransactionStateError",
    "UnreachableResidualError",
    "ValidationIssue",
    "acceptance_probability",
    "begin_round",
    "build_trace_document",
    "cancel_round",
    "canonical_trace_bytes",
    "commit_round",
    "decide_one_token",
    "enumerate_speculative_law",
    "enumerate_speculative_round_law",
    "enumerate_target_law",
    "exact_bernoulli",
    "greedy_speculative_decode",
    "greedy_target_decode",
    "load_component_document",
    "load_topology",
    "run_simulation",
    "sample_speculative_round",
    "synchronize_pending",
    "validate_benchmark_file",
    "validate_project",
    "validate_research_catalogs",
    "validate_task_packet_file",
]

__version__ = "0.1.0"
