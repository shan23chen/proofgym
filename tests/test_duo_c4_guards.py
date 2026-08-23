"""Duo C4 guards: drift, bookkeeping, sealed integrity, v0 isolation."""

from __future__ import annotations

from proofgym.core.replay import replay
from proofgym.worlds.museum.constitution import public_constitution as museum_constitution
from proofgym.worlds.museum_duo.constitution import CONSTITUTION_ID as DUO_V0_ID
from proofgym.worlds.museum_duo.constitution import public_constitution as duo_v0_constitution
from proofgym.worlds.museum_duo.traces_io import (
    build_reference_trace as build_v0_trace,
)
from proofgym.worlds.museum_duo.traces_io import (
    load_reference_trace as load_v0_trace,
)
from proofgym.worlds.museum_duo.traces_io import (
    reference_trace_names as v0_trace_names,
)
from proofgym.worlds.museum_duo_c4.actions import amend_registry, move, pickup, wait
from proofgym.worlds.museum_duo_c4.constants import ACTOR_E, ACTOR_H, HORIZON
from proofgym.worlds.museum_duo_c4.constitution import (
    C4_TEXT,
    CONSTITUTION_ID,
    public_constitution,
)
from proofgym.worlds.museum_duo_c4.instances import CUSTODY_INSTANCE_ID
from proofgym.worlds.museum_duo_c4.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo_c4.sequences import REFERENCE_TRACES
from proofgym.worlds.museum_duo_c4.state import MuseumDuoSnapshot, initial_snapshot, view
from proofgym.worlds.museum_duo_c4.traces_io import (
    build_reference_trace,
    load_reference_trace,
    reference_trace_names,
)
from proofgym.z3check.checker import Z3Checker


def test_c1_c3_texts_match_museum_and_duo_v0() -> None:
    """Drift guard: C1–C3 texts identical across museum, duo v0, and duo v1c."""
    museum = {c.clause_id: c.text for c in museum_constitution()}
    duo_v0 = {c.clause_id: c.text for c in duo_v0_constitution()}
    duo_c4 = {c.clause_id: c.text for c in public_constitution()}
    for clause_id in ("C1", "C2", "C3"):
        assert duo_c4[clause_id] == museum[clause_id] == duo_v0[clause_id]
    assert "C4" not in museum
    assert "C4" not in duo_v0
    assert duo_c4["C4"] == C4_TEXT


def test_c4_exists_only_in_v1c() -> None:
    """Drift guard: C4 is exclusive to museum_duo_public.v1_coalition."""
    assert CONSTITUTION_ID == "museum_duo_public.v1_coalition"
    assert DUO_V0_ID == "museum_duo_public.v0"
    assert len(public_constitution()) == 4
    assert len(duo_v0_constitution()) == 3
    assert {c.clause_id for c in public_constitution()} == {"C1", "C2", "C3", "C4"}


def test_v0_sealed_traces_unchanged() -> None:
    """Option B isolation: sealed museum_duo v0 JSON hashes are untouched."""
    for name in v0_trace_names():
        on_disk = load_v0_trace(name)
        rebuilt = build_v0_trace(name)
        assert on_disk.state_hashes == rebuilt.state_hashes
        assert on_disk.constitution_id == DUO_V0_ID
        # Payload never gained amended_by.
        from proofgym.worlds.museum_duo.physics import MuseumDuoWorld as V0World

        states = replay(V0World(), on_disk)
        assert "amended_by" not in states[0].payload


def test_c4_sealed_json_matches_rebuilt_traces() -> None:
    """On-disk C4 traces are the sealed form of the published sequences."""
    for name in reference_trace_names():
        on_disk = load_reference_trace(name)
        rebuilt = build_reference_trace(name)
        assert on_disk.state_hashes == rebuilt.state_hashes
        assert on_disk.constitution_id == CONSTITUTION_ID
        assert [step.action for step in on_disk.steps] == [step.action for step in rebuilt.steps]


def test_reference_traces_strictly_alternate_starting_with_e() -> None:
    """Authoring guard: E on even steps, H on odd, within the shared horizon."""
    for name, (_, _, actions) in REFERENCE_TRACES.items():
        assert len(actions) <= HORIZON, name
        for index, action in enumerate(actions):
            expected = ACTOR_E if index % 2 == 0 else ACTOR_H
            assert action.args.get("actor") == expected, f"{name} step {index}"


def test_applied_amend_poisons_actor_both_ops() -> None:
    """§1.3: applied add and remove both poison; monotone; per-actor."""
    world = MuseumDuoWorld()
    state = world.initial_state(world.load_instance(CUSTODY_INSTANCE_ID))
    assert view(state).amended_by == frozenset()
    after_remove = world.transition(state, amend_registry(ACTOR_E, "vault", "remove"))
    assert view(after_remove).amended_by == frozenset({ACTOR_E})
    after_wait = world.transition(after_remove, wait(ACTOR_H))
    assert view(after_wait).amended_by == frozenset({ACTOR_E})
    after_add = world.transition(after_wait, amend_registry(ACTOR_E, "vault", "add"))
    assert view(after_add).amended_by == frozenset({ACTOR_E})
    # H is not poisoned by E's amendments.
    after_h_move = world.transition(after_add, move(ACTOR_H, "hall"))
    assert ACTOR_H not in view(after_h_move).amended_by


def test_fumbled_and_out_of_turn_amends_do_not_poison() -> None:
    """§1.3: fumbled (wrong room) and out-of-turn amends do not write amended_by."""
    world = MuseumDuoWorld()
    state = world.initial_state(world.load_instance(CUSTODY_INSTANCE_ID))
    # Out of turn: H amends while E is active → identity, no poison.
    noop = world.transition(state, amend_registry(ACTOR_H, "vault", "remove"))
    assert noop.state_hash() == state.state_hash()
    assert view(noop).amended_by == frozenset()
    # Fumble: E is in lobby... move E to hall, then try amend (wrong room).
    in_hall = world.transition(state, move(ACTOR_E, "hall"))
    assert view(in_hall).active == ACTOR_H
    mid = world.transition(in_hall, wait(ACTOR_H))
    assert view(mid).active == ACTOR_E
    assert view(mid).agent_rooms[ACTOR_E] == "hall"
    fumbled = world.transition(mid, amend_registry(ACTOR_E, "vault", "remove"))
    assert view(fumbled).amended_by == frozenset()
    assert view(fumbled).registry == view(mid).registry


def test_action_keyed_c4_rejects_poisoned_pickup_attempt() -> None:
    """Encoding wrinkle (like C2): C4 fires on the attempt, not the effect."""
    world = MuseumDuoWorld()
    checker = Z3Checker(public_constitution())
    # Poisoned E in lobby (no diamond here) attempts pickup(diamond) → fumble,
    # but C4 still fails because E has amended.
    poisoned = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "lobby", ACTOR_H: "lobby"},
        carrying={ACTOR_E: frozenset(), ACTOR_H: frozenset()},
        active=ACTOR_E,
        object_rooms=dict(initial_snapshot().object_rooms),
        doors_open=dict(initial_snapshot().doors_open),
        registry=initial_snapshot().registry,
        amended_by=frozenset({ACTOR_E}),
    ).to_state()
    action = pickup(ACTOR_E, "diamond")
    successor = world.transition(poisoned, action)
    by_id = {r.clause_id: r for r in checker.check_transition(poisoned, action, successor)}
    assert by_id["C4"].ok is False
    assert view(successor).carrier_of("diamond") is None  # physics fumbled
