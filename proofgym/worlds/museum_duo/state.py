"""Duo museum snapshot view over a generic :class:`~proofgym.core.types.State`."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from proofgym.core.types import Instance, State
from proofgym.worlds.museum_duo.constants import (
    ACTOR_E,
    ACTOR_H,
    ACTORS,
    INITIAL_DOORS_OPEN,
    INITIAL_OBJECT_ROOMS,
    OBJECTS,
    ROOMS,
)


@dataclass(frozen=True)
class MuseumDuoSnapshot:
    """Typed view of a duo museum state payload.

    Attributes:
        agent_rooms: Location of each actor (a room or ``outside``).
        carrying: Objects carried, per actor. An object appears in at most one
            actor's set (it is either carried or lying, never both).
        active: Whose turn it is (``E`` or ``H``).
        object_rooms: Last sitting-room of each object (ignored while carried).
        doors_open: Open/closed flag per door id. Shared between actors.
        registry: Live charter — the mutable "museum" used by C1. Shared.
    """

    agent_rooms: Mapping[str, str]
    carrying: Mapping[str, frozenset[str]]
    active: str
    object_rooms: Mapping[str, str]
    doors_open: Mapping[str, bool]
    registry: frozenset[str]

    def carrier_of(self, obj: str) -> str | None:
        """Return the actor carrying ``obj``, or ``None`` if it is lying.

        Args:
            obj: Object id.

        Returns:
            ``E``, ``H``, or ``None``.
        """
        for actor in ACTORS:
            if obj in self.carrying[actor]:
                return actor
        return None

    def loc(self, obj: str) -> str:
        """Return the location of ``obj`` (its carrier's room if carried).

        Args:
            obj: Object id.

        Returns:
            A room id or ``outside``.

        Raises:
            KeyError: If ``obj`` is unknown.
        """
        carrier = self.carrier_of(obj)
        if carrier is not None:
            return self.agent_rooms[carrier]
        try:
            return self.object_rooms[obj]
        except KeyError as exc:
            raise KeyError(f"unknown object: {obj}") from exc

    def to_state(self) -> State:
        """Pack this snapshot into a core :class:`~proofgym.core.types.State`."""
        return State(
            payload={
                "agent_rooms": {actor: self.agent_rooms[actor] for actor in sorted(ACTORS)},
                "carrying": {actor: sorted(self.carrying[actor]) for actor in sorted(ACTORS)},
                "active": self.active,
                "object_rooms": dict(sorted(self.object_rooms.items())),
                "doors_open": {key: bool(self.doors_open[key]) for key in sorted(self.doors_open)},
                "registry": sorted(self.registry),
            }
        )


def view(state: State) -> MuseumDuoSnapshot:
    """Decode a core state into a :class:`MuseumDuoSnapshot`.

    Args:
        state: Opaque core state produced by this world.

    Returns:
        Typed snapshot.

    Raises:
        KeyError: If required payload keys are missing.
        TypeError: If a field has the wrong shape.
        ValueError: If ``active`` is not a known actor.
    """
    payload = state.payload
    agent_rooms = payload["agent_rooms"]
    carrying = payload["carrying"]
    active = payload["active"]
    object_rooms = payload["object_rooms"]
    doors_open = payload["doors_open"]
    registry = payload["registry"]
    if not isinstance(agent_rooms, dict):
        raise TypeError("agent_rooms must be a dict")
    if not isinstance(carrying, dict):
        raise TypeError("carrying must be a dict of lists")
    if not isinstance(object_rooms, dict):
        raise TypeError("object_rooms must be a dict")
    if not isinstance(doors_open, dict):
        raise TypeError("doors_open must be a dict")
    if not isinstance(registry, list):
        raise TypeError("registry must be a list")
    if str(active) not in ACTORS:
        raise ValueError(f"active must be one of {ACTORS}, got {active!r}")
    return MuseumDuoSnapshot(
        agent_rooms={str(key): str(value) for key, value in agent_rooms.items()},
        carrying={
            str(actor): frozenset(str(item) for item in items) for actor, items in carrying.items()
        },
        active=str(active),
        object_rooms={str(key): str(value) for key, value in object_rooms.items()},
        doors_open={str(key): bool(value) for key, value in doors_open.items()},
        registry=frozenset(str(item) for item in registry),
    )


def initial_snapshot() -> MuseumDuoSnapshot:
    """Return the t=0 duo snapshot (seed does not randomize physics).

    Both actors start in the lobby; E is active first (PLAN_MULTIAGENT.md M1).
    """
    return MuseumDuoSnapshot(
        agent_rooms={ACTOR_E: "lobby", ACTOR_H: "lobby"},
        carrying={ACTOR_E: frozenset(), ACTOR_H: frozenset()},
        active=ACTOR_E,
        object_rooms=dict(INITIAL_OBJECT_ROOMS),
        doors_open=dict(INITIAL_DOORS_OPEN),
        registry=frozenset(ROOMS),
    )


def protected_rooms_of(instance: Instance) -> frozenset[str]:
    """Return the frozen t=0 registry recorded on ``instance``.

    Args:
        instance: Duo museum instance.

    Returns:
        Room ids that I1 treats as the physical museum.

    Raises:
        KeyError: If ``protected_rooms`` is missing.
        TypeError: If the field is not a list of strings.
    """
    raw = instance.parameters["protected_rooms"]
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise TypeError("protected_rooms must be a list of strings")
    return frozenset(raw)


def exploit_family_of(instance: Instance) -> str | None:
    """Return the instance exploit-family tag, if any."""
    raw = instance.parameters.get("exploit_family")
    if raw is None:
        return None
    return str(raw)


def known_object(obj: str) -> bool:
    """Return whether ``obj`` is one of the three pilot objects."""
    return obj in OBJECTS
