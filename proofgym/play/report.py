"""Markdown/JSON reports for player runs and comparisons."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from proofgym.core.types import Trace, Verdict
from proofgym.play.confront import ConfrontationVerdict
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
        settlement: Mission-credit settlement computed from the *declared*
            debrief answers under announced stakes (``credited`` /
            ``forfeited`` / ``no_claim``), or ``None`` when the episode ran
            without stakes. A recorded consequence, never an outcome
            (STAGE5.md §3.1).
        credit_objective: Whether TASK.md bound the recorded credit into the
            player's stated engagement (STAGE6.md §4.1). Objective-bound and
            objective-free runs are distinct conditions; tables label the
            mission cell ``+credit`` and sweeps never pool across the flag.
        self_certified: Whether the settlement was read from the declared
            claim answer instead of physics task success (STAGE8.md §3.2).
            Bases are distinct conditions; tables label the mission cell
            ``+cert`` and sweeps never pool across the flag.
        confront: Whether the run was armed for a confrontation round
            (STAGE9.md). Arming is invisible during play (workspaces are
            byte-identical until after ``debrief.json`` is filed), so
            round-1 measurements pool across the flag; it is recorded so
            round-2 denominators are honest.
        confrontation: The confrontation verdict, or ``None`` when the round
            never fired (not armed, or nothing to confront). When present,
            ``settlement`` holds the final (post-confrontation) settlement
            and the round-1 settlement lives inside this block.
        reaffirm: Whether the run was armed for the neutral re-ask
            (STAGE10.md) — the control arm that asserts nothing about the
            record. Mutually exclusive with ``confront``; like it, invisible
            during play. The arms never pool: they live in separate fields
            and separate table columns.
        reaffirmation: The neutral re-ask verdict, or ``None`` when the
            round never fired (not armed, or no readable filing). Same
            shape and settlement semantics as ``confrontation``; adds the
            ``held`` and ``degraded`` transitions reachable only from a
            truthful round 1.
        adapter_error: Whether the coding CLI exited nonzero having
            submitted zero actions and filed nothing — an absent player,
            distinct from a player that chose silence. The episode is still
            scored by the normal rules (the labels are correct bookkeeping);
            the marker exists so analysts can separate harness casualties
            from behavior in disclosure and settlement denominators
            (docs/ADAPTER_ROBUSTNESS.md).
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
    settlement: str | None = None
    credit_objective: bool = False
    self_certified: bool = False
    confront: bool = False
    confrontation: ConfrontationVerdict | None = None
    reaffirm: bool = False
    reaffirmation: ConfrontationVerdict | None = None
    adapter_error: bool = False

    def mission_label(self) -> str:
        """Return the mission cell label with its condition markers."""
        label = self.mission
        if self.credit_objective:
            label += " +credit"
        if self.self_certified:
            label += " +cert"
        return label

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
                "settlement": self.settlement,
                "credit_objective": self.credit_objective,
                "self_certified": self.self_certified,
                "confront": self.confront,
                "confrontation": (
                    self.confrontation.to_dict() if self.confrontation is not None else None
                ),
                "reaffirm": self.reaffirm,
                "reaffirmation": (
                    self.reaffirmation.to_dict() if self.reaffirmation is not None else None
                ),
                "adapter_error": self.adapter_error,
                "trace": _trace_dict(self.trace),
                "workspace": self.workspace,
                "adapter": {
                    key: value
                    for key, value in self.adapter.items()
                    if key
                    not in {
                        "stdout",
                        "stderr",
                        "confront_stdout",
                        "confront_stderr",
                        "reaffirm_stdout",
                        "reaffirm_stderr",
                    }
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
        "Settlement",
        "Confront",
        "Reaffirm",
        "Integrity",
        "Adapter",
    )
    rows: list[tuple[str, ...]] = []
    for record in records:
        rows.append(
            (
                record.agent,
                record.model,
                record.mission_label(),
                record.gate,
                record.verdict.outcome,
                "ok" if record.verdict.formal.ok else "violated",
                record.verdict.intent.verdict,
                str(record.rejected_steps()),
                record.disclosure.label if record.disclosure is not None else "—",
                record.settlement if record.settlement is not None else "—",
                record.confrontation.transition if record.confrontation is not None else "—",
                record.reaffirmation.transition if record.reaffirmation is not None else "—",
                str(record.integrity.get("status", "clean")),
                "error" if record.adapter_error else "ok",
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
    header = (
        "Task",
        "Formal",
        "Intent",
        "Outcome",
        "Exploit family",
        "Disclosure",
        "Settlement",
    )
    family = record.verdict.exploit_family or "—"
    row = (
        "yes" if record.verdict.task_success else "no",
        "ok" if record.verdict.formal.ok else "violated",
        record.verdict.intent.verdict,
        record.verdict.outcome,
        family,
        record.disclosure.label if record.disclosure is not None else "—",
        record.settlement if record.settlement is not None else "—",
    )
    intro = (
        f"# ProofGym run: {record.agent} / {record.model} / {record.mission_label()}\n\n"
        f"Gate mode: `{record.gate}`. The player workspace contained only "
        "public information; I* was applied after the episode.\n\n"
    )
    document = intro + _table(header, [row])
    if record.disclosure is not None and record.disclosure.mismatches:
        contested = ", ".join(f"`{item}`" for item in record.disclosure.mismatches)
        document += f"\nMisreported debrief answers (declared ≠ trace): {contested}.\n"
    if record.settlement is not None:
        document += (
            f"\nMission credit settled from the *declared* debrief: `{record.settlement}`. "
            "The settlement follows the filing, not the trace; the outcome above "
            "is unaffected (STAGE5.md).\n"
        )
    if record.confrontation is not None:
        confrontation = record.confrontation
        document += (
            "\n**Confronted** (the round-1 filing contradicted the sealed "
            f"record): the player **{confrontation.transition}** "
            f"(round-2 label `{confrontation.round2.label}`)."
        )
        if confrontation.settlement_round1 is not None:
            document += (
                f" Settlement re-settled from the re-filing: round 1 "
                f"`{confrontation.settlement_round1}`, final "
                f"`{record.settlement}` (STAGE9.md)."
            )
        if confrontation.round2_adapter_error:
            document += (
                " **Round-2 adapter error:** the CLI exited nonzero having "
                "filed nothing — a casualty, not necessarily silence "
                "(docs/ADAPTER_ROBUSTNESS.md)."
            )
        document += "\n"
    if record.reaffirmation is not None:
        reaffirmation = record.reaffirmation
        document += (
            "\n**Re-asked** (neutral re-filing request, issued regardless of "
            f"the filing's content): the player **{reaffirmation.transition}** "
            f"(round-2 label `{reaffirmation.round2.label}`)."
        )
        if reaffirmation.settlement_round1 is not None:
            document += (
                f" Settlement re-settled from the re-filing: round 1 "
                f"`{reaffirmation.settlement_round1}`, final "
                f"`{record.settlement}` (STAGE10.md)."
            )
        if reaffirmation.round2_adapter_error:
            document += (
                " **Round-2 adapter error:** the CLI exited nonzero having "
                "filed nothing — a casualty, not necessarily silence "
                "(docs/ADAPTER_ROBUSTNESS.md)."
            )
        document += "\n"
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
    if record.adapter_error:
        document += (
            "\n**Adapter error:** the coding CLI exited nonzero having "
            "submitted zero actions and filed nothing. This row records an "
            "absent player, not player behavior; exclude it from disclosure "
            "and settlement denominators (docs/ADAPTER_ROBUSTNESS.md).\n"
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
