"""Shape A smoke: sealed wipe-mule via live seat + scripted co-actor."""

from __future__ import annotations

from pathlib import Path

from proofgym.play.harness import run_episode

FIXTURE = Path(__file__).parent / "fixtures" / "duo" / "duo_wipe_mule_coactor.json"


def test_shape_a_mock_wipe_mule_formal_exploit(tmp_path: Path) -> None:
    record = run_episode(
        agent="mock",
        mission="exfiltration",
        world_name="museum_duo",
        script="duo_wipe_mule",
        gate="enforce",
        out_dir=tmp_path / "try",
        mo1_arm="a",
        live_actor="E",
        coactor_script=FIXTURE,
    )
    assert record.verdict.outcome == "formal_exploit"
    assert record.verdict.task_success is True
    assert record.verdict.formal.ok is True
    assert record.verdict.intent.verdict == "violation"
    assert len(record.trace.steps) == 24
    assert record.trace.meta.get("duo_shape") == "A"
    assert record.trace.meta.get("live_actor") == "E"
