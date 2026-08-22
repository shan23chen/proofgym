"""Gate-mode episode runner (PLAN.md D7 / §7).

Two gate modes:

- ``enforce`` (default, unchanged): illegal actions are rejected, logged with
  the failing clause id (O1), cost a turn, and leave the state unchanged.
  Physics is not applied on a rejection. Every executed step of an
  enforce-mode trace therefore satisfies the constitution by construction, so
  a player behind this gate can never produce an ``illegal_shortcut`` outcome.
- ``permissive``: audit-mode semantics (D7) applied during live play. Physics
  executes regardless of legality; a failing clause is reported in the
  feedback (the alarm rings) and the executed step is sealed into the trace,
  where audit evaluation scores it as a formal violation. This is what makes
  the ``illegal_shortcut`` row reachable for players at all.

The runner is world-agnostic: it talks only to ``World`` and ``Checker``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from proofgym.core.protocols import Checker, World
from proofgym.core.types import (
    ENGINE_VERSION,
    Action,
    ClauseResult,
    GateFeedback,
    Instance,
    State,
    Trace,
    TraceStep,
)


class EpisodeFinishedError(RuntimeError):
    """Raised when a step is submitted after the horizon has been consumed."""


GATE_ENFORCE = "enforce"
GATE_PERMISSIVE = "permissive"
GATE_MODES: frozenset[str] = frozenset({GATE_ENFORCE, GATE_PERMISSIVE})


class EnforceRunner:
    """Deterministic gated loop for one instance.

    Args:
        world: Physics engine.
        instance: Seeded instance (mission, parameters).
        checker: Constitution checker used as the gate.
        horizon: Episode length. Rejected actions count against it.
        constitution_id: Recorded on the produced trace (informational).
        engine_version: Engine id sealed into the trace.
        meta: Free-form trace metadata (agent id, mission, …).
        gate: ``enforce`` (default) rejects constitution-illegal actions;
            ``permissive`` executes them and reports the violation instead
            (audit semantics during live play).

    Raises:
        ValueError: If ``horizon`` is not positive or ``gate`` is unknown.
    """

    def __init__(
        self,
        world: World,
        instance: Instance,
        checker: Checker,
        *,
        horizon: int,
        constitution_id: str,
        engine_version: str = ENGINE_VERSION,
        meta: Mapping[str, Any] | None = None,
        gate: str = GATE_ENFORCE,
    ) -> None:
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon}")
        if gate not in GATE_MODES:
            raise ValueError(f"gate must be one of {sorted(GATE_MODES)}, got {gate!r}")
        self.world = world
        self.instance = instance
        self.checker = checker
        self.horizon = horizon
        self.constitution_id = constitution_id
        self.engine_version = engine_version
        self.meta: dict[str, Any] = dict(meta or {})
        self.gate = gate
        self.state: State = world.initial_state(instance)
        self.steps: list[TraceStep] = []
        self.state_hashes: list[str] = [self.state.state_hash()]
        self.done: bool = False

    @property
    def step_index(self) -> int:
        """Return the number of submitted steps so far."""
        return len(self.steps)

    def submit(self, action: Action) -> GateFeedback:
        """Gate ``action`` according to the runner's gate mode.

        In ``enforce`` mode a constitution-illegal action is rejected: it
        costs a turn and changes nothing. In ``permissive`` mode it executes
        anyway; the feedback still names the first failing clause, so the
        player knows the alarm went off. Malformed actions (unknown type, bad
        arguments) are rejected in both modes.

        Args:
            action: Typed action submitted by the player.

        Returns:
            Gate feedback. ``failing_clause_id`` is the first failing clause
            in constitution order (O1), or ``None`` if every clause held.

        Raises:
            EpisodeFinishedError: If the horizon has already been consumed.
        """
        if self.done:
            raise EpisodeFinishedError(
                f"horizon {self.horizon} reached; no further actions accepted"
            )
        try:
            successor = self.world.transition(self.state, action)
        except (ValueError, KeyError, TypeError) as exc:
            return self._reject(
                action,
                failing_clause_id=None,
                results=(),
                error=str(exc),
            )
        results = tuple(self.checker.check_transition(self.state, action, successor))
        failing = _first_failing_clause(results)
        if failing is not None and self.gate == GATE_ENFORCE:
            return self._reject(
                action,
                failing_clause_id=failing,
                results=results,
                error=None,
            )
        return self._accept(action, successor, results, failing_clause_id=failing)

    def to_trace(self) -> Trace:
        """Seal the episode so far as a replayable trace.

        Returns:
            Trace with integrity hashes. Verdicts are not stored here.
        """
        return Trace(
            instance_id=self.instance.instance_id,
            engine_version=self.engine_version,
            constitution_id=self.constitution_id,
            seed=self.instance.seed,
            steps=tuple(self.steps),
            state_hashes=tuple(self.state_hashes),
            meta=self.meta,
        )

    def restore(
        self,
        *,
        state: State,
        steps: list[TraceStep],
        state_hashes: list[str],
        done: bool,
    ) -> None:
        """Restore a persisted episode (filesystem protocol).

        Args:
            state: Current physics snapshot.
            steps: Already-submitted steps.
            state_hashes: Integrity hashes including the initial state.
            done: Whether the horizon has been consumed.
        """
        if len(state_hashes) != len(steps) + 1:
            raise ValueError("state_hashes must be one longer than steps")
        self.state = state
        self.steps = list(steps)
        self.state_hashes = list(state_hashes)
        self.done = done

    def _accept(
        self,
        action: Action,
        successor: State,
        results: tuple[ClauseResult, ...],
        *,
        failing_clause_id: str | None = None,
    ) -> GateFeedback:
        self.state = successor
        self.steps.append(TraceStep(action=action, executed=True))
        self.state_hashes.append(self.state.state_hash())
        self._tick()
        return GateFeedback(
            executed=True,
            failing_clause_id=failing_clause_id,
            clause_results=results,
        )

    def _reject(
        self,
        action: Action,
        *,
        failing_clause_id: str | None,
        results: tuple[ClauseResult, ...],
        error: str | None,
    ) -> GateFeedback:
        self.steps.append(TraceStep(action=action, executed=False))
        self.state_hashes.append(self.state.state_hash())
        self._tick()
        return GateFeedback(
            executed=False,
            failing_clause_id=failing_clause_id,
            clause_results=results,
            error=error,
        )

    def _tick(self) -> None:
        if len(self.steps) >= self.horizon:
            self.done = True


def _first_failing_clause(results: tuple[ClauseResult, ...]) -> str | None:
    """Return the first failing clause id in constitution order (O1)."""
    for item in results:
        if not item.ok:
            return item.clause_id
    return None
