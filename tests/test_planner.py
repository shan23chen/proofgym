"""Unit tests for the minimal plan-then-act probe."""

from __future__ import annotations

import json
from pathlib import Path

from proofgym.play.harness import run_episode
from proofgym.play.planner import (
    inject_strategy,
    load_strategy,
    render_strategy_note,
    score_plan,
)


def test_score_plan_labels() -> None:
    assert score_plan({"expects_success": True}, task_success=True)["label"] == "plan_matches"
    assert score_plan({"expects_success": True}, task_success=False)["label"] == "plan_overpredicts"
    assert (
        score_plan({"expects_success": False}, task_success=True)["label"] == "plan_underpredicts"
    )
    assert score_plan(None, task_success=False)["label"] == "plan_missing"
    assert score_plan({}, task_success=False)["label"] == "plan_missing"


def test_load_strategy_rejects_truthy_non_boolean_claim(tmp_path: Path) -> None:
    path = tmp_path / "strategy.json"
    path.write_text('{"expects_success": "false"}\n', encoding="utf-8")
    try:
        load_strategy(path)
    except ValueError as exc:
        assert "JSON boolean" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("string forecasts must not be coerced to true")


def test_inject_strategy_appends_note_once(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "TASK.md").write_text("# Mission\nDo it.\n", encoding="utf-8")
    strategy = {"expects_success": False, "steps": ["wait"], "notes": ""}
    inject_strategy(workspace, strategy)
    inject_strategy(workspace, strategy)
    text = (workspace / "TASK.md").read_text(encoding="utf-8")
    assert text.count("## Prior strategy") == 1
    loaded = load_strategy(workspace / "strategy.json")
    assert loaded["expects_success"] is False
    assert "## Prior strategy" in render_strategy_note()


def test_mock_plan_file_episode_labels_plus_plan(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({"expects_success": True, "steps": ["exploit"], "notes": "n"}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    record = run_episode(
        agent="mock",
        mission="heist_patched",
        gate="permissive",
        out_dir=out,
        debrief=True,
        debrief_version=5,
        debrief_stakes=True,
        credit_objective=True,
        self_certify=True,
        plan_file=plan_path,
    )
    assert record.plan is True
    assert "+plan" in record.mission_label()
    assert record.plan_score is not None
    assert (out / "plan_score.json").is_file()
    assert (out / "plan.json").is_file()
