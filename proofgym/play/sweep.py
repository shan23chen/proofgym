"""Repeated-try sweeps: turn single-run outcome flips into rates.

Physics is deterministic (D9), so repeated tries of the *mock* adapter always
agree — the sweep machinery is exercised in CI with mocks, while its scientific
use is live coding-CLI players, whose sampling makes outcomes vary across
tries. A sweep never calls a third-party LLM API itself; it only reruns
:func:`proofgym.play.harness.run_episode`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from proofgym.play.harness import run_episode
from proofgym.play.report import RunRecord


@dataclass(frozen=True)
class SweepSummary:
    """Aggregated outcomes for one (agent, model, mission, gate) cell.

    Attributes:
        agent: Adapter id.
        model: Model id, or ``scripted``.
        mission: Mission id.
        gate: Gate mode all tries ran under.
        tries: Number of episodes aggregated.
        outcome_counts: Outcome label to occurrence count.
        mean_steps: Mean submitted steps per episode.
        mean_rejected: Mean gate-rejected steps per episode.
        disclosure_counts: Disclosure label to occurrence count. Empty when
            the cell ran without debriefs.
        flagged: Episodes whose workspace integrity was flagged (scored from
            the authoritative rebuild; counted here for eval hygiene).
    """

    agent: str
    model: str
    mission: str
    gate: str
    tries: int
    outcome_counts: dict[str, int]
    mean_steps: float
    mean_rejected: float
    disclosure_counts: dict[str, int] = field(default_factory=dict)
    flagged: int = 0

    def outcome_rates(self) -> str:
        """Render outcome counts as ``label n/tries`` fragments.

        Returns:
            Comma-joined rates, most frequent first, ties broken by label.
        """
        ordered = sorted(self.outcome_counts.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"{label} {count}/{self.tries}" for label, count in ordered)

    def disclosure_rates(self) -> str:
        """Render disclosure counts as ``label n/tries`` fragments, or ``—``."""
        if not self.disclosure_counts:
            return "—"
        ordered = sorted(self.disclosure_counts.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"{label} {count}/{self.tries}" for label, count in ordered)


def run_sweep(
    *,
    agent: str,
    mission: str,
    tries: int,
    out_dir: Path,
    model: str | None = None,
    script: str | None = None,
    world_name: str = "museum",
    gate: str = "enforce",
    timeout: float | None = None,
    debrief: bool = False,
    debrief_policy: str | None = None,
    debrief_version: int = 1,
) -> list[RunRecord]:
    """Run ``tries`` episodes of one (agent, model, mission, gate) cell.

    Each try writes its artifacts under ``out_dir / try-NN``.

    Args:
        agent: ``mock``, ``opencode``, or ``codex``.
        mission: Mission id.
        tries: Number of episodes (must be positive).
        out_dir: Parent directory for per-try artifact directories.
        model: Model id (required for coding CLIs).
        script: Mock script id override.
        world_name: Catalog world.
        gate: ``enforce`` or ``permissive``.
        timeout: Subprocess timeout for coding CLIs.
        debrief: Ask for and score a post-episode self-report.
        debrief_policy: Mock-only debrief control.
        debrief_version: Questionnaire version (STAGE4.md §3.1).

    Returns:
        One completed run record per try, in order.

    Raises:
        ValueError: If ``tries`` is not positive.
        AdapterNotInstalledError: If a coding CLI is missing from PATH.
        KeyError: If the agent, world, mission, or script is unknown.
    """
    if tries <= 0:
        raise ValueError(f"tries must be positive, got {tries}")
    records: list[RunRecord] = []
    for index in range(1, tries + 1):
        records.append(
            run_episode(
                agent=agent,
                mission=mission,
                model=model,
                script=script,
                world_name=world_name,
                out_dir=out_dir / f"try-{index:02d}",
                timeout=timeout,
                gate=gate,
                debrief=debrief,
                debrief_policy=debrief_policy,
                debrief_version=debrief_version,
            )
        )
    return records


def summarize_records(records: Sequence[RunRecord]) -> list[SweepSummary]:
    """Group records by (agent, model, mission, gate) and aggregate outcomes.

    Args:
        records: Completed evaluations, possibly spanning several cells.

    Returns:
        One summary per cell, in first-appearance order.
    """
    order: list[tuple[str, str, str, str]] = []
    grouped: dict[tuple[str, str, str, str], list[RunRecord]] = {}
    for record in records:
        key = (record.agent, record.model, record.mission, record.gate)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(record)

    summaries: list[SweepSummary] = []
    for key in order:
        cell = grouped[key]
        outcomes = Counter(record.verdict.outcome for record in cell)
        steps = [len(record.trace.steps) for record in cell]
        rejected = [record.rejected_steps() for record in cell]
        disclosures = Counter(
            record.disclosure.label for record in cell if record.disclosure is not None
        )
        flagged = sum(
            1 for record in cell if record.integrity.get("status") == "flagged"
        )
        summaries.append(
            SweepSummary(
                agent=key[0],
                model=key[1],
                mission=key[2],
                gate=key[3],
                tries=len(cell),
                outcome_counts=dict(outcomes),
                mean_steps=sum(steps) / len(cell),
                mean_rejected=sum(rejected) / len(cell),
                disclosure_counts=dict(disclosures),
                flagged=flagged,
            )
        )
    return summaries


def format_sweep_table(summaries: Sequence[SweepSummary]) -> str:
    """Render sweep summaries as a GitHub-flavored Markdown table.

    Args:
        summaries: Aggregated cells in display order.

    Returns:
        Markdown table with outcome rates and step statistics.
    """
    header = (
        "Agent",
        "Model",
        "Mission",
        "Gate",
        "Tries",
        "Outcomes",
        "Steps",
        "Rejected",
        "Disclosure",
        "Flagged",
    )
    rows: list[tuple[str, ...]] = []
    for summary in summaries:
        rows.append(
            (
                summary.agent,
                summary.model,
                summary.mission,
                summary.gate,
                str(summary.tries),
                summary.outcome_rates(),
                f"{summary.mean_steps:.1f}",
                f"{summary.mean_rejected:.1f}",
                summary.disclosure_rates(),
                str(summary.flagged),
            )
        )
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
