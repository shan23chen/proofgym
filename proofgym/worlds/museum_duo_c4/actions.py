"""Constructors for the seven typed duo actions. Every action names its actor."""

from __future__ import annotations

from proofgym.core.types import Action
from proofgym.worlds.museum_duo_c4.constants import (
    ACTION_AMEND,
    ACTION_DROP,
    ACTION_FORCE,
    ACTION_MOVE,
    ACTION_OPEN,
    ACTION_PICKUP,
    ACTION_WAIT,
)


def move(actor: str, room: str) -> Action:
    """Relocate ``actor`` (and carried objects) to an adjacent open-door room."""
    return Action(type=ACTION_MOVE, args={"actor": actor, "room": room})


def open_door(actor: str, door: str) -> Action:
    """Open a door ``actor`` is incident to, if unlocked or the key is carried."""
    return Action(type=ACTION_OPEN, args={"actor": actor, "door": door})


def force(actor: str, door: str) -> Action:
    """Force a locked door. Physically possible; C2 forbids it."""
    return Action(type=ACTION_FORCE, args={"actor": actor, "door": door})


def pickup(actor: str, obj: str) -> Action:
    """Pick up a lying object in ``actor``'s room. No stealing from hands."""
    return Action(type=ACTION_PICKUP, args={"actor": actor, "obj": obj})


def drop(actor: str, obj: str) -> Action:
    """Set down an object ``actor`` carries, in ``actor``'s room."""
    return Action(type=ACTION_DROP, args={"actor": actor, "obj": obj})


def amend_registry(actor: str, room: str, op: str) -> Action:
    """Add or remove a room from the live registry. Requires the lobby."""
    return Action(type=ACTION_AMEND, args={"actor": actor, "room": room, "op": op})


def wait(actor: str) -> Action:
    """Deliberately pass the turn."""
    return Action(type=ACTION_WAIT, args={"actor": actor})
