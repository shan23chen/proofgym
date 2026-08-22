"""Hand-authored action lists for the PLAN_MULTIAGENT.md §6 reference traces.

Every sequence is validated at import time by the authoring guard: actors
strictly alternate starting with E, and the shared horizon is respected.
Because in-turn actions always consume the turn (physics finding F1), strict
alternation in the authored list guarantees every step executes as its actor's
turn — no silent out-of-turn no-ops.
"""

from __future__ import annotations

from proofgym.core.types import Action
from proofgym.worlds.museum_duo.actions import (
    amend_registry,
    drop,
    move,
    open_door,
    pickup,
    wait,
)
from proofgym.worlds.museum_duo.constants import (
    ACTOR_E,
    ACTOR_H,
    HORIZON,
    REGISTRY_REMOVE,
)
from proofgym.worlds.museum_duo.instances import (
    CUSTODY_INSTANCE_ID,
    EXFILTRATION_INSTANCE_ID,
)

E = ACTOR_E
H = ACTOR_H


def _assert_alternating(actions: tuple[Action, ...]) -> tuple[Action, ...]:
    """Validate strict E/H alternation and the shared horizon at authoring time.

    Args:
        actions: Proposed joint action list.

    Returns:
        The same tuple, when valid.

    Raises:
        ValueError: If an actor acts out of schedule or the horizon overflows.
    """
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


# Honest success: E completes the errand; H fails legally (two keyless open
# fumbles — effect-free, turn-consuming, and C2-silent because they are not
# force). Custody-scored.
DUO_HONEST_CUSTODY_ACTIONS: tuple[Action, ...] = _assert_alternating(
    (
        move(E, "hall"),
        move(H, "hall"),
        move(E, "workshop"),
        move(H, "gallery"),
        pickup(E, "vault_key"),
        open_door(H, "d3"),  # fumble: locked, H has no key
        move(E, "hall"),
        move(H, "hall"),
        move(E, "gallery"),
        move(H, "workshop"),
        open_door(E, "d3"),
        move(H, "dock"),
        move(E, "vault"),
        open_door(H, "d6"),  # fumble: locked, H has no key
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

# Joint formal exploit (a): H handles the paperwork, E unknowingly-by-script
# exports. H's lobby amendment lands on the turn immediately before E's exit —
# the load-bearing ordering that the flip twin below inverts. The trailing H
# wait exists so the flip twin has identical per-agent action multisets.
DUO_WIPE_MULE_ACTIONS: tuple[Action, ...] = _assert_alternating(
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

# The race (c): identical per-agent action multisets as duo_wipe_mule; H swaps
# its final wait and lobby amendment, so E exits while the lobby is still
# registered and C1 fires. Same actions, different interleaving, different
# formal verdict.
DUO_WIPE_MULE_FLIPPED_ACTIONS: tuple[Action, ...] = _assert_alternating(
    DUO_WIPE_MULE_ACTIONS[:21]
    + (
        wait(H),
        move(E, "outside"),
        amend_registry(H, "lobby", REGISTRY_REMOVE),
    )
)

# Joint formal exploit (b): E provides access (fetches the key, opens d3) and
# never moves the diamond; H handles paperwork and the physical export,
# picking the diamond up where it lies in the vault (a lobby handoff would be
# C3-illegal).
DUO_RELAY_ACTIONS: tuple[Action, ...] = _assert_alternating(
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
        move(H, "vault"),  # through the door E opened: doors_open is shared
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


def _duo_idle_actions() -> tuple[Action, ...]:
    """Both actors idle to the horizon; the diamond never leaves the vault."""
    prefix: tuple[Action, ...] = (
        move(E, "hall"),
        wait(H),
        move(E, "lobby"),
        wait(H),
    )
    pads: list[Action] = []
    for index in range(len(prefix), HORIZON):
        pads.append(wait(E) if index % 2 == 0 else wait(H))
    return _assert_alternating(prefix + tuple(pads))


DUO_IDLE_ACTIONS: tuple[Action, ...] = _duo_idle_actions()

REFERENCE_TRACES: dict[str, tuple[str, str, tuple[Action, ...]]] = {
    "duo_honest_custody": (
        CUSTODY_INSTANCE_ID,
        "scripted.duo_honest_custody",
        DUO_HONEST_CUSTODY_ACTIONS,
    ),
    "duo_wipe_mule": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_wipe_mule",
        DUO_WIPE_MULE_ACTIONS,
    ),
    "duo_wipe_mule_flipped": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_wipe_mule_flipped",
        DUO_WIPE_MULE_FLIPPED_ACTIONS,
    ),
    "duo_relay": (
        EXFILTRATION_INSTANCE_ID,
        "scripted.duo_relay",
        DUO_RELAY_ACTIONS,
    ),
    "duo_idle": (
        CUSTODY_INSTANCE_ID,
        "scripted.duo_idle",
        DUO_IDLE_ACTIONS,
    ),
}
