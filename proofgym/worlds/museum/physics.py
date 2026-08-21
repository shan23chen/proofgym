"""Deterministic museum physics. What is possible, not what is permitted."""

from __future__ import annotations

from collections.abc import Sequence

from proofgym.core.types import Action, Instance, State
from proofgym.worlds.museum.constants import (
    ACTION_AMEND,
    ACTION_DROP,
    ACTION_FORCE,
    ACTION_MOVE,
    ACTION_OPEN,
    ACTION_PICKUP,
    ACTION_WAIT,
    ADMIN_ROOM,
    DOORS,
    LOCATIONS,
    OBJECTS,
    REGISTRY_ADD,
    REGISTRY_OPS,
    REGISTRY_REMOVE,
    ROOMS,
)
from proofgym.worlds.museum.instances import INSTANCES
from proofgym.worlds.museum.missions import mission_for_id
from proofgym.worlds.museum.state import MuseumSnapshot, initial_snapshot, view


class MuseumWorld:
    """Six-room graph world with a mutable registry and three objects.

    Transition is total: unknown action types raise; failed preconditions are
    no-ops. Same instance + same actions yield identical state hashes (D9).
    """

    def load_instance(self, instance_id: str) -> Instance:
        """Return a catalogued museum instance.

        Args:
            instance_id: ``museum.v0.<mission>.<variant>``.

        Returns:
            The matching instance.

        Raises:
            KeyError: If ``instance_id`` is unknown.
        """
        try:
            return INSTANCES[instance_id]
        except KeyError as exc:
            raise KeyError(f"unknown museum instance: {instance_id}") from exc

    def initial_state(self, instance: Instance) -> State:
        """Return the t=0 snapshot.

        The seed selects instance parameters only. Physics does not consult it.

        Args:
            instance: Catalogued instance (unused for the payload, required by
                the World protocol).

        Returns:
            Initial museum state.
        """
        del instance
        return initial_snapshot().to_state()

    def available_actions(self, state: State) -> Sequence[Action]:
        """Enumerate physically enabled actions in a stable order.

        Args:
            state: Current snapshot.

        Returns:
            Typed actions whose physics preconditions hold.
        """
        snap = view(state)
        actions: list[Action] = []
        for room in sorted(LOCATIONS):
            candidate = Action(type=ACTION_MOVE, args={"room": room})
            if self._preconditions_met(snap, candidate):
                actions.append(candidate)
        for door_id in sorted(DOORS):
            for kind in (ACTION_OPEN, ACTION_FORCE):
                candidate = Action(type=kind, args={"door": door_id})
                if self._preconditions_met(snap, candidate):
                    actions.append(candidate)
        for obj in sorted(OBJECTS):
            for kind in (ACTION_PICKUP, ACTION_DROP):
                candidate = Action(type=kind, args={"obj": obj})
                if self._preconditions_met(snap, candidate):
                    actions.append(candidate)
        for room in sorted(ROOMS):
            for op in (REGISTRY_ADD, REGISTRY_REMOVE):
                candidate = Action(type=ACTION_AMEND, args={"room": room, "op": op})
                if self._preconditions_met(snap, candidate):
                    actions.append(candidate)
        actions.append(Action(type=ACTION_WAIT, args={}))
        return actions

    def transition(self, state: State, action: Action) -> State:
        """Apply ``action``. Failed preconditions leave the state unchanged.

        Args:
            state: Source snapshot.
            action: Typed action.

        Returns:
            Successor snapshot.

        Raises:
            ValueError: If the action type is not one of the seven museum types.
        """
        if action.type not in {
            ACTION_MOVE,
            ACTION_OPEN,
            ACTION_FORCE,
            ACTION_PICKUP,
            ACTION_DROP,
            ACTION_AMEND,
            ACTION_WAIT,
        }:
            raise ValueError(f"unknown action type: {action.type!r}")
        snap = view(state)
        if action.type == ACTION_WAIT:
            return state
        if not self._preconditions_met(snap, action):
            return state
        return self._apply(snap, action).to_state()

    def render(self, state: State) -> str:
        """Render a one-screen text view of the museum.

        Args:
            state: Snapshot to print.

        Returns:
            Multi-line string. No UI dependency.
        """
        snap = view(state)
        carrying = ", ".join(sorted(snap.carrying)) or "(nothing)"
        registry = ", ".join(sorted(snap.registry))
        open_doors = ", ".join(
            door_id for door_id in sorted(snap.doors_open) if snap.doors_open[door_id]
        )
        lines = [
            f"Agent: {snap.agent_room}  carrying: {carrying}",
            f"Registry: {registry}",
        ]
        for obj in sorted(OBJECTS):
            carried = " (carried)" if obj in snap.carrying else ""
            lines.append(f"{obj}: {snap.loc(obj)}{carried}")
        lines.append(f"Doors open: {open_doors or '(none)'}")
        return "\n".join(lines) + "\n"

    def mission_for(self, instance: Instance):
        """Return the mission named by ``instance.mission_id``."""
        return mission_for_id(instance.mission_id)

    def _preconditions_met(self, snap: MuseumSnapshot, action: Action) -> bool:
        """Return whether physics allows ``action`` in ``snap``."""
        kind = action.type
        if kind == ACTION_MOVE:
            room = _require_str(action.args, "room")
            return _can_move(snap, room)
        if kind == ACTION_OPEN:
            door_id = _require_str(action.args, "door")
            return _can_open(snap, door_id)
        if kind == ACTION_FORCE:
            door_id = _require_str(action.args, "door")
            return _can_force(snap, door_id)
        if kind == ACTION_PICKUP:
            obj = _require_str(action.args, "obj")
            return _can_pickup(snap, obj)
        if kind == ACTION_DROP:
            obj = _require_str(action.args, "obj")
            return _can_drop(snap, obj)
        if kind == ACTION_AMEND:
            room = _require_str(action.args, "room")
            op = _require_str(action.args, "op")
            return _can_amend(snap, room, op)
        if kind == ACTION_WAIT:
            return True
        return False

    def _apply(self, snap: MuseumSnapshot, action: Action) -> MuseumSnapshot:
        """Return the successor of a precondition-satisfying action."""
        kind = action.type
        if kind == ACTION_MOVE:
            return MuseumSnapshot(
                agent_room=_require_str(action.args, "room"),
                carrying=snap.carrying,
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
            )
        if kind in {ACTION_OPEN, ACTION_FORCE}:
            door_id = _require_str(action.args, "door")
            doors_open = dict(snap.doors_open)
            doors_open[door_id] = True
            return MuseumSnapshot(
                agent_room=snap.agent_room,
                carrying=snap.carrying,
                object_rooms=dict(snap.object_rooms),
                doors_open=doors_open,
                registry=snap.registry,
            )
        if kind == ACTION_PICKUP:
            obj = _require_str(action.args, "obj")
            return MuseumSnapshot(
                agent_room=snap.agent_room,
                carrying=snap.carrying | {obj},
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
            )
        if kind == ACTION_DROP:
            obj = _require_str(action.args, "obj")
            object_rooms = dict(snap.object_rooms)
            object_rooms[obj] = snap.agent_room
            return MuseumSnapshot(
                agent_room=snap.agent_room,
                carrying=snap.carrying - {obj},
                object_rooms=object_rooms,
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
            )
        if kind == ACTION_AMEND:
            room = _require_str(action.args, "room")
            op = _require_str(action.args, "op")
            registry = set(snap.registry)
            if op == REGISTRY_ADD:
                registry.add(room)
            elif op == REGISTRY_REMOVE:
                registry.discard(room)
            return MuseumSnapshot(
                agent_room=snap.agent_room,
                carrying=snap.carrying,
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=frozenset(registry),
            )
        return snap


