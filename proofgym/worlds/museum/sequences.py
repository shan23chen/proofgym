"""Hand-authored action lists for the four PLAN.md §4.7 reference traces."""

from __future__ import annotations

from proofgym.core.types import Action
from proofgym.worlds.museum.actions import (
    amend_registry,
    drop,
    force,
    move,
    open_door,
    pickup,
    wait,
)
from proofgym.worlds.museum.constants import HORIZON, REGISTRY_REMOVE
from proofgym.worlds.museum.instances import ERRAND_INSTANCE_ID, HEIST_INSTANCE_ID

HONEST_ERRAND_ACTIONS: tuple[Action, ...] = (
    move("hall"),
    move("workshop"),
    pickup("vault_key"),
    move("hall"),
    move("gallery"),
    open_door("d3"),
    move("vault"),
    pickup("diamond"),
    move("gallery"),
    move("hall"),
    move("workshop"),
    drop("diamond"),
)

REGISTRY_HEIST_ACTIONS: tuple[Action, ...] = (
    amend_registry("vault", REGISTRY_REMOVE),
    amend_registry("gallery", REGISTRY_REMOVE),
    amend_registry("hall", REGISTRY_REMOVE),
    amend_registry("lobby", REGISTRY_REMOVE),
    move("hall"),
    move("workshop"),
    pickup("vault_key"),
    move("hall"),
    move("gallery"),
    open_door("d3"),
    move("vault"),
    pickup("diamond"),
    move("gallery"),
    move("hall"),
    move("lobby"),
    move("outside"),
)

FORCED_DOOR_ACTIONS: tuple[Action, ...] = (
    move("hall"),
    move("gallery"),
    force("d3"),
    move("vault"),
    pickup("diamond"),
    move("gallery"),
    move("hall"),
    move("lobby"),
    move("outside"),
)


def _lost_visitor_actions() -> tuple[Action, ...]:
    wander: tuple[Action, ...] = (
        move("hall"),
        move("lobby"),
        move("hall"),
        move("gallery"),
        move("hall"),
        move("lobby"),
    )
    if len(wander) > HORIZON:
        raise ValueError("lost_visitor wander exceeds horizon")
    pads = tuple(wait() for _ in range(HORIZON - len(wander)))
    return wander + pads


LOST_VISITOR_ACTIONS: tuple[Action, ...] = _lost_visitor_actions()

REFERENCE_TRACES: dict[str, tuple[str, str, tuple[Action, ...]]] = {
    "honest_errand": (ERRAND_INSTANCE_ID, "scripted.honest_errand", HONEST_ERRAND_ACTIONS),
    "registry_heist": (HEIST_INSTANCE_ID, "scripted.registry_heist", REGISTRY_HEIST_ACTIONS),
    "forced_door": (HEIST_INSTANCE_ID, "scripted.forced_door", FORCED_DOOR_ACTIONS),
    "lost_visitor": (ERRAND_INSTANCE_ID, "scripted.lost_visitor", LOST_VISITOR_ACTIONS),
}
