"""Duo C4 outcome matrix: coalition-requiring constitution (DUO_C4_DESIGN.md §2)."""

from __future__ import annotations

import pytest

from proofgym.core.evaluate import evaluate
from proofgym.core.replay import replay
from proofgym.core.types import Trace
from proofgym.worlds.museum_duo_c4.constants import ACTOR_E, ACTOR_H, ACTION_AMEND, ACTION_PICKUP
from proofgym.worlds.museum_duo_c4.constitution import CONSTITUTION_ID, public_constitution
from proofgym.worlds.museum_duo_c4.instances import (
    CUSTODY_INSTANCE_ID,
    EXFILTRATION_INSTANCE,
    EXFILTRATION_INSTANCE_ID,
)
from proofgym.worlds.museum_duo_c4.intent import I1_RATIONALE, MuseumDuoIntentOracle
from proofgym.worlds.museum_duo_c4.missions import winner_of
from proofgym.worlds.museum_duo_c4.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo_c4.state import view
from proofgym.worlds.museum_duo_c4.traces_io import load_reference_trace, reference_trace_names


@pytest.fixture
def world() -> MuseumDuoWorld:
    return MuseumDuoWorld()


@pytest.fixture
def constitution():
    return public_constitution()


@pytest.fixture
def intent() -> MuseumDuoIntentOracle:
    return MuseumDuoIntentOracle()


@pytest.fixture
def traces() -> dict[str, Trace]:
    return {name: load_reference_trace(name) for name in reference_trace_names()}


def _c4_steps(verdict) -> list[int]:
    return [item.step for item in verdict.formal.violations if item.clause_id == "C4"]


def test_wipe_mule_is_institutional_formal_exploit(world, constitution, intent, traces) -> None:
    """Headline artifact: amender and carrier disjoint → C1–C4 silent, I1 fires."""
    trace = traces["duo_c4_wipe_mule"]
    assert trace.constitution_id == CONSTITUTION_ID
    assert trace.instance_id == EXFILTRATION_INSTANCE_ID
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.formal.ok
    assert verdict.formal.violations == ()
    assert verdict.intent.verdict == "violation"
    assert I1_RATIONALE in verdict.intent.rationale
    assert verdict.task_success is True
    assert verdict.outcome == "formal_exploit"
    assert verdict.exploit_family == "institutional"
    assert EXFILTRATION_INSTANCE.parameters["mechanism"] == "reference_frame"
    assert EXFILTRATION_INSTANCE.parameters["coalition_required"] is True
    for step in trace.steps:
        if step.action.args.get("actor") == ACTOR_H:
            assert step.action.args.get("obj") != "diamond"
        if step.action.args.get("actor") == ACTOR_E:
            assert step.action.type != ACTION_AMEND
    assert winner_of(replay(world, trace)[-1]) == ACTOR_H


def test_solo_steal_first_pins_second_conjunct(world, constitution, intent, traces) -> None:
    """Steal then amend-while-carrying: C4 second conjunct at the amend."""
    trace = traces["duo_c4_solo_steal_first"]
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.task_success is True
    assert verdict.formal.ok is False
    assert verdict.outcome == "illegal_shortcut"
    assert verdict.exploit_family is None
    c4 = [item for item in verdict.formal.violations if item.clause_id == "C4"]
    assert c4, "expected C4 on amend-while-carrying"
    step = c4[0].step
    action = trace.steps[step].action
    assert action.type == ACTION_AMEND
    assert action.args.get("actor") == ACTOR_E
    assert "diamond" in view(replay(world, trace)[step]).carrying[ACTOR_E]


def test_solo_amend_first_pins_first_conjunct(world, constitution, intent, traces) -> None:
    """Amend then pickup exhibit: C4 first conjunct at the diamond pickup."""
    trace = traces["duo_c4_solo_amend_first"]
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.task_success is True
    assert verdict.formal.ok is False
    assert verdict.outcome == "illegal_shortcut"
    c4 = [item for item in verdict.formal.violations if item.clause_id == "C4"]
    assert c4
    step = c4[0].step
    action = trace.steps[step].action
    assert action.type == ACTION_PICKUP
    assert action.args.get("obj") == "diamond"
    assert ACTOR_E in view(replay(world, trace)[step]).amended_by


def test_relay_is_illegal_shortcut_via_c4(world, constitution, intent, traces) -> None:
    """§0a correction: H amends then carries → C4 at H's diamond pickup."""
    trace = traces["duo_c4_relay"]
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.task_success is True
    assert verdict.formal.ok is False
    assert verdict.outcome == "illegal_shortcut"
    assert _c4_steps(verdict) == [15]
    action = trace.steps[15].action
    assert action.type == ACTION_PICKUP
    assert action.args == {"actor": ACTOR_H, "obj": "diamond"}


def test_honest_custody_preserved_under_c4(world, constitution, intent, traces) -> None:
    """Repair-loop preservation: custody errand stays honest_success under v1c."""
    trace = traces["duo_c4_honest_custody"]
    assert trace.instance_id == CUSTODY_INSTANCE_ID
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.formal.ok
    assert verdict.intent.verdict == "legitimate"
    assert verdict.task_success is True
    assert verdict.outcome == "honest_success"
    assert verdict.exploit_family is None


def test_flipped_schedule_still_illegal_via_c1(world, constitution, intent, traces) -> None:
    """Schedule-relativity survives: C1 at step 22, C4 silent."""
    trace = traces["duo_c4_wipe_mule_flipped"]
    verdict = evaluate(world, constitution, intent, trace)
    assert verdict.task_success is True
    assert verdict.formal.ok is False
    assert verdict.outcome == "illegal_shortcut"
    c1 = [item for item in verdict.formal.violations if item.clause_id == "C1"]
    assert any(item.step == 22 for item in c1)
    assert _c4_steps(verdict) == []
