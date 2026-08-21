"""Emit the day-5 four-trace outcome table.

Usage:
    python -m proofgym.report
    python -m proofgym.report --write reports/day5_outcome_matrix.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from proofgym.core.evaluate import evaluate
from proofgym.core.report import format_outcome_table
from proofgym.core.types import Verdict
from proofgym.worlds.museum.constitution import public_constitution
from proofgym.worlds.museum.intent import MuseumIntentOracle
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.traces_io import load_reference_trace, reference_trace_names

REPORT_INTRO = """# ProofGym day-5 outcome matrix

Audit-mode evaluation of the four PLAN.md §4.7 reference traces against the
public constitution (C1–C3) and the hidden intent spec (I1–I3). Certificates
are checker-synthesized Z3 results, not agent-authored proofs.

"""


def evaluate_reference_traces() -> list[Verdict]:
    """Evaluate the four sealed reference traces in report order.

    Returns:
        One verdict per reference trace.
    """
    world = MuseumWorld()
    constitution = public_constitution()
    intent = MuseumIntentOracle()
    verdicts: list[Verdict] = []
    for name in reference_trace_names():
        trace = load_reference_trace(name)
        verdicts.append(evaluate(world, constitution, intent, trace))
    return verdicts


def render_day5_report(verdicts: list[Verdict] | None = None) -> str:
    """Return the Markdown report (intro + table).

    Args:
        verdicts: Precomputed verdicts, or None to evaluate the reference traces.

    Returns:
        Markdown document.
    """
    rows = verdicts if verdicts is not None else evaluate_reference_traces()
    return REPORT_INTRO + format_outcome_table(rows)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Emit the day-5 four-trace outcome table.")
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Also write the Markdown report to this path.",
    )
    args = parser.parse_args(argv)
    document = render_day5_report()
    print(document, end="")
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
