"""Museum snapshot view over a generic :class:`~proofgym.core.types.State`."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from proofgym.core.types import Instance, State
from proofgym.worlds.museum.constants import (
    INITIAL_DOORS_OPEN,
    INITIAL_OBJECT_ROOMS,
    OBJECTS,
    ROOMS,
)


@dataclass(frozen=True)
class MuseumSnapshot:
    """Typed view of a museum state payload.

    Attributes:
        agent_room: Agent location (a room or ``outside``).
        carrying: Objects currently carried.
        object_rooms: Last sitting-room of each object (ignored while carried).
        doors_open: Open/closed flag per door id.
        registry: Live charter — the mutable "museum" used by C1.
    """

    agent_room: str
    carrying: frozenset[str]
    object_rooms: Mapping[str, str]
    doors_open: Mapping[str, bool]
    registry: frozenset[str]

    def loc(self, obj: str) -> str:
        """Return the location of ``obj`` (carrier's room if carried).

        Args:
            obj: Object id.

        Returns:
            A room id or ``outside``.

        Raises:
            KeyError: If ``obj`` is unknown.
        """
        if obj in self.carrying:
            return self.agent_room
        try:
            return self.object_rooms[obj]
        except KeyError as exc:
            raise KeyError(f"unknown object: {obj}") from exc

    def to_state(self) -> State:
        """Pack this snapshot into a core :class:`~proofgym.core.types.State`."""
        return State(
            payload={
                "agent_room": self.agent_room,
                "carrying": sorted(self.carrying),
                "object_rooms": dict(sorted(self.object_rooms.items())),
                "doors_open": {key: bool(self.doors_open[key]) for key in sorted(self.doors_open)},
                "registry": sorted(self.registry),
            }
        )


def view(state: State) -> MuseumSnapshot:
    """Decode a core state into a :class:`MuseumSnapshot`.

    Args:
        state: Opaque core state produced by this world.

    Returns:
        Typed snapshot.

    Raises:
        KeyError: If required payload keys are missing.
        TypeError: If a field has the wrong shape.
    """
    payload = state.payload
    carrying = payload["carrying"]
    object_rooms = payload["object_rooms"]
    doors_open = payload["doors_open"]
    registry = payload["registry"]
    if not isinstance(carrying, list):
        raise TypeError("carrying must be a list")
    if not isinstance(object_rooms, dict):
        raise TypeError("object_rooms must be a dict")
    if not isinstance(doors_open, dict):
        raise TypeError("doors_open must be a dict")
    if not isinstance(registry, list):
        raise TypeError("registry must be a list")
    return MuseumSnapshot(
        agent_room=str(payload["agent_room"]),
        carrying=frozenset(str(item) for item in carrying),
        object_rooms={str(key): str(value) for key, value in object_rooms.items()},
        doors_open={str(key): bool(value) for key, value in doors_open.items()},
        registry=frozenset(str(item) for item in registry),
    )


def initial_snapshot() -> MuseumSnapshot:
    """Return the t=0 museum snapshot (seed does not randomize physics)."""
    return MuseumSnapshot(
        agent_room="lobby",
        carrying=frozenset(),
        object_rooms=dict(INITIAL_OBJECT_ROOMS),
        doors_open=dict(INITIAL_DOORS_OPEN),
        registry=frozenset(ROOMS),
    )


def protected_rooms_of(instance: Instance) -> frozenset[str]:
    """Return the frozen t=0 registry recorded on ``instance``.

    Args:
        instance: Museum instance.

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
