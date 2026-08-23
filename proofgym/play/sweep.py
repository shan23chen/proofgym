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
        settlement_counts: Settlement label to occurrence count. Empty when
            the cell ran without announced stakes (STAGE5.md).
        confrontation_counts: Confrontation transition label to occurrence
            count (STAGE9.md). Empty when no try in the cell was confronted;
            the implicit denominator difference (confronted tries vs. all
            tries) is why counts are reported against ``tries`` like every
            other rate column.
        reaffirmation_counts: Neutral re-ask transition label to occurrence
            count (STAGE10.md). Separate from the confrontation counts —
            the two arms never pool.
        flagged: Episodes whose workspace integrity was flagged (scored from
            the authoritative rebuild; counted here for eval hygiene).
        adapter_errors: Episodes whose coding CLI exited nonzero with zero
            submitted actions and no filing — absent players, not behavior.
            Counted so live rates can be read against an honest denominator
            (docs/ADAPTER_ROBUSTNESS.md).
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
    settlement_counts: dict[str, int] = field(default_factory=dict)
    confrontation_counts: dict[str, int] = field(default_factory=dict)
    reaffirmation_counts: dict[str, int] = field(default_factory=dict)
    flagged: int = 0
    adapter_errors: int = 0

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

    def settlement_rates(self) -> str:
        """Render settlement counts as ``label n/tries`` fragments, or ``—``."""
        if not self.settlement_counts:
            return "—"
        ordered = sorted(self.settlement_counts.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"{label} {count}/{self.tries}" for label, count in ordered)

    def confrontation_rates(self) -> str:
        """Render confrontation transitions as ``label n/tries``, or ``—``."""
        if not self.confrontation_counts:
            return "—"
        ordered = sorted(self.confrontation_counts.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"{label} {count}/{self.tries}" for label, count in ordered)

    def reaffirmation_rates(self) -> str:
        """Render neutral re-ask transitions as ``label n/tries``, or ``—``."""
        if not self.reaffirmation_counts:
            return "—"
        ordered = sorted(self.reaffirmation_counts.items(), key=lambda item: (-item[1], item[0]))
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
    debrief_stakes: bool = False,
    credit_objective: bool = False,
    self_certify: bool = False,
    confront: bool = False,
    reaffirm: bool = False,
    confront_policy: str | None = None,
    retry_on_empty: bool = False,
    ledger_path: Path | None = None,
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
        debrief_stakes: Announce and record the mission-credit settlement
            (STAGE5.md §3.1). Requires the v2 questionnaire.
        credit_objective: Bind the recorded credit into the player's stated
            engagement (STAGE6.md §4.1). Requires stakes; summaries keep
            objective-bound cells separate.
        self_certify: Settle from the declared claim instead of physics
            (STAGE8.md §3.2). Requires stakes and v4; summaries keep the
            bases separate.
        confront: Arm the confrontation round: a filed misreport triggers a
            re-filing request and the transition is labeled (STAGE9.md).
        reaffirm: Arm the neutral re-ask: every readable filing triggers an
            uninformative re-filing request (STAGE10.md). Mutually exclusive
            with ``confront``.
        confront_policy: Mock-only second-ask control (``recant`` /
            ``double_down`` / ``withdraw`` / ``self_serving``), shared by
            both arms.
        retry_on_empty: Coding-CLI robustness control: retry a try once
            when the CLI exits nonzero having submitted zero actions and
            filed nothing. Off by default; the mock adapter rejects it
            (docs/ADAPTER_ROBUSTNESS.md).
        ledger_path: Engagement-ledger file threaded through the tries
            *sequentially* — try ``n`` plays under the standing tries
            ``1..n-1`` earned, so the sweep is the multi-episode
            experiment (STAGE11.md). One player's record: callers must not
            share a ledger across cells.

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
                debrief_stakes=debrief_stakes,
                credit_objective=credit_objective,
                self_certify=self_certify,
                confront=confront,
                reaffirm=reaffirm,
                confront_policy=confront_policy,
                retry_on_empty=retry_on_empty,
                ledger_path=ledger_path,
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
        # The mission label carries the credit-objective marker, so
        # objective-bound and objective-free runs never pool into one cell
        # (STAGE6.md §4.3).
        key = (record.agent, record.model, record.mission_label(), record.gate)
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
        settlements = Counter(
            record.settlement for record in cell if record.settlement is not None
        )
        confrontations = Counter(
            record.confrontation.transition
            for record in cell
            if record.confrontation is not None
        )
        reaffirmations = Counter(
            record.reaffirmation.transition
            for record in cell
            if record.reaffirmation is not None
        )
        flagged = sum(
            1 for record in cell if record.integrity.get("status") == "flagged"
        )
        adapter_errors = sum(1 for record in cell if record.adapter_error)
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
                settlement_counts=dict(settlements),
                confrontation_counts=dict(confrontations),
                reaffirmation_counts=dict(reaffirmations),
                flagged=flagged,
                adapter_errors=adapter_errors,
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
        "Settlement",
        "Confront",
        "Reaffirm",
        "Flagged",
        "Adapter errors",
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
                summary.settlement_rates(),
                summary.confrontation_rates(),
                summary.reaffirmation_rates(),
                str(summary.flagged),
                str(summary.adapter_errors),
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
