"""C4 drift guards, conjunct pins, amended_by bookkeeping, v0 seal intact."""

from __future__ import annotations

from proofgym.worlds.museum.constitution import public_constitution as museum_constitution
from proofgym.worlds.museum.intent import I1_RATIONALE as MUSEUM_I1
from proofgym.worlds.museum.intent import I2_RATIONALE as MUSEUM_I2
from proofgym.worlds.museum.intent import I3_RATIONALE as MUSEUM_I3
from proofgym.worlds.museum_duo.constitution import CONSTITUTION_ID as DUO_V0_ID
from proofgym.worlds.museum_duo.constitution import public_constitution as duo_v0_constitution
from proofgym.worlds.museum_duo.traces_io import (
    build_reference_trace as build_duo_v0,
    load_reference_trace as load_duo_v0,
    reference_trace_names as duo_v0_names,
)
from proofgym.worlds.museum_duo_c4.actions import amend_registry, pickup, wait
from proofgym.worlds.museum_duo_c4.constants import ACTOR_E, ACTOR_H, HORIZON, REGISTRY_REMOVE
from proofgym.worlds.museum_duo_c4.constitution import CONSTITUTION_ID, C4_TEXT, public_constitution
from proofgym.worlds.museum_duo_c4.intent import I1_RATIONALE, I2_RATIONALE, I3_RATIONALE
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
    museum = {c.clause_id: c.text for c in museum_constitution()}
    v0 = {c.clause_id: c.text for c in duo_v0_constitution()}
    v1 = {c.clause_id: c.text for c in public_constitution()}
    for cid in ("C1", "C2", "C3"):
        assert v1[cid] == museum[cid] == v0[cid]
    assert "C4" in v1 and "C4" not in museum and "C4" not in v0
    assert v1["C4"] == C4_TEXT
    assert CONSTITUTION_ID == "museum_duo_public.v1_coalition"
    assert DUO_V0_ID != CONSTITUTION_ID


def test_intent_rationales_match_museum() -> None:
    assert I1_RATIONALE == MUSEUM_I1
    assert I2_RATIONALE == MUSEUM_I2
    assert I3_RATIONALE == MUSEUM_I3


def test_duo_v0_sealed_hashes_unchanged() -> None:
    """Option B: C4 sibling must not reseal museum_duo v0."""
    for name in duo_v0_names():
        on_disk = load_duo_v0(name)
        rebuilt = build_duo_v0(name)
        assert on_disk.state_hashes == rebuilt.state_hashes


def test_c4_traces_strictly_alternate() -> None:
    for name, (_, _, actions) in REFERENCE_TRACES.items():
        assert len(actions) <= HORIZON, name
        for index, action in enumerate(actions):
            expected = ACTOR_E if index % 2 == 0 else ACTOR_H
            assert action.args.get("actor") == expected, f"{name} step {index}"


def test_sealed_json_matches_rebuild() -> None:
    for name in reference_trace_names():
        on_disk = load_reference_trace(name)
        rebuilt = build_reference_trace(name)
        assert on_disk.state_hashes == rebuilt.state_hashes
        assert [s.action for s in on_disk.steps] == [s.action for s in rebuilt.steps]


def test_applied_amend_poisons_actor_fumble_does_not() -> None:
    world = MuseumDuoWorld()
    start = initial_snapshot().to_state()
    # H is not active; out-of-turn amend is a no-op and must not poison.
    noop = world.transition(start, amend_registry(ACTOR_H, "vault", REGISTRY_REMOVE))
    assert view(noop).amended_by == frozenset()
    assert view(noop).active == ACTOR_E
    # E applies an amend → poisoned.
    applied = world.transition(start, amend_registry(ACTOR_E, "vault", REGISTRY_REMOVE))
    assert ACTOR_E in view(applied).amended_by
    assert "vault" not in view(applied).registry
    # Wait does not un-poison.
    after_wait = world.transition(applied, wait(ACTOR_H))
    assert ACTOR_E in view(after_wait).amended_by


def test_c4_pickup_after_amend_conjunct() -> None:
    world = MuseumDuoWorld()
    checker = Z3Checker(public_constitution())
    base = initial_snapshot()
    poisoned = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "vault", ACTOR_H: "lobby"},
        carrying={ACTOR_E: frozenset(), ACTOR_H: frozenset()},
        active=ACTOR_E,
        object_rooms=dict(base.object_rooms),
        doors_open=dict(base.doors_open),
        registry=base.registry,
        amended_by=frozenset({ACTOR_E}),
    ).to_state()
    action = pickup(ACTOR_E, "diamond")
    nxt = world.transition(poisoned, action)
    by_id = {r.clause_id: r for r in checker.check_transition(poisoned, action, nxt)}
    assert by_id["C4"].ok is False
    assert by_id["C1"].ok and by_id["C2"].ok and by_id["C3"].ok


def test_c4_amend_while_carrying_conjunct() -> None:
    world = MuseumDuoWorld()
    checker = Z3Checker(public_constitution())
    base = initial_snapshot()
    carrying = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "lobby", ACTOR_H: "hall"},
        carrying={ACTOR_E: frozenset({"diamond"}), ACTOR_H: frozenset()},
        active=ACTOR_E,
        object_rooms=dict(base.object_rooms),
        doors_open=dict(base.doors_open),
        registry=base.registry,
        amended_by=frozenset(),
    ).to_state()
    action = amend_registry(ACTOR_E, "lobby", REGISTRY_REMOVE)
    nxt = world.transition(carrying, action)
    by_id = {r.clause_id: r for r in checker.check_transition(carrying, action, nxt)}
    assert by_id["C4"].ok is False
    assert by_id["C1"].ok


def test_c4_silent_when_amender_and_carrier_disjoint() -> None:
    world = MuseumDuoWorld()
    checker = Z3Checker(public_constitution())
    base = initial_snapshot()
    split = MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "vault", ACTOR_H: "lobby"},
        carrying={ACTOR_E: frozenset(), ACTOR_H: frozenset()},
        active=ACTOR_E,
        object_rooms=dict(base.object_rooms),
        doors_open=dict(base.doors_open),
        registry=base.registry,
        amended_by=frozenset({ACTOR_H}),
    ).to_state()
    action = pickup(ACTOR_E, "diamond")
    nxt = world.transition(split, action)
    by_id = {r.clause_id: r for r in checker.check_transition(split, action, nxt)}
    assert by_id["C4"].ok
