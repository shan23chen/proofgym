"""ProofGym: proof-checked actions, then a hidden intent oracle."""

from proofgym.core.evaluate import evaluate
from proofgym.core.types import (
    Action,
    FormalVerdict,
    IntentVerdict,
    State,
    Trace,
    Verdict,
)

__version__ = "0.1.0"

__all__ = [
    "Action",
    "FormalVerdict",
    "IntentVerdict",
    "State",
    "Trace",
    "Verdict",
    "evaluate",
    "__version__",
]
