"""Z3-backed checker. Certificates are solver verdicts on concrete transitions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import z3

from proofgym.core.protocols import Clause, World
from proofgym.core.replay import replay
from proofgym.core.types import (
    Action,
    ClauseResult,
    FormalVerdict,
    FormalViolation,
    State,
    Trace,
)


def model_to_dict(model: z3.ModelRef) -> dict[str, str]:
    """Extract a SAT model as a string mapping.

    Args:
        model: Z3 model of a negated clause.

    Returns:
        Declaration name to value, both as strings.
    """
    witness: dict[str, str] = {}
    for decl in model.decls():
        witness[str(decl.name())] = str(model[decl])
    return witness


def formula_holds(phi: z3.BoolRef) -> tuple[bool, dict[str, str] | None]:
    """Return whether ``phi`` is valid of this concrete transition.

    Checking is substitution plus ``solve(¬phi)``: UNSAT means the clause holds;
    a SAT model is the violation witness (PLAN.md §5.1).

    Args:
        phi: Closed Z3 Boolean (already grounded on a concrete ``(s, a, s')``).

    Returns:
        ``(True, None)`` if the clause holds, else ``(False, model)``.

    Raises:
        RuntimeError: If Z3 returns ``unknown``.
    """
    solver = z3.Solver()
    solver.add(z3.Not(phi))
    result = solver.check()
    if result == z3.unsat:
        return True, None
    if result == z3.sat:
        return False, model_to_dict(solver.model())
    raise RuntimeError(f"Z3 returned {result} (expected sat or unsat)")


class Z3Checker:
    """Evaluate a list of :class:`~proofgym.core.protocols.Clause` objects with Z3.

    Args:
        clauses: Constitution clauses. Order is preserved in results.
    """

    def __init__(self, clauses: Sequence[Clause]) -> None:
        self.clauses: tuple[Clause, ...] = tuple(clauses)

    def check_transition(self, s: State, a: Action, s_next: State) -> list[ClauseResult]:
        """Evaluate every clause on one transition.

        Args:
            s: Source state.
            a: Action.
            s_next: Successor state.

        Returns:
            One :class:`~proofgym.core.types.ClauseResult` per clause.
        """
        results: list[ClauseResult] = []
        for clause in self.clauses:
            phi = clause.encode(s, a, s_next)
            ok, model = formula_holds(phi)
            witness: dict[str, Any] | None = None
            if not ok:
                witness = {
                    "clause_id": clause.clause_id,
                    "action": a.to_dict(),
                    "z3_model": model or {},
                    "source_hash": s.state_hash(),
                    "successor_hash": s_next.state_hash(),
                }
            results.append(ClauseResult(clause_id=clause.clause_id, ok=ok, witness=witness))
        return results

    def check_trace(self, world: World, trace: Trace) -> FormalVerdict:
        """Replay ``trace`` and check each executed step.

        Args:
            world: Physics used to reconstruct states.
            trace: Stored episode.

        Returns:
            Trace-level formal verdict with per-step violation witnesses.
        """
        states = replay(world, trace, verify_hashes=True)
        violations: list[FormalViolation] = []
        for index, step in enumerate(trace.steps):
            if not step.executed:
                continue
            results = self.check_transition(states[index], step.action, states[index + 1])
            for result in results:
                if result.ok:
                    continue
                violations.append(
                    FormalViolation(
                        step=index,
                        clause_id=result.clause_id,
                        witness=dict(result.witness or {}),
                    )
                )
        return FormalVerdict(ok=not violations, violations=tuple(violations))
