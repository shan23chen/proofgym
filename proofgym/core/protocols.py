"""World-agnostic protocols. Domain logic lives in ``worlds/<name>/``."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from proofgym.core.types import (
    Action,
    ClauseResult,
    FormalVerdict,
    Instance,
    IntentVerdict,
    State,
    Trace,
)


@runtime_checkable
class World(Protocol):
    """Operational truth: deterministic physics behind a typed action API."""

    def load_instance(self, instance_id: str) -> Instance:
        """Return the catalogued instance for ``instance_id``.

        Args:
            instance_id: Stable instance identifier.

        Returns:
            The matching instance.

        Raises:
            KeyError: If the identifier is unknown.
        """

    def initial_state(self, instance: Instance) -> State:
        """Return the t=0 snapshot for ``instance``."""

    def available_actions(self, state: State) -> Sequence[Action]:
        """Return physically enabled actions from ``state``, in a stable order."""

    def transition(self, state: State, action: Action) -> State:
        """Apply ``action``. Total and deterministic: failed preconditions are no-ops."""

    def render(self, state: State) -> str:
        """Return a text rendering of ``state``. No UI dependency."""

    def mission_for(self, instance: Instance) -> Mission:
        """Return the mission attached to ``instance``."""


@runtime_checkable
class Clause(Protocol):
    """One public constitution clause that compiles to a Z3 formula.

    The encode interface is the IR (D4). There is no constitution DSL.
    """

    clause_id: str
    text: str
    purpose: str

    def encode(self, s: State, a: Action, s_next: State) -> Any:
        """Return a closed Z3 Boolean claim about this concrete transition.

        Args:
            s: Source state.
            a: Action taken.
            s_next: Successor state.

        Returns:
            A ``z3.BoolRef``. UNSAT of its negation means the clause holds.
        """


@runtime_checkable
class Checker(Protocol):
    """Verifier backend. The pilot wraps Z3 only."""

    def check_transition(self, s: State, a: Action, s_next: State) -> list[ClauseResult]:
        """Evaluate every clause on one transition."""

    def check_trace(self, world: World, trace: Trace) -> FormalVerdict:
        """Replay ``trace`` under ``world`` physics and check each executed step."""


@runtime_checkable
class IntentOracle(Protocol):
    """Hidden intended-legitimacy judge. Deterministic; no model in the loop."""

    def judge(self, world: World, trace: Trace) -> IntentVerdict:
        """Return a trace-level intent verdict."""


@runtime_checkable
class Mission(Protocol):
    """Task-success predicate over the final state."""

    mission_id: str
    horizon: int

    def success(self, final_state: State) -> bool:
        """Return whether the mission is achieved in ``final_state``."""


class Agent(Protocol):
    """Reserved for day 14 scripted agents. Unused on day 5."""

    def act(self, obs: Any, feedback: Any | None) -> Action:
        """Choose a typed action. Not implemented in the day-5 slice."""
