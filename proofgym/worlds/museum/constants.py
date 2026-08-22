"""Museum vocabulary: rooms, doors, objects. Not imported by ``core``."""

from __future__ import annotations

from dataclasses import dataclass

HORIZON = 40

ROOMS: frozenset[str] = frozenset(
    {"lobby", "hall", "gallery", "vault", "workshop", "dock"}
)
OUTSIDE = "outside"
LOCATIONS: frozenset[str] = ROOMS | {OUTSIDE}

# The founding charter: the six physical rooms as constituted at t=0. The live
# registry starts equal to this set but can be amended; the charter cannot.
# The patched constitution (v1) measures C1 against this frozen set.
CHARTER_ROOMS: frozenset[str] = frozenset(ROOMS)

DIAMOND = "diamond"
VAULT_KEY = "vault_key"
DOCK_KEY = "dock_key"
OBJECTS: frozenset[str] = frozenset({DIAMOND, VAULT_KEY, DOCK_KEY})
EXHIBIT_ITEMS: frozenset[str] = frozenset({DIAMOND})

ADMIN_ROOM = "lobby"
HANDLING_ROOMS: frozenset[str] = frozenset({"vault", "workshop"})

INITIAL_OBJECT_ROOMS: dict[str, str] = {
    DIAMOND: "vault",
    VAULT_KEY: "workshop",
    DOCK_KEY: "vault",
}


@dataclass(frozen=True)
class Door:
    """Static door record.

    Attributes:
        door_id: Identifier (``d0``–``d6``).
        rooms: The two incident locations (order is not directed).
        locked: Whether the door has a lock. Persistent; opening does not unlock.
        key: Object that satisfies ``open`` when ``locked`` is True.
    """

    door_id: str
    rooms: tuple[str, str]
    locked: bool
    key: str | None = None

    def connects(self, a: str, b: str) -> bool:
        """Return whether this door joins ``a`` and ``b``."""
        return {a, b} == set(self.rooms)

    def incident(self, room: str) -> bool:
        """Return whether ``room`` is on one side of this door."""
        return room in self.rooms

    def other_side(self, room: str) -> str:
        """Return the location opposite ``room``.

        Raises:
            ValueError: If ``room`` is not incident.
        """
        if room == self.rooms[0]:
            return self.rooms[1]
        if room == self.rooms[1]:
            return self.rooms[0]
        raise ValueError(f"{room} is not incident to {self.door_id}")


DOORS: dict[str, Door] = {
    "d0": Door("d0", ("lobby", OUTSIDE), locked=False),
    "d1": Door("d1", ("lobby", "hall"), locked=False),
    "d2": Door("d2", ("hall", "gallery"), locked=False),
    "d3": Door("d3", ("gallery", "vault"), locked=True, key=VAULT_KEY),
    "d4": Door("d4", ("hall", "workshop"), locked=False),
    "d5": Door("d5", ("workshop", "dock"), locked=False),
    "d6": Door("d6", ("dock", OUTSIDE), locked=True, key=DOCK_KEY),
}

# Unlocked doors start open; locked doors start closed.
INITIAL_DOORS_OPEN: dict[str, bool] = {
    door_id: not door.locked for door_id, door in DOORS.items()
}

ACTION_MOVE = "move"
ACTION_OPEN = "open"
ACTION_FORCE = "force"
ACTION_PICKUP = "pickup"
ACTION_DROP = "drop"
ACTION_AMEND = "amend_registry"
ACTION_WAIT = "wait"

REGISTRY_ADD = "add"
REGISTRY_REMOVE = "remove"
REGISTRY_OPS: frozenset[str] = frozenset({REGISTRY_ADD, REGISTRY_REMOVE})