def _require_str(args: dict[str, object] | object, key: str) -> str:
    if not isinstance(args, dict):
        raise TypeError("action args must be a mapping")
    value = args[key]
    if not isinstance(value, str):
        raise TypeError(f"action arg {key!r} must be a string")
    return value


def _can_move(snap: MuseumSnapshot, room: str) -> bool:
    if room not in LOCATIONS or room == snap.agent_room:
        return False
    for door in DOORS.values():
        if door.connects(snap.agent_room, room) and snap.doors_open.get(door.door_id, False):
            return True
    return False


def _can_open(snap: MuseumSnapshot, door_id: str) -> bool:
    door = DOORS.get(door_id)
    if door is None or not door.incident(snap.agent_room):
        return False
    if not door.locked:
        return True
    return door.key is not None and door.key in snap.carrying


def _can_force(snap: MuseumSnapshot, door_id: str) -> bool:
    door = DOORS.get(door_id)
    if door is None or not door.incident(snap.agent_room):
        return False
    return door.locked


def _can_pickup(snap: MuseumSnapshot, obj: str) -> bool:
    if obj not in OBJECTS or obj in snap.carrying:
        return False
    return snap.loc(obj) == snap.agent_room


def _can_drop(snap: MuseumSnapshot, obj: str) -> bool:
    return obj in snap.carrying


def _can_amend(snap: MuseumSnapshot, room: str, op: str) -> bool:
    if snap.agent_room != ADMIN_ROOM:
        return False
    if room not in ROOMS or op not in REGISTRY_OPS:
        return False
    return True
