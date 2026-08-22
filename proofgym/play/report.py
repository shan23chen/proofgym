"""Markdown/JSON reports for player runs and comparisons."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from proofgym.core.types import Trace, Verdict


@dataclass(frozen=True)
class RunRecord:
    """One (agent, model, mission) evaluation.

    Attributes:
        agent: Adapter id (``mock``, ``opencode``, ``codex``).
        model: Model id, or ``scripted`` for the mock adapter.
        mission: Mission id.
        verdict: Four-outcome evaluation (uses hidden I*, post-episode).
        trace: Reconstructed enforce-mode trace.
        workspace: Player workspace used during the episode.
        adapter: Adapter metadata (argv, return code, …).
    """

    agent: str
    model: str
    mission: str
    verdict: Verdict
    trace: Trace
    workspace: str
    adapter: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON report: axes, outcome, family, plus the trace."""
        payload = self.verdict.to_dict()
        payload.update(
            {
                "agent": self.agent,
                "model": self.model,
                "mission": self.mission,
                "task_success": self.verdict.task_success,
                "formal": self.verdict.formal.to_dict(),
                "intent": self.verdict.intent.to_dict(),
                "outcome": self.verdict.outcome,
                "exploit_family": self.verdict.exploit_family,
                "trace": _trace_dict(self.trace),
                "workspace": self.workspace,
                "adapter": {
                    key: value
                    for key, value in self.adapter.items()
                    if key not in {"stdout", "stderr"}
                },
            }
        )
        return payload


def format_verdict_table(records: Sequence[RunRecord]) -> str:
    """Render a Markdown table of player runs.

    Args:
        records: Completed evaluations.

    Returns:
        GitHub-flavored Markdown with columns agent, model, mission, outcome,
        formal, intent.
    """
    header = ("Agent", "Model", "Mission", "Outcome", "Formal", "Intent")
    rows: list[tuple[str, ...]] = []
    for record in records:
        rows.append(
            (
                record.agent,
                record.model,
                record.mission,
                record.verdict.outcome,
                "ok" if record.verdict.formal.ok else "violated",
                record.verdict.intent.verdict,
            )
        )
    return _table(header, rows)


def format_one_row_report(record: RunRecord) -> str:
    """Render a one-row Markdown report for a single run.

    Args:
        record: Completed evaluation.

    Returns:
        Markdown with task / formal / intent / outcome / exploit_family.
    """
    header = ("Task", "Formal", "Intent", "Outcome", "Exploit family")
    family = record.verdict.exploit_family or "—"
    row = (
        "yes" if record.verdict.task_success else "no",
        "ok" if record.verdict.formal.ok else "violated",
        record.verdict.intent.verdict,
        record.verdict.outcome,
        family,
    )
    intro = (
        f"# ProofGym run: {record.agent} / {record.model} / {record.mission}\n\n"
        "Enforce-mode evaluation. The player workspace contained only public "
        "information; I* was applied after the episode.\n\n"
    )
    return intro + _table(header, [row])


def _trace_dict(trace: Trace) -> dict[str, Any]:
    from proofgym.core.serialize import trace_to_dict

    return trace_to_dict(trace)


def _table(header: tuple[str, ...], rows: Sequence[tuple[str, ...]]) -> str:
    widths = [len(title) for title in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _fmt(cells: Sequence[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    lines = [
        _fmt(header),
        "| " + " | ".join("-" * widths[i] for i in range(len(header))) + " |",
    ]
    lines.extend(_fmt(row) for row in rows)
    return "\n".join(lines) + "\n"
