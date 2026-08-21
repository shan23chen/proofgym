"""Deterministic replay of a stored trace against a world's physics."""

from __future__ import annotations

from proofgym.core.protocols import World
from proofgym.core.types import State, Trace


class HashMismatchError(ValueError):
    """Raised when stored ``state_hashes`` do not match a deterministic replay."""


def replay(world: World, trace: Trace, *, verify_hashes: bool = True) -> list[State]:
    """Recompute the state sequence of ``trace``.

    Audit mode: physics runs regardless of constitution legality. A step with
    ``executed=False`` (enforce-mode rejection) leaves the state unchanged.

    Args:
        world: Physics engine.
        trace: Stored action list.
        verify_hashes: When True and the trace records hashes, require an exact
            match (D9 integrity check).

    Returns:
        ``[s0, s1, ..., sN]`` where ``s0`` is the instance initial state.

    Raises:
        KeyError: If the trace instance is unknown.
        HashMismatchError: If stored hashes disagree with the replay.
    """
    instance = world.load_instance(trace.instance_id)
    state = world.initial_state(instance)
    states: list[State] = [state]
    for step in trace.steps:
        if step.executed:
            state = world.transition(state, step.action)
        states.append(state)
    if verify_hashes and trace.state_hashes:
        computed = tuple(item.state_hash() for item in states)
        if computed != tuple(trace.state_hashes):
            raise HashMismatchError(
                "stored state_hashes do not match deterministic replay of "
                f"{trace.instance_id} ({len(trace.steps)} steps)"
            )
    return states
