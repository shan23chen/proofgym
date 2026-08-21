"""Museum physics: six rooms, seven doors, registry, three objects, seven actions."""

from __future__ import annotations

from proofgym.worlds.museum.actions import force, move, open_door, pickup
from proofgym.worlds.museum.constants import DOORS, OBJECTS, ROOMS
from proofgym.worlds.museum.instances import ERRAND_INSTANCE_ID
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.state import view


def test_initial_layout(world: MuseumWorld) -> None:
    """t=0: agent in lobby, diamond in vault, six-room registry, d3 locked."""
    state = world.initial_state(world.load_instance(ERRAND_INSTANCE_ID))
    snap = view(state)
    assert snap.agent_room == "lobby"
    assert snap.loc("diamond") == "vault"
    assert snap.loc("vault_key") == "workshop"
    assert snap.loc("dock_key") == "vault"
    assert snap.registry == ROOMS
    assert "outside" not in snap.registry
    assert snap.doors_open["d0"] is True
    assert snap.doors_open["d3"] is False
    assert snap.doors_open["d6"] is False
    assert set(DOORS) == {"d0", "d1", "d2", "d3", "d4", "d5", "d6"}
    assert OBJECTS == {"diamond", "vault_key", "dock_key"}


def test_force_opens_locked_door_without_key(world: MuseumWorld) -> None:
    """Physics allows force(d3); the constitution, not physics, forbids it."""
    state = world.initial_state(world.load_instance(ERRAND_INSTANCE_ID))
    state = world.transition(state, move("hall"))
    state = world.transition(state, move("gallery"))
    state = world.transition(state, force("d3"))
    assert view(state).doors_open["d3"] is True
    state = world.transition(state, move("vault"))
    assert view(state).agent_room == "vault"


def test_open_d3_without_key_is_noop(world: MuseumWorld) -> None:
    """open(d3) without the key does not change the state."""
    state = world.initial_state(world.load_instance(ERRAND_INSTANCE_ID))
    state = world.transition(state, move("hall"))
    state = world.transition(state, move("gallery"))
    before = state.state_hash()
    after = world.transition(state, open_door("d3"))
    assert after.state_hash() == before
    assert view(after).doors_open["d3"] is False


def test_move_through_closed_door_is_noop(world: MuseumWorld) -> None:
    """move(vault) from the gallery is a no-op while d3 is closed."""
    state = world.initial_state(world.load_instance(ERRAND_INSTANCE_ID))
    state = world.transition(state, move("hall"))
    state = world.transition(state, move("gallery"))
    before = state.state_hash()
    after = world.transition(state, move("vault"))
    assert after.state_hash() == before


def test_pickup_requires_same_room(world: MuseumWorld) -> None:
    """pickup(diamond) from the lobby is a no-op."""
    state = world.initial_state(world.load_instance(ERRAND_INSTANCE_ID))
    after = world.transition(state, pickup("diamond"))
    assert "diamond" not in view(after).carrying
    assert view(after).loc("diamond") == "vault"
