"""Pin the duo turn semantics (PLAN_MULTIAGENT.md M1, §4.2, finding F1)."""

from __future__ import annotations

import pytest

from proofgym.core.types import State
from proofgym.worlds.museum_duo.actions import (
    amend_registry,
    drop,
    force,
    move,
    open_door,
    pickup,
    wait,
)
from proofgym.worlds.museum_duo.constants import ACTOR_E, ACTOR_H
from proofgym.worlds.museum_duo.instances import CUSTODY_INSTANCE_ID
from proofgym.worlds.museum_duo.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo.state import MuseumDuoSnapshot, initial_snapshot, view


@pytest.fixture
def duo_world() -> MuseumDuoWorld:
    """Return a duo museum world."""
    return MuseumDuoWorld()


@pytest.fixture
def start(duo_world: MuseumDuoWorld) -> State:
    """Return the t=0 state (both actors in the lobby, E active)."""
    return duo_world.initial_state(duo_world.load_instance(CUSTODY_INSTANCE_ID))


def test_initial_active_actor_is_e(start: State) -> None:
    """E moves first (M1); both actors start in the lobby."""
    snap = view(start)
    assert snap.active == ACTOR_E
    assert snap.agent_rooms == {ACTOR_E: "lobby", ACTOR_H: "lobby"}


def test_out_of_turn_actions_are_identity_noops(duo_world: MuseumDuoWorld, start: State) -> None:
    """All seven action types by the frozen actor, including wait, change nothing."""
    out_of_turn = (
        move(ACTOR_H, "hall"),
        open_door(ACTOR_H, "d0"),
        force(ACTOR_H, "d0"),
        pickup(ACTOR_H, "vault_key"),
        drop(ACTOR_H, "vault_key"),
        amend_registry(ACTOR_H, "vault", "remove"),
        wait(ACTOR_H),
    )
    for action in out_of_turn:
        successor = duo_world.transition(start, action)
        assert successor.state_hash() == start.state_hash(), action.type
        assert view(successor).active == ACTOR_E, action.type


def test_in_turn_wait_toggles_active_and_nothing_else(
    duo_world: MuseumDuoWorld, start: State
) -> None:
    """wait is not short-circuited: it passes the turn (the museum trap, fixed)."""
    successor = duo_world.transition(start, wait(ACTOR_E))
    before = view(start)
    after = view(successor)
    assert after.active == ACTOR_H
    assert after.agent_rooms == before.agent_rooms
    assert after.carrying == before.carrying
    assert after.object_rooms == before.object_rooms
    assert after.doors_open == before.doors_open
    assert after.registry == before.registry
    assert successor.state_hash() != start.state_hash()


def test_in_turn_fumble_consumes_the_turn_without_effects(
    duo_world: MuseumDuoWorld, start: State
) -> None:
    """Finding F1: a failed in-turn attempt passes the baton, no stalling channel."""
    # E is in the lobby; d3 is elsewhere, so this open attempt fails physics.
    successor = duo_world.transition(start, open_door(ACTOR_E, "d3"))
    before = view(start)
    after = view(successor)
    assert after.active == ACTOR_H
    assert after.doors_open == before.doors_open
    assert after.agent_rooms == before.agent_rooms


def test_pickup_cannot_steal_from_the_other_actor(duo_world: MuseumDuoWorld) -> None:
    """An object carried by anyone cannot be picked up (no-steal, §4.3)."""
    snap = initial_snapshot()
    contested = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "vault", ACTOR_H: "vault"},
        carrying={ACTOR_E: frozenset({"diamond"}), ACTOR_H: frozenset()},
        active=ACTOR_H,
        object_rooms=dict(snap.object_rooms),
        doors_open=dict(snap.doors_open),
        registry=snap.registry,
    ).to_state()
    successor = duo_world.transition(contested, pickup(ACTOR_H, "diamond"))
    after = view(successor)
    assert "diamond" in after.carrying[ACTOR_E]
    assert "diamond" not in after.carrying[ACTOR_H]
    assert after.active == ACTOR_E, "the failed attempt still consumes H's turn"


def test_open_requires_the_acting_actor_to_carry_the_key(
    duo_world: MuseumDuoWorld,
) -> None:
    """H cannot open d3 on the strength of E's key."""
    snap = initial_snapshot()
    at_door = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "gallery", ACTOR_H: "gallery"},
        carrying={ACTOR_E: frozenset({"vault_key"}), ACTOR_H: frozenset()},
        active=ACTOR_H,
        object_rooms={"diamond": "vault", "dock_key": "vault"},
        doors_open=dict(snap.doors_open),
        registry=snap.registry,
    ).to_state()
    successor = duo_world.transition(at_door, open_door(ACTOR_H, "d3"))
    assert view(successor).doors_open["d3"] is False
    assert view(successor).active == ACTOR_E


def test_carried_objects_move_with_their_carrier(duo_world: MuseumDuoWorld) -> None:
    """loc() resolves through the carrier for either actor."""
    snap = initial_snapshot()
    carrying_h = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "lobby", ACTOR_H: "hall"},
        carrying={ACTOR_E: frozenset(), ACTOR_H: frozenset({"vault_key"})},
        active=ACTOR_H,
        object_rooms={"diamond": "vault", "dock_key": "vault"},
        doors_open=dict(snap.doors_open),
        registry=snap.registry,
    ).to_state()
    assert view(carrying_h).loc("vault_key") == "hall"
    successor = duo_world.transition(carrying_h, move(ACTOR_H, "workshop"))
    assert view(successor).loc("vault_key") == "workshop"


def test_unknown_actor_or_type_raises(duo_world: MuseumDuoWorld, start: State) -> None:
    """Malformed actions fail loudly rather than silently no-op."""
    from proofgym.core.types import Action

    with pytest.raises(ValueError):
        duo_world.transition(start, Action(type="move", args={"actor": "X", "room": "hall"}))
    with pytest.raises(ValueError):
        duo_world.transition(start, Action(type="teleport", args={"actor": ACTOR_E}))
    with pytest.raises(KeyError):
        duo_world.transition(start, Action(type="move", args={"room": "hall"}))


def test_available_actions_are_tagged_with_the_active_actor(
    duo_world: MuseumDuoWorld, start: State
) -> None:
    """Enumeration covers only the active actor; wait is always present."""
    actions = duo_world.available_actions(start)
    assert actions, "expected at least wait"
    assert all(action.args.get("actor") == ACTOR_E for action in actions)
    assert any(action.type == "wait" for action in actions)
    after_wait = duo_world.transition(start, wait(ACTOR_E))
    actions_h = duo_world.available_actions(after_wait)
    assert all(action.args.get("actor") == ACTOR_H for action in actions_h)
