"""Constructors for the seven typed museum actions."""

from __future__ import annotations

from proofgym.core.types import Action
from proofgym.worlds.museum.constants import (
    ACTION_AMEND,
    ACTION_DROP,
    ACTION_FORCE,
    ACTION_MOVE,
    ACTION_OPEN,
    ACTION_PICKUP,
    ACTION_WAIT,
)


def move(room: str) -> Action:
    """Relocate the agent (and carried objects) to an adjacent open-door room."""
    return Action(type=ACTION_MOVE, args={"room": room})


def open_door(door: str) -> Action:
    """Open a door the agent is incident to, if unlocked or the key is carried."""
    return Action(type=ACTION_OPEN, args={"door": door})


def force(door: str) -> Action:
    """Force a locked door. Physically possible; C2 forbids it."""
    return Action(type=ACTION_FORCE, args={"door": door})


def pickup(obj: str) -> Action:
    """Pick up an object in the agent's room."""
    return Action(type=ACTION_PICKUP, args={"obj": obj})


def drop(obj: str) -> Action:
    """Set down a carried object in the agent's room."""
    return Action(type=ACTION_DROP, args={"obj": obj})


def amend_registry(room: str, op: str) -> Action:
    """Add or remove a room from the live registry. Requires the lobby."""
    return Action(type=ACTION_AMEND, args={"room": room, "op": op})


def wait() -> Action:
    """No-op."""
    return Action(type=ACTION_WAIT, args={})
