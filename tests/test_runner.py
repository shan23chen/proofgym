"""Enforce-mode runner: illegal actions are rejected, cost a turn, change nothing."""

from __future__ import annotations

import pytest

from proofgym.core.runner import EnforceRunner, EpisodeFinishedError
from proofgym.core.types import Action
from proofgym.worlds.museum.actions import force, move, wait
from proofgym.worlds.museum.constants import HORIZON
from proofgym.worlds.museum.constitution import CONSTITUTION_ID, public_constitution
from proofgym.worlds.museum.instances import HEIST_INSTANCE
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.state import view
from proofgym.z3check.checker import Z3Checker


def _runner(world: MuseumWorld) -> EnforceRunner:
    return EnforceRunner(
        world,
        HEIST_INSTANCE,
        Z3Checker(public_constitution()),
        horizon=HORIZON,
        constitution_id=CONSTITUTION_ID,
        meta={"agent_id": "test.enforce"},
    )


def test_force_is_rejected_with_c2_and_state_unchanged(world: MuseumWorld) -> None:
    """force(d3) is constitution-illegal: O1 returns C2, the door stays closed."""
    runner = _runner(world)
    runner.submit(move("hall"))
    runner.submit(move("gallery"))
    before = runner.state.state_hash()
    step_before = runner.step_index
    feedback = runner.submit(force("d3"))
    assert feedback.executed is False
    assert feedback.failing_clause_id == "C2"
    assert runner.state.state_hash() == before
    assert view(runner.state).doors_open["d3"] is False
    assert runner.step_index == step_before + 1
    assert runner.steps[-1].executed is False
    assert runner.state_hashes[-1] == before


def test_legal_move_is_accepted(world: MuseumWorld) -> None:
    """A legal lobby→hall move executes and changes the room."""
    runner = _runner(world)
    feedback = runner.submit(move("hall"))
    assert feedback.executed is True
    assert feedback.failing_clause_id is None
    assert view(runner.state).agent_room == "hall"


def test_unknown_action_costs_a_turn_and_changes_nothing(world: MuseumWorld) -> None:
    """Unknown action types are rejected (no clause id), consume a step."""
    runner = _runner(world)
    before = runner.state.state_hash()
    feedback = runner.submit(Action(type="teleport", args={"room": "vault"}))
    assert feedback.executed is False
    assert feedback.failing_clause_id is None
    assert feedback.error is not None
    assert runner.state.state_hash() == before
    assert runner.step_index == 1


def test_horizon_rejects_further_actions(world: MuseumWorld) -> None:
    """After 40 steps the runner is done; a further submit raises."""
    runner = EnforceRunner(
        world,
        HEIST_INSTANCE,
        Z3Checker(public_constitution()),
        horizon=2,
        constitution_id=CONSTITUTION_ID,
    )
    runner.submit(wait())
    runner.submit(wait())
    assert runner.done is True
    with pytest.raises(EpisodeFinishedError):
        runner.submit(wait())


def test_enforce_runner_is_deterministic(world: MuseumWorld) -> None:
    """Same actions yield the same hashes (D9)."""
    left = _runner(world)
    right = _runner(world)
    for action in (move("hall"), move("gallery"), force("d3")):
        left.submit(action)
        right.submit(action)
    assert left.state_hashes == right.state_hashes
    assert [step.executed for step in left.steps] == [step.executed for step in right.steps]
