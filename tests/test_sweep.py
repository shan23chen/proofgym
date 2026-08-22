"""Sweep helper: repeated tries become outcome rates. Mock-only, no LLM calls."""

from __future__ import annotations

from pathlib import Path

import pytest

from proofgym.cli import main as cli_main
from proofgym.play.sweep import format_sweep_table, run_sweep, summarize_records


def test_run_sweep_mock_heist_rates_are_deterministic(tmp_path: Path) -> None:
    """n=3 mock heist tries agree (D9) and aggregate to a 3/3 rate."""
    records = run_sweep(
        agent="mock",
        mission="heist",
        tries=3,
        out_dir=tmp_path / "sweep",
    )
    assert len(records) == 3
    assert {record.verdict.outcome for record in records} == {"formal_exploit"}
    for index in (1, 2, 3):
        assert (tmp_path / "sweep" / f"try-{index:02d}" / "verdict.json").is_file()

    summaries = summarize_records(records)
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.tries == 3
    assert summary.outcome_counts == {"formal_exploit": 3}
    assert summary.outcome_rates() == "formal_exploit 3/3"
    assert summary.mean_rejected == 0.0
    assert summary.mean_steps == 16.0


def test_run_sweep_rejects_nonpositive_tries(tmp_path: Path) -> None:
    """tries must be positive."""
    with pytest.raises(ValueError, match="tries"):
        run_sweep(agent="mock", mission="heist", tries=0, out_dir=tmp_path)


def test_summarize_records_groups_cells_and_mixed_outcomes(tmp_path: Path) -> None:
    """Cells are keyed by (agent, model, mission, gate); mixed outcomes rank."""
    records = run_sweep(
        agent="mock",
        mission="heist_patched",
        tries=2,
        out_dir=tmp_path / "enforce",
    )
    records += run_sweep(
        agent="mock",
        mission="heist_patched",
        tries=1,
        gate="permissive",
        out_dir=tmp_path / "permissive",
    )
    summaries = summarize_records(records)
    assert [(s.gate, s.tries) for s in summaries] == [("enforce", 2), ("permissive", 1)]
    assert summaries[0].outcome_counts == {"honest_failure": 2}
    assert summaries[0].mean_rejected == 1.0
    assert summaries[1].outcome_counts == {"illegal_shortcut": 1}
    table = format_sweep_table(summaries)
    assert "honest_failure 2/2" in table
    assert "illegal_shortcut 1/1" in table
    assert "permissive" in table


def test_cli_sweep_writes_rate_table(tmp_path: Path) -> None:
    """``python -m proofgym sweep`` writes sweep.md with per-cell rates."""
    out = tmp_path / "sweep"
    code = cli_main(
        [
            "sweep",
            "--agent",
            "mock",
            "--mission",
            "heist",
            "--mission",
            "heist_patched",
            "--n",
            "3",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    table = (out / "sweep.md").read_text(encoding="utf-8")
    assert "formal_exploit 3/3" in table
    assert "honest_failure 3/3" in table
    assert (out / "mock-scripted-heist" / "try-03" / "trace.json").is_file()
    assert (out / "mock-scripted-heist_patched" / "try-01" / "report.md").is_file()


def test_cli_sweep_unknown_mission_fails_cleanly(tmp_path: Path) -> None:
    """A bad mission id returns exit code 2, not a traceback."""
    code = cli_main(
        ["sweep", "--agent", "mock", "--mission", "vault_party", "--out", str(tmp_path / "s")]
    )
    assert code == 2
