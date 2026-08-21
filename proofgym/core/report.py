"""Markdown reporting for verdict tables."""

from __future__ import annotations

from collections.abc import Sequence

from proofgym.core.types import Verdict

_HEADER = ("Trace", "Task", "Formal", "Intent", "Outcome")


def format_outcome_table(verdicts: Sequence[Verdict]) -> str:
    """Render verdicts as a GitHub-flavored Markdown table.

    Args:
        verdicts: Already-evaluated traces, in display order.

    Returns:
        A Markdown table with columns trace, task, formal, intent, outcome.
    """
    rows: list[tuple[str, str, str, str, str]] = []
    for verdict in verdicts:
        rows.append(
            (
                verdict.trace,
                "yes" if verdict.task_success else "no",
                "ok" if verdict.formal.ok else "violated",
                verdict.intent.verdict,
                verdict.outcome,
            )
        )
    widths = [len(title) for title in _HEADER]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _fmt(cells: Sequence[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    lines = [
        _fmt(_HEADER),
        "| " + " | ".join("-" * widths[i] for i in range(len(_HEADER))) + " |",
    ]
    lines.extend(_fmt(row) for row in rows)
    return "\n".join(lines) + "\n"
