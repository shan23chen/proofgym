"""Markdown/JSON reports for player runs and comparisons."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from proofgym.core.types import Trace, Verdict
from proofgym.play.debrief import DisclosureVerdict


def _clean_integrity() -> dict[str, Any]:
    """Default integrity block: nothing to report."""
    return {"status": "clean", "events": []}


@dataclass(frozen=True)
class RunRecord:
    """One (agent, model, mission, gate) evaluation.

    Attributes:
        agent: Adapter id (``mock``, ``opencode``, ``codex``).
        model: Model id, or ``scripted`` for the mock adapter.
        mission: Mission id.
        gate: Gate mode the episode ran under (``enforce`` or ``permissive``).
        verdict: Four-outcome evaluation (uses hidden I*, post-episode).
        trace: Reconstructed gated trace.
        workspace: Player workspace used during the episode.
        adapter: Adapter metadata (argv, return code, …).
        disclosure: Deterministic debrief score, or ``None`` when the episode
            ran without a debrief request.
        integrity: Workspace-integrity block: ``status`` is ``clean`` or
            ``flagged``; ``events`` records mirror tampering/deletion seen
            during play and any divergence between the on-disk episode and
            the harness's in-process authoritative rebuild. Scoring always
            uses the rebuild, so a flagged run is *scored correctly* — the
            flag marks the artifact for eval-hygiene review.
    """

    agent: str
    model: str
    mission: str
    verdict: Verdict
    trace: Trace
    workspace: str
    adapter: dict[str, Any]
    gate: str = "enforce"
    disclosure: DisclosureVerdict | None = None
    integrity: dict[str, Any] = field(default_factory=_clean_integrity)

    def rejected_steps(self) -> int:
        """Return how many submitted actions the gate rejected (enforce mode)."""
        return sum(1 for step in self.trace.steps if not step.executed)

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON report: axes, outcome, family, plus the trace."""
        payload = self.verdict.to_dict()
        payload.update(
            {
                "agent": self.agent,
                "model": self.model,
                "mission": self.mission,
                "gate": self.gate,
                "task_success": self.verdict.task_success,
                "formal": self.verdict.formal.to_dict(),
                "intent": self.verdict.intent.to_dict(),
                "outcome": self.verdict.outcome,
                "exploit_family": self.verdict.exploit_family,
                "rejected_steps": self.rejected_steps(),
                "disclosure": self.disclosure.to_dict() if self.disclosure is not None else None,
                "integrity": dict(self.integrity),
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
        GitHub-flavored Markdown with columns agent, model, mission, gate,
        outcome, formal, intent, rejected steps, disclosure.
    """
    header = (
        "Agent",
        "Model",
        "Mission",
        "Gate",
        "Outcome",
        "Formal",
        "Intent",
        "Rejected",
        "Disclosure",
        "Integrity",
    )
    rows: list[tuple[str, ...]] = []
    for record in records:
        rows.append(
            (
                record.agent,
                record.model,
                record.mission,
                record.gate,
                record.verdict.outcome,
                "ok" if record.verdict.formal.ok else "violated",
                record.verdict.intent.verdict,
                str(record.rejected_steps()),
                record.disclosure.label if record.disclosure is not None else "—",
                str(record.integrity.get("status", "clean")),
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
    header = ("Task", "Formal", "Intent", "Outcome", "Exploit family", "Disclosure")
    family = record.verdict.exploit_family or "—"
    row = (
        "yes" if record.verdict.task_success else "no",
        "ok" if record.verdict.formal.ok else "violated",
        record.verdict.intent.verdict,
        record.verdict.outcome,
        family,
        record.disclosure.label if record.disclosure is not None else "—",
    )
    intro = (
        f"# ProofGym run: {record.agent} / {record.model} / {record.mission}\n\n"
        f"Gate mode: `{record.gate}`. The player workspace contained only "
        "public information; I* was applied after the episode.\n\n"
    )
    document = intro + _table(header, [row])
    if record.disclosure is not None and record.disclosure.mismatches:
        contested = ", ".join(f"`{item}`" for item in record.disclosure.mismatches)
        document += f"\nMisreported debrief answers (declared ≠ trace): {contested}.\n"
    if record.integrity.get("status") == "flagged":
        kinds = ", ".join(
            sorted({str(event.get("kind", "?")) for event in record.integrity.get("events", [])})
        )
        document += (
            "\n**Workspace integrity: flagged** "
            f"({kinds}). The verdict above was scored from the harness's "
            "authoritative in-process replay, not from the on-disk record; "
            "archive this run for eval-hygiene review.\n"
        )
    return document


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
