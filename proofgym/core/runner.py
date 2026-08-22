"""Enforce-mode episode runner (PLAN.md D7 / §7).

Illegal actions are rejected, logged with the failing clause id (O1), cost a
turn, and leave the state unchanged. Physics is not applied on a rejection.
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


class EnforceRunner:
    """Deterministic enforce-mode loop for one instance.

    Args:
        world: Physics engine.
        instance: Seeded instance (mission, parameters).
        checker: Constitution checker used as the gate.
        horizon: Episode length. Rejected actions count against it.
        constitution_id: Recorded on the produced trace (informational).
        engine_version: Engine id sealed into the trace.
        meta: Free-form trace metadata (agent id, mission, …).
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
    ) -> None:
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon}")
        self.world = world
        self.instance = instance
        self.checker = checker
        self.horizon = horizon
        self.constitution_id = constitution_id
        self.engine_version = engine_version
        self.meta: dict[str, Any] = dict(meta or {})
        self.state: State = world.initial_state(instance)
        self.steps: list[TraceStep] = []
        self.state_hashes: list[str] = [self.state.state_hash()]
        self.done: bool = False

    @property
    def step_index(self) -> int:
        """Return the number of submitted steps so far."""
        return len(self.steps)

    def submit(self, action: Action) -> GateFeedback:
        """Gate ``action``: accept and apply, or reject, cost a turn, no change.

        Args:
            action: Typed action submitted by the player.

        Returns:
            Gate feedback. On rejection ``failing_clause_id`` is the first
            failing clause in constitution order (O1).

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
        if failing is not None:
            return self._reject(
                action,
                failing_clause_id=failing,
                results=results,
                error=None,
            )
        return self._accept(action, successor, results)

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
    ) -> GateFeedback:
        self.state = successor
        self.steps.append(TraceStep(action=action, executed=True))
        self.state_hashes.append(self.state.state_hash())
        self._tick()
        return GateFeedback(executed=True, failing_clause_id=None, clause_results=results)

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
