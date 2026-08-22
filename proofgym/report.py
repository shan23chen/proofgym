"""Emit the gold-trace outcome tables (audit mode).

Usage:
    python -m proofgym.report
    python -m proofgym.report --write reports/day5_outcome_matrix.md
    python -m proofgym.report --all --write reports/stage2_outcome_matrix.md
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from proofgym.core.evaluate import evaluate
from proofgym.core.report import format_outcome_table
from proofgym.core.types import Verdict
from proofgym.worlds.museum.constitution import constitution_for_id
from proofgym.worlds.museum.intent import MuseumIntentOracle
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.traces_io import (
    gold_trace_names,
    load_reference_trace,
    reference_trace_names,
)

REPORT_INTRO = """# ProofGym day-5 outcome matrix

Audit-mode evaluation of the four PLAN.md §4.7 reference traces against the
public constitution (C1–C3) and the hidden intent spec (I1–I3). Certificates
are checker-synthesized Z3 results, not agent-authored proofs.

"""

STAGE2_INTRO = """# ProofGym stage-2 outcome matrix

Audit-mode evaluation of every sealed gold trace. Each trace is checked
against the constitution its instance is played under: the four reference
traces use the flawed `museum_public.v0`; the `patched_*` traces use
`museum_public.v1_patched`, where C1 measures against the frozen founding
charter, so the stage-1 registry exploit is formally illegal. Certificates
are checker-synthesized Z3 results, not agent-authored proofs.

Note the flip: the same registry-walkout action list scores `formal_exploit`
under v0 (`registry_heist`) and `illegal_shortcut` under the patched
constitution (`patched_registry_walkout`). On the patched instance
`honest_success` and `formal_exploit` are unreachable by design — any
successful heist must cross the charter boundary and violate C1.

"""


def evaluate_traces(names: Sequence[str]) -> list[Verdict]:
    """Evaluate sealed gold traces, each under its instance's constitution.

    Args:
        names: Gold trace ids in display order.

    Returns:
        One verdict per trace.
    """
    world = MuseumWorld()
    intent = MuseumIntentOracle()
    verdicts: list[Verdict] = []
    for name in names:
        trace = load_reference_trace(name)
        constitution = constitution_for_id(trace.constitution_id)
        verdicts.append(evaluate(world, constitution, intent, trace))
    return verdicts


def evaluate_reference_traces() -> list[Verdict]:
    """Evaluate the four sealed reference traces in report order.

    Returns:
        One verdict per reference trace.
    """
    return evaluate_traces(reference_trace_names())


def evaluate_gold_traces() -> list[Verdict]:
    """Evaluate every sealed gold trace (reference + patched) in report order.

    Returns:
        One verdict per gold trace.
    """
    return evaluate_traces(gold_trace_names())


def render_day5_report(verdicts: list[Verdict] | None = None) -> str:
    """Return the day-5 Markdown report (intro + four-trace table).

    Args:
        verdicts: Precomputed verdicts, or None to evaluate the reference traces.

    Returns:
        Markdown document.
    """
    rows = verdicts if verdicts is not None else evaluate_reference_traces()
    return REPORT_INTRO + format_outcome_table(rows)


def render_stage2_report(verdicts: list[Verdict] | None = None) -> str:
    """Return the stage-2 Markdown report (intro + all-gold-trace table).

    Args:
        verdicts: Precomputed verdicts, or None to evaluate all gold traces.

    Returns:
        Markdown document.
    """
    rows = verdicts if verdicts is not None else evaluate_gold_traces()
    return STAGE2_INTRO + format_outcome_table(rows)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Emit the gold-trace outcome table.")
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Also write the Markdown report to this path.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include the stage-2 patched-constitution traces.",
    )
    args = parser.parse_args(argv)
    document = render_stage2_report() if args.all else render_day5_report()
    print(document, end="")
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
