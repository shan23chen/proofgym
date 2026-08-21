"""Core dataclasses: states, actions, traces, and verdicts.

``core`` stores world snapshots as opaque JSON-ready payloads. Worlds interpret
the payload; this module only hashes and round-trips it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

ENGINE_VERSION = "0.1.0"

IntentLabel = Literal["legitimate", "violation", "ambiguous"]
Outcome = Literal[
    "honest_success",
    "formal_exploit",
    "illegal_shortcut",
    "honest_failure",
    "other",
]


def canonical_json(value: Any) -> str:
    """Serialize ``value`` to a deterministic JSON string.

    Args:
        value: A JSON-serializable object.

    Returns:
        Compact JSON with sorted keys.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class State:
    """Hashable, serializable world snapshot.

    Attributes:
        payload: World-specific JSON-ready mapping. ``core`` does not interpret it.
    """

    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", json.loads(canonical_json(dict(self.payload))))

    def state_hash(self) -> str:
        """Return a deterministic SHA-256 hex digest of the canonical payload.

        Returns:
            64-character hex digest.
        """
        blob = canonical_json(self.payload)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Action:
    """Typed finite action. Worlds define the legal ``type`` vocabulary.

    Attributes:
        type: Action type name (for example ``move`` or ``amend_registry``).
        args: Enumerable parameter map (rooms, doors, objects, ops).
    """

    type: str
    args: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "args", json.loads(canonical_json(dict(self.args))))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of this action."""
        return {"type": self.type, "args": dict(self.args)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Action:
        """Build an action from a ``{type, args}`` mapping.

        Args:
            data: Serialized action.

        Returns:
            Parsed action.

        Raises:
            KeyError: If ``type`` is missing.
            TypeError: If ``type`` is not a string.
        """
        action_type = data["type"]
        if not isinstance(action_type, str):
            raise TypeError(f"action type must be a string, got {type(action_type)!r}")
        args = data.get("args", {})
        if args is None:
            args = {}
        if not isinstance(args, Mapping):
            raise TypeError(f"action args must be a mapping, got {type(args)!r}")
        return cls(type=action_type, args=args)


@dataclass(frozen=True)
class TraceStep:
    """One recorded action in a trace.

    Attributes:
        action: The submitted action.
        executed: ``False`` marks an enforce-mode rejection (no state change).
            Day-5 traces are audit-mode and use ``True``.
    """

    action: Action
    executed: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of this step."""
        return {"action": self.action.to_dict(), "executed": self.executed}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TraceStep:
        """Build a step from a serialized mapping."""
        return cls(
            action=Action.from_dict(data["action"]),
            executed=bool(data.get("executed", True)),
        )


@dataclass(frozen=True)
class Trace:
    """Replayable episode record. Verdicts are derived, never stored here.

    Attributes:
        instance_id: World instance identifier.
        engine_version: Engine that produced or last sealed the trace.
        constitution_id: Public constitution identifier (informational).
        seed: Instance seed. Physics itself is not random.
        steps: Submitted actions in order.
        state_hashes: Integrity hashes, one for the initial state and one after
            each step. Recomputed from physics on evaluation (D9).
        meta: Free-form metadata (agent id, trace name, notes).
    """

    instance_id: str
    engine_version: str
    constitution_id: str
    seed: int
    steps: tuple[TraceStep, ...]
    state_hashes: tuple[str, ...] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "state_hashes", tuple(self.state_hashes))
        object.__setattr__(self, "meta", json.loads(canonical_json(dict(self.meta))))


@dataclass(frozen=True)
class Instance:
    """A seeded world configuration.

    Attributes:
        instance_id: Stable identifier (for example ``museum.v0.heist.base``).
        seed: Selects instance parameters only; physics is deterministic.
        mission_id: Mission evaluated against the final state.
        parameters: World-specific JSON-ready configuration. ``core`` does not
            interpret keys such as ``protected_rooms`` or ``exploit_family``.
    """

    instance_id: str
    seed: int
    mission_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", json.loads(canonical_json(dict(self.parameters))))


@dataclass(frozen=True)
class ClauseResult:
    """Per-clause result for one transition.

    Attributes:
        clause_id: Public clause identifier.
        ok: Whether the clause held of this transition.
        witness: SAT-model facts and concrete transition context on violation.
    """

    clause_id: str
    ok: bool
    witness: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class FormalViolation:
    """A constitution violation at a particular step.

    Attributes:
        step: Zero-based index into ``trace.steps``.
        clause_id: Failing clause.
        witness: Checker-synthesized violation witness.
    """

    step: int
    clause_id: str
    witness: Mapping[str, Any]


@dataclass(frozen=True)
class FormalVerdict:
    """Trace-level formal legality.

    Attributes:
        ok: True when no clause failed on any executed step.
        violations: Failing (step, clause, witness) triples.
    """

    ok: bool
    violations: tuple[FormalViolation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return {
            "ok": self.ok,
            "violations": [
                {"step": v.step, "clause_id": v.clause_id, "witness": dict(v.witness)}
                for v in self.violations
            ],
        }


@dataclass(frozen=True)
class IntentViolation:
    """An intent-rule failure at a particular step or state.

    Attributes:
        step: Zero-based step index. For state-invariant rules this is the
            index of the action that produced the offending successor, or
            ``-1`` if the initial state already fails.
        rule_id: Intent rule identifier (``I1``, ``I2``, ``I3``).
        rationale: Written rationale for the failing rule.
    """

    step: int
    rule_id: str
    rationale: str


@dataclass(frozen=True)
class IntentVerdict:
    """Trace-level intended legitimacy.

    ``ambiguous`` is reserved (O2) and is not returned by pilot missions.

    Attributes:
        verdict: ``legitimate``, ``violation``, or ``ambiguous``.
        violations: Failing rules.
        rationale: Joined rationales of failing rules, or a success summary.
    """

    verdict: IntentLabel
    violations: tuple[IntentViolation, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return {
            "verdict": self.verdict,
            "violations": [
                {"step": v.step, "rule_id": v.rule_id, "rationale": v.rationale}
                for v in self.violations
            ],
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class Verdict:
    """Derived evaluation of a trace. Never stored inside the trace.

    Attributes:
        trace: Trace label (filename or ``meta.trace_id``).
        task_success: Mission success at the final state.
        formal: Constitution verdict.
        intent: Hidden intent verdict.
        outcome: One of the four matrix rows, or ``other``.
        exploit_family: Instance tag, set on ``formal_exploit`` (O5).
    """

    trace: str
    task_success: bool
    formal: FormalVerdict
    intent: IntentVerdict
    outcome: Outcome
    exploit_family: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation matching PLAN.md §5.2."""
        return {
            "trace": self.trace,
            "task_success": self.task_success,
            "formal": self.formal.to_dict(),
            "intent": self.intent.to_dict(),
            "outcome": self.outcome,
            "exploit_family": self.exploit_family,
        }
