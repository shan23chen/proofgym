"""Duo guards: cross-world drift, strict-alternation authoring, determinism (D9)."""

from __future__ import annotations

from proofgym.core.replay import replay
from proofgym.worlds.museum.constitution import public_constitution as museum_constitution
from proofgym.worlds.museum.intent import I1_RATIONALE as MUSEUM_I1
from proofgym.worlds.museum.intent import I2_RATIONALE as MUSEUM_I2
from proofgym.worlds.museum.intent import I3_RATIONALE as MUSEUM_I3
from proofgym.worlds.museum_duo.constants import ACTOR_E, ACTOR_H, HORIZON
from proofgym.worlds.museum_duo.constitution import CONSTITUTION_ID
from proofgym.worlds.museum_duo.constitution import public_constitution as duo_constitution
from proofgym.worlds.museum_duo.intent import I1_RATIONALE as DUO_I1
from proofgym.worlds.museum_duo.intent import I2_RATIONALE as DUO_I2
from proofgym.worlds.museum_duo.intent import I3_RATIONALE as DUO_I3
from proofgym.worlds.museum_duo.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo.sequences import REFERENCE_TRACES
from proofgym.worlds.museum_duo.traces_io import (
    build_reference_trace,
    load_reference_trace,
    reference_trace_names,
)


def test_clause_texts_match_the_museum_string_for_string() -> None:
    """Drift guard: the duo world runs the same public law, verbatim.

    The constitution ids differ (different state encodings); the player-facing
    clause texts must not.
    """
    museum = {clause.clause_id: clause.text for clause in museum_constitution()}
    duo = {clause.clause_id: clause.text for clause in duo_constitution()}
    assert duo == museum
    assert CONSTITUTION_ID != "museum_public.v0", "encodings differ; the id must too"


def test_intent_rationales_match_the_museum_string_for_string() -> None:
    """Drift guard: joint I* uses the museum's rationale strings verbatim."""
    assert DUO_I1 == MUSEUM_I1
    assert DUO_I2 == MUSEUM_I2
    assert DUO_I3 == MUSEUM_I3


def test_reference_traces_strictly_alternate_starting_with_e() -> None:
    """Authoring guard: E on even steps, H on odd, within the shared horizon."""
    for name, (_, _, actions) in REFERENCE_TRACES.items():
        assert len(actions) <= HORIZON, name
        for index, action in enumerate(actions):
            expected = ACTOR_E if index % 2 == 0 else ACTOR_H
            assert action.args.get("actor") == expected, f"{name} step {index}"


def test_every_reference_step_executes_in_turn() -> None:
    """No silent no-ops: each in-turn step changes the state hash (turn toggle).

    An out-of-turn step would replay as an identity and leave the hash
    unchanged — this test would catch such a mis-authored trace.
    """
    world = MuseumDuoWorld()
    for name in reference_trace_names():
        trace = load_reference_trace(name)
        states = replay(world, trace)
        for index in range(len(trace.steps)):
            before = states[index].state_hash()
            after = states[index + 1].state_hash()
            assert before != after, f"{name} step {index} replayed as a no-op"


def test_same_instance_and_actions_same_state_hashes() -> None:
    """D9: replaying the same joint action list twice yields identical hashes."""
    world = MuseumDuoWorld()
    for name in reference_trace_names():
        first = load_reference_trace(name)
        second = load_reference_trace(name)
        hashes_a = [state.state_hash() for state in replay(world, first)]
        hashes_b = [state.state_hash() for state in replay(world, second)]
        assert hashes_a == hashes_b
        assert hashes_a == list(first.state_hashes)
        assert len(hashes_a) == len(first.steps) + 1


def test_sealed_json_matches_rebuilt_traces() -> None:
    """On-disk duo traces are the sealed form of the published sequences."""
    for name in reference_trace_names():
        on_disk = load_reference_trace(name)
        rebuilt = build_reference_trace(name)
        assert on_disk.state_hashes == rebuilt.state_hashes
        assert [step.action for step in on_disk.steps] == [step.action for step in rebuilt.steps]
        assert on_disk.meta.get("roster") == {ACTOR_E: "scripted", ACTOR_H: "scripted"}
