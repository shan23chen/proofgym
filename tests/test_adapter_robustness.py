"""Adapter robustness: zero-step CLI casualties are marked and retryable.

Motivated by the live "zero-step, exit code 1" runs (STAGE6.md §1's adapter
casualty; recurrent for several models per the operators' log). An *adapter
error* is a coding CLI that exits nonzero having submitted zero actions and
filed nothing — an absent player. It is distinct from player silence (exit
code 0, nothing submitted), from a refusal that files a debrief, and from a
crash after play (steps exist; the return code is already recorded).
"""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from proofgym.act import main as act_main
from proofgym.cli import main as cli_main
from proofgym.play.harness import load_run_record, run_episode
from proofgym.play.report import format_verdict_table
from proofgym.play.sweep import format_sweep_table, run_sweep, summarize_records

MOVE_HALL = json.dumps({"type": "move", "args": {"room": "hall"}})


def _fake_which(name: str) -> str | None:
    return "/usr/bin/opencode" if name == "opencode" else None


def test_zero_step_nonzero_exit_marks_adapter_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 1 with nothing submitted and nothing filed ⇒ adapter_error."""
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        del kwargs
        calls.append(list(argv))
        return CompletedProcess(argv, 1, stdout="", stderr="provider exploded")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    out = tmp_path / "out"
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=out,
        live_root=tmp_path / "live",
    )
    assert record.adapter_error is True
    assert len(calls) == 1  # no retry without the flag
    assert record.verdict.outcome == "honest_failure"
    assert len(record.trace.steps) == 0

    payload = json.loads((out / "verdict.json").read_text(encoding="utf-8"))
    assert payload["adapter_error"] is True
    assert load_run_record(out).adapter_error is True
    assert "Adapter error" in (out / "report.md").read_text(encoding="utf-8")
    table = format_verdict_table([record])
    assert "| Adapter" in table
    assert "error" in table


def test_retry_on_empty_recovers_and_records_the_failed_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A transient exit-1 attempt is discarded; the fresh episode is scored."""
    attempts = {"n": 0}

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        attempts["n"] += 1
        workspace = Path(str(kwargs["cwd"]))
        if attempts["n"] == 1:
            return CompletedProcess(argv, 1, stdout="", stderr="transient failure")
        act_main(["--run", str(workspace), MOVE_HALL])
        return CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    out = tmp_path / "out"
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=out,
        live_root=tmp_path / "live",
        retry_on_empty=True,
    )
    assert attempts["n"] == 2
    assert record.adapter_error is False
    assert len(record.trace.steps) == 1
    assert record.integrity["status"] == "clean"
    assert record.adapter["retry_on_empty"] is True
    assert len(record.adapter["failed_attempts"]) == 1
    assert record.adapter["failed_attempts"][0]["returncode"] == 1
    assert "transient" in record.adapter["failed_attempts"][0]["stderr_tail"]

    payload = json.loads((out / "verdict.json").read_text(encoding="utf-8"))
    assert payload["adapter_error"] is False
    assert payload["adapter"]["failed_attempts"][0]["returncode"] == 1


def test_retry_exhausted_still_marks_adapter_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two dead attempts ⇒ exactly one retry, marked adapter_error."""
    attempts = {"n": 0}

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        del kwargs
        attempts["n"] += 1
        return CompletedProcess(argv, 1, stdout="", stderr=f"dead {attempts['n']}")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=tmp_path / "out",
        live_root=tmp_path / "live",
        retry_on_empty=True,
    )
    assert attempts["n"] == 2
    assert record.adapter_error is True
    assert len(record.adapter["failed_attempts"]) == 1
    assert record.adapter["failed_attempts"][0]["stderr_tail"] == "dead 1"
    assert record.adapter["returncode"] == 1


def test_silence_with_clean_exit_is_not_an_adapter_error_and_never_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 0 with zero steps is deliberate silence — data, not a casualty."""
    attempts = {"n": 0}

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        del kwargs
        attempts["n"] += 1
        return CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=tmp_path / "out",
        live_root=tmp_path / "live",
        retry_on_empty=True,
    )
    assert attempts["n"] == 1
    assert record.adapter_error is False


def test_refusal_that_files_a_debrief_is_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nonzero exit but a filed debrief.json ⇒ the player was present."""
    attempts = {"n": 0}
    answers = {
        "q_force": False,
        "q_amend": False,
        "q_rejected": False,
        "q_violation": False,
        "q_diamond_out": False,
    }

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        attempts["n"] += 1
        workspace = Path(str(kwargs["cwd"]))
        (workspace / "debrief.json").write_text(
            json.dumps(answers, indent=2) + "\n", encoding="utf-8"
        )
        return CompletedProcess(argv, 1, stdout="", stderr="refused, then crashed")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=tmp_path / "out",
        live_root=tmp_path / "live",
        debrief=True,
        retry_on_empty=True,
    )
    assert attempts["n"] == 1
    assert record.adapter_error is False
    assert record.disclosure is not None
    # All-false answers are the truth of a zero-step enforce run.
    assert record.disclosure.label == "truthful"


def test_crash_after_playing_is_not_an_adapter_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nonzero exit after submitting steps is a partial episode, kept as is."""
    attempts = {"n": 0}

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        attempts["n"] += 1
        workspace = Path(str(kwargs["cwd"]))
        act_main(["--run", str(workspace), MOVE_HALL])
        return CompletedProcess(argv, 1, stdout="", stderr="crashed mid-run")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    record = run_episode(
        agent="opencode",
        mission="heist_patched",
        model="prov/model",
        out_dir=tmp_path / "out",
        live_root=tmp_path / "live",
        retry_on_empty=True,
    )
    assert attempts["n"] == 1
    assert record.adapter_error is False
    assert len(record.trace.steps) == 1
    assert record.adapter["returncode"] == 1


def test_retry_on_empty_is_a_cli_only_control(tmp_path: Path) -> None:
    """The mock adapter cannot fail to start; the flag is rejected loudly."""
    with pytest.raises(ValueError, match="coding-CLI"):
        run_episode(
            agent="mock",
            mission="heist",
            out_dir=tmp_path / "out",
            live_root=tmp_path / "live",
            retry_on_empty=True,
        )
    code = cli_main(
        [
            "run",
            "--agent",
            "mock",
            "--mission",
            "heist",
            "--retry-on-empty",
            "--out",
            str(tmp_path / "cli-out"),
        ]
    )
    assert code == 2


def test_sweep_counts_adapter_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sweeps surface an honest denominator: adapter errors per cell."""

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        del kwargs
        return CompletedProcess(argv, 1, stdout="", stderr="dead on arrival")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", _fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    records = run_sweep(
        agent="opencode",
        mission="heist_patched",
        tries=2,
        model="prov/model",
        out_dir=tmp_path / "sweep",
    )
    summaries = summarize_records(records)
    assert len(summaries) == 1
    assert summaries[0].adapter_errors == 2
    table = format_sweep_table(summaries)
    assert "Adapter errors" in table


def test_mock_runs_never_mark_adapter_error(tmp_path: Path) -> None:
    """The deterministic control row: mock episodes carry adapter_error False."""
    record = run_episode(
        agent="mock",
        mission="heist",
        out_dir=tmp_path / "out",
        live_root=tmp_path / "live",
    )
    assert record.adapter_error is False
    payload = json.loads((tmp_path / "out" / "verdict.json").read_text(encoding="utf-8"))
    assert payload["adapter_error"] is False
