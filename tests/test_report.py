"""Day-5 Markdown table of the four traces × (task, formal, intent, outcome)."""

from __future__ import annotations

from proofgym.core.report import format_outcome_table
from proofgym.report import evaluate_reference_traces, render_day5_report


def test_outcome_table_lists_all_four_traces() -> None:
    """The report table contains the four reference outcomes in PLAN.md order."""
    verdicts = evaluate_reference_traces()
    table = format_outcome_table(verdicts)
    assert "| Trace" in table
    assert "honest_errand" in table
    assert "registry_heist" in table
    assert "forced_door" in table
    assert "lost_visitor" in table
    assert "honest_success" in table
    assert "formal_exploit" in table
    assert "illegal_shortcut" in table
    assert "honest_failure" in table
    document = render_day5_report(verdicts)
    assert document.startswith("# ProofGym day-5 outcome matrix")
    assert table in document
