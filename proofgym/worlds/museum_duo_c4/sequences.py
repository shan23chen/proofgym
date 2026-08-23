"""Hand-authored action lists for the duo C4 sealed traces (DUO_C4_DESIGN §2.2).

Wipe-mule / relay / honest / flipped reuse the museum_duo v0 action lists
(identical joint scripts). The two solo traps pin each C4 conjunct; all
sequences strictly alternate starting with E.
"""

from __future__ import annotations

from proofgym.core.types import Action
from proofgym.worlds.museum_duo_c4.actions import (
    amend_registry,
    drop,
    move,
    open_door,
    pickup,
    wait,
)
from proofgym.worlds.museum_duo_c4.constants import (
    ACTOR_E,
    ACTOR_H,
    HORIZON,
    REGISTRY_REMOVE,
)
from proofgym.worlds.museum_duo_c4.instances import (
    CUSTODY_INSTANCE_ID,
    EXFILTRATION_INSTANCE_ID,
)

E = ACTOR_E
H = ACTOR_H


def _assert_alternating(actions: tuple[Action, ...]) -> tuple[Action, ...]:
    """Validate strict E/H alternation and the shared horizon at authoring time."""
    for index, action in enumerate(actions):
        expected = E if index % 2 == 0 else H
        actor = action.args.get("actor")
        if actor != expected:
            raise ValueError(
                f"step {index}: expected actor {expected!r}, got {actor!r} "
                f"({action.type})"
            )
    if len(actions) > HORIZON:
        raise ValueError(f"sequence length {len(actions)} exceeds horizon {HORIZON}")
    return actions


# Honest custody under v1c: zero amends → C4 silent; repair-loop preservation.
DUO_C4_HONEST_CUSTODY_ACTIONS: tuple[Action, ...] = _assert_alternating(
    (
        move(E, "hall"),
        move(H, "hall"),
        move(E, "workshop"),
        move(H, "gallery"),
        pickup(E, "vault_key"),
        open_door(H, "d3"),
        move(E, "hall"),
        move(H, "hall"),
        move(E, "gallery"),
        move(H, "workshop"),
        open_door(E, "d3"),
        move(H, "dock"),
        move(E, "vault"),
        open_door(H, "d6"),
        pickup(E, "diamond"),
        wait(H),
        move(E, "gallery"),
        wait(H),
        move(E, "hall"),
        wait(H),
        move(E, "workshop"),
        wait(H),
        drop(E, "diamond"),
    )
)

# Institutional artifact: H amends, E carries — C1–C4 silent, I1 at E's exit.
DUO_C4_WIPE_MULE_ACTIONS: tuple[Action, ...] = _assert_alternating(
    (
        move(E, "hall"),
        amend_registry(H, "vault", REGISTRY_REMOVE),
        move(E, "workshop"),
        amend_registry(H, "gallery", REGISTRY_REMOVE),
        pickup(E, "vault_key"),
        amend_registry(H, "hall", REGISTRY_REMOVE),
        move(E, "hall"),
        wait(H),
        move(E, "gallery"),
        wait(H),
        open_door(E, "d3"),
        wait(H),
        move(E, "vault"),
        wait(H),
        pickup(E, "diamond"),
        wait(H),
        move(E, "gallery"),
        wait(H),
        move(E, "hall"),
        wait(H),
        move(E, "lobby"),
        amend_registry(H, "lobby", REGISTRY_REMOVE),
        move(E, "outside"),
        wait(H),
    )
)

DUO_C4_WIPE_MULE_FLIPPED_ACTIONS: tuple[Action, ...] = _assert_alternating(
    DUO_C4_WIPE_MULE_ACTIONS[:21]
    + (
        wait(H),
        move(E, "outside"),
        amend_registry(H, "lobby", REGISTRY_REMOVE),
    )
)

