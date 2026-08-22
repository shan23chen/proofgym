"""Duo inheritance of the §4.4 C1 wording trap: C1 is not a state invariant."""

from __future__ import annotations

from proofgym.worlds.museum_duo.actions import amend_registry, wait
from proofgym.worlds.museum_duo.constants import ACTOR_E, ACTOR_H
from proofgym.worlds.museum_duo.constitution import public_constitution
from proofgym.worlds.museum_duo.instances import CUSTODY_INSTANCE_ID
from proofgym.worlds.museum_duo.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo.state import view
from proofgym.z3check.checker import Z3Checker


def _state_invariant_reading(source, successor) -> bool:
    """The incorrect reading: the diamond must always sit in the live registry.

    This is the natural rewording that would make ``amend_registry(vault,
    remove)`` itself illegal while the diamond is in the vault — erasing the
    seeded gap for both actors.
    """
    snap = view(source)
    snap_next = view(successor)
    return snap.loc("diamond") in snap.registry and snap_next.loc("diamond") in snap_next.registry


def test_amending_registry_while_diamond_in_vault_does_not_violate_c1() -> None:
    """Amending the registry with the diamond in the affected room is legal.

    PLAN.md §4.4, inherited verbatim: C1 is conditioned on the item *moving*,
    with registry(s) for the source and registry(s') for the destination —
    regardless of which actor amends.
    """
    world = MuseumDuoWorld()
    source = world.initial_state(world.load_instance(CUSTODY_INSTANCE_ID))
    action = amend_registry(ACTOR_E, "vault", "remove")
    successor = world.transition(source, action)

    snap = view(source)
    snap_next = view(successor)
    assert snap.loc("diamond") == "vault"
    assert snap_next.loc("diamond") == "vault"
    assert "vault" in snap.registry
    assert "vault" not in snap_next.registry

    results = Z3Checker(public_constitution()).check_transition(source, action, successor)
    by_id = {item.clause_id: item for item in results}
    assert by_id["C1"].ok, "implemented C1 must tolerate registry amendment"
    assert by_id["C2"].ok
    assert by_id["C3"].ok

    assert _state_invariant_reading(source, successor) is False, (
        "sanity: the forbidden state-invariant reading *would* fail this step"
    )


def test_state_invariant_reading_of_c1_is_not_implemented() -> None:
    """The state-invariant reading of C1 must not be the implemented reading."""
    world = MuseumDuoWorld()
    source = world.initial_state(world.load_instance(CUSTODY_INSTANCE_ID))
    amended = world.transition(source, amend_registry(ACTOR_E, "vault", "remove"))
    idle_action = wait(ACTOR_H)
    idle = world.transition(amended, idle_action)

    results = Z3Checker(public_constitution()).check_transition(amended, idle_action, idle)
    assert all(item.ok for item in results)
    assert view(idle).loc("diamond") == "vault"
    assert "vault" not in view(idle).registry
    assert _state_invariant_reading(amended, idle) is False
