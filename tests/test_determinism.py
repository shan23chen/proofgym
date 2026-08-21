"""D9: same instance + same actions ⇒ identical state hashes."""

from __future__ import annotations

from proofgym.core.replay import replay
from proofgym.core.types import Trace
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.sequences import REFERENCE_TRACES
from proofgym.worlds.museum.traces_io import build_reference_trace, load_reference_trace


def test_same_instance_and_actions_same_state_hashes(world: MuseumWorld) -> None:
    """Replaying the same action list twice yields the same hash sequence."""
    for name in REFERENCE_TRACES:
        first = load_reference_trace(name)
        second = load_reference_trace(name)
        hashes_a = [state.state_hash() for state in replay(world, first)]
        hashes_b = [state.state_hash() for state in replay(world, second)]
        assert hashes_a == hashes_b
        assert hashes_a == list(first.state_hashes)
        assert len(hashes_a) == len(first.steps) + 1


def test_sealed_json_matches_rebuilt_traces() -> None:
    """On-disk traces are the sealed form of the published action sequences."""
    for name in REFERENCE_TRACES:
        on_disk = load_reference_trace(name)
        rebuilt = build_reference_trace(name)
        assert on_disk.state_hashes == rebuilt.state_hashes
        assert [step.action for step in on_disk.steps] == [step.action for step in rebuilt.steps]


def test_transition_is_deterministic(
    world: MuseumWorld, reference_traces: dict[str, Trace]
) -> None:
    """Applying one action to a copy of a state does not depend on call identity."""
    trace = reference_traces["honest_errand"]
    instance = world.load_instance(trace.instance_id)
    start = world.initial_state(instance)
    action = trace.steps[0].action
    left = world.transition(start, action)
    right = world.transition(start, action)
    assert left.state_hash() == right.state_hash()
    assert left.payload == right.payload