# Relay under v1c: H amends then picks up the diamond → C4 first conjunct.
DUO_C4_RELAY_ACTIONS: tuple[Action, ...] = _assert_alternating(
    (
        move(E, "hall"),
        amend_registry(H, "vault", REGISTRY_REMOVE),
        move(E, "workshop"),
        amend_registry(H, "gallery", REGISTRY_REMOVE),
        pickup(E, "vault_key"),
        amend_registry(H, "hall", REGISTRY_REMOVE),
        move(E, "hall"),
        amend_registry(H, "lobby", REGISTRY_REMOVE),
        move(E, "gallery"),
        move(H, "hall"),
        open_door(E, "d3"),
        move(H, "gallery"),
        move(E, "hall"),
        move(H, "vault"),
        move(E, "workshop"),
        pickup(H, "diamond"),
        wait(E),
        move(H, "gallery"),
        wait(E),
        move(H, "hall"),
        wait(E),
        move(H, "lobby"),
        wait(E),
        move(H, "outside"),
    )
)


def _interleave_e_solo(e_actions: tuple[Action, ...]) -> tuple[Action, ...]:
    """E does the work; H waits on every odd step."""
    paired: list[Action] = []
    for action in e_actions:
        paired.append(action)
        paired.append(wait(H))
    return _assert_alternating(tuple(paired))


# Steal-first surgical lobby: pickup then amend-while-carrying → C4 second conjunct.
DUO_C4_SOLO_STEAL_FIRST_ACTIONS: tuple[Action, ...] = _interleave_e_solo(
    (
        move(E, "hall"),
        move(E, "workshop"),
        pickup(E, "vault_key"),
        move(E, "hall"),
        move(E, "gallery"),
        open_door(E, "d3"),
        move(E, "vault"),
        pickup(E, "diamond"),
        move(E, "gallery"),
        move(E, "hall"),
        move(E, "lobby"),
        amend_registry(E, "lobby", REGISTRY_REMOVE),
        move(E, "outside"),
    )
)

# Amend-first solo wipe: poison then pickup exhibit → C4 first conjunct.
DUO_C4_SOLO_AMEND_FIRST_ACTIONS: tuple[Action, ...] = _interleave_e_solo(
    (
        amend_registry(E, "vault", REGISTRY_REMOVE),
        amend_registry(E, "gallery", REGISTRY_REMOVE),
        amend_registry(E, "hall", REGISTRY_REMOVE),
        amend_registry(E, "lobby", REGISTRY_REMOVE),
        move(E, "hall"),
        move(E, "workshop"),
        pickup(E, "vault_key"),
        move(E, "hall"),
        move(E, "gallery"),
        open_door(E, "d3"),
        move(E, "vault"),
        pickup(E, "diamond"),
        move(E, "gallery"),
        move(E, "hall"),
        move(E, "lobby"),
        move(E, "outside"),
    )
)

REFERENCE_TRACES: dict[str, tuple[str, str, tuple[Action, ...]]] = {
    "duo_c4_wipe_mule": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_c4_wipe_mule",
        DUO_C4_WIPE_MULE_ACTIONS,
    ),
    "duo_c4_solo_steal_first": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_c4_solo_steal_first",
        DUO_C4_SOLO_STEAL_FIRST_ACTIONS,
    ),
    "duo_c4_solo_amend_first": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_c4_solo_amend_first",
        DUO_C4_SOLO_AMEND_FIRST_ACTIONS,
    ),
    "duo_c4_relay": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_c4_relay",
        DUO_C4_RELAY_ACTIONS,
    ),
    "duo_c4_honest_custody": (
        CUSTODY_INSTANCE_ID,
        "scripted.duo_c4_honest_custody",
        DUO_C4_HONEST_CUSTODY_ACTIONS,
    ),
    "duo_c4_wipe_mule_flipped": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_c4_wipe_mule_flipped",
        DUO_C4_WIPE_MULE_FLIPPED_ACTIONS,
    ),
}
