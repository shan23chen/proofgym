"""World-agnostic types, protocols, evaluation, and reporting."""

from proofgym.core.evaluate import evaluate, map_outcome
from proofgym.core.protocols import Checker, Clause, IntentOracle, Mission, World
from proofgym.core.serialize import dump_trace, load_trace, trace_from_dict, trace_to_dict
from proofgym.core.types import (
    Action,
    ClauseResult,
    FormalVerdict,
    FormalViolation,
    Instance,
    IntentVerdict,
    IntentViolation,
    State,
    Trace,
    TraceStep,
    Verdict,
)

__all__ = [
    "Action",
    "Checker",
    "Clause",
    "ClauseResult",
    "FormalVerdict",
    "FormalViolation",
    "Instance",
    "IntentOracle",
    "IntentVerdict",
    "IntentViolation",
    "Mission",
    "State",
    "Trace",
    "TraceStep",
    "Verdict",
    "World",
    "dump_trace",
    "evaluate",
    "load_trace",
    "map_outcome",
    "trace_from_dict",
    "trace_to_dict",
]
