"""Deterministic two-actor museum physics. What is possible, not what is permitted.

Turn semantics (PLAN_MULTIAGENT.md M1, as amended by implementation finding F1):

- Every action carries ``args.actor``. An action by the non-active actor is an
  identity no-op: the frozen actor can affect neither the world nor the clock.
- Every **in-turn** action consumes the turn (toggles ``active``), whether or
  not its remaining preconditions hold. A failed in-turn attempt (e.g. a
  keyless ``open``) is effect-free but still passes the baton. Without this,
  an actor could fumble deliberately to deny the other actor all remaining
  turns, and strictly alternating traces containing legal failed attempts
  would be impossible to author.
- ``wait`` is the deliberate pass. Unlike the single-agent museum, it is NOT
  short-circuited before precondition checks: an out-of-turn ``wait`` must be
  an identity no-op, and an in-turn ``wait`` must toggle ``active``.
"""

from __future__ import annotations

from collections.abc import Sequence

from proofgym.core.types import Action, Instance, State
from proofgym.worlds.museum_duo_c4.constants import (
    ACTION_AMEND,
    ACTION_DROP,
    ACTION_FORCE,
    ACTION_MOVE,
    ACTION_OPEN,
    ACTION_PICKUP,
    ACTION_WAIT,
    ACTOR_E,
    ACTOR_H,
    ACTORS,
    ADMIN_ROOM,
    DOORS,
    LOCATIONS,
    OBJECTS,
    REGISTRY_ADD,
    REGISTRY_OPS,
    REGISTRY_REMOVE,
    ROOMS,
)
from proofgym.worlds.museum_duo_c4.instances import INSTANCES
from proofgym.worlds.museum_duo_c4.missions import mission_for_id
from proofgym.worlds.museum_duo_c4.state import MuseumDuoSnapshot, initial_snapshot, view

ACTION_TYPES: frozenset[str] = frozenset(
    {
        ACTION_MOVE,
        ACTION_OPEN,
        ACTION_FORCE,
        ACTION_PICKUP,
        ACTION_DROP,
        ACTION_AMEND,
        ACTION_WAIT,
    }
)


def other_actor(actor: str) -> str:
    """Return the actor opposite ``actor``.

    Args:
        actor: ``E`` or ``H``.

    Returns:
        The other actor id.

    Raises:
        ValueError: If ``actor`` is unknown.
    """
    if actor == ACTOR_E:
        return ACTOR_H
    if actor == ACTOR_H:
        return ACTOR_E
    raise ValueError(f"unknown actor: {actor!r}")


class MuseumDuoWorld:
    """Six-room graph world with two actors on a strict alternating schedule.

    Transition is total: unknown action types or actors raise; an out-of-turn
    action is an identity no-op; an in-turn action always toggles ``active``
    and applies its effects only when its preconditions hold. Same instance +
    same actions yield identical state hashes (D9).
    """

    def load_instance(self, instance_id: str) -> Instance:
        """Return a catalogued duo instance.

        Args:
            instance_id: ``museum_duo.v1c.<mission>.<variant>``.

        Returns:
            The matching instance.

        Raises:
            KeyError: If ``instance_id`` is unknown.
        """
        try:
            return INSTANCES[instance_id]
        except KeyError as exc:
            raise KeyError(f"unknown museum_duo_c4 instance: {instance_id}") from exc

    def initial_state(self, instance: Instance) -> State:
        """Return the t=0 snapshot.

        The seed selects instance parameters only. Physics does not consult it.

        Args:
            instance: Catalogued instance (unused for the payload, required by
                the World protocol).

        Returns:
            Initial duo museum state.
        """
        del instance
        return initial_snapshot().to_state()

    def available_actions(self, state: State) -> Sequence[Action]:
        """Enumerate effect-capable actions for the active actor, stable order.

        Args:
            state: Current snapshot.

        Returns:
            Typed actions (tagged with the active actor) whose physics
            preconditions hold, plus ``wait``.
        """
        snap = view(state)
        actor = snap.active
        actions: list[Action] = []
        for room in sorted(LOCATIONS):
            candidate = Action(type=ACTION_MOVE, args={"actor": actor, "room": room})
            if self._preconditions_met(snap, actor, candidate):
                actions.append(candidate)
        for door_id in sorted(DOORS):
            for kind in (ACTION_OPEN, ACTION_FORCE):
                candidate = Action(type=kind, args={"actor": actor, "door": door_id})
                if self._preconditions_met(snap, actor, candidate):
                    actions.append(candidate)
        for obj in sorted(OBJECTS):
            for kind in (ACTION_PICKUP, ACTION_DROP):
                candidate = Action(type=kind, args={"actor": actor, "obj": obj})
                if self._preconditions_met(snap, actor, candidate):
                    actions.append(candidate)
        for room in sorted(ROOMS):
            for op in (REGISTRY_ADD, REGISTRY_REMOVE):
                candidate = Action(type=ACTION_AMEND, args={"actor": actor, "room": room, "op": op})
                if self._preconditions_met(snap, actor, candidate):
                    actions.append(candidate)
        actions.append(Action(type=ACTION_WAIT, args={"actor": actor}))
        return actions

    def transition(self, state: State, action: Action) -> State:
        """Apply ``action`` under the M1 turn semantics.

        Args:
            state: Source snapshot.
            action: Typed action carrying ``args.actor``.

        Returns:
            Successor snapshot. Identity when the action is out of turn;
            toggle-only when an in-turn attempt fails its preconditions.

        Raises:
            ValueError: If the action type or actor is not in the vocabulary.
            KeyError: If ``args.actor`` is missing.
            TypeError: If ``args.actor`` is not a string.
        """
        if action.type not in ACTION_TYPES:
            raise ValueError(f"unknown action type: {action.type!r}")
        actor = _require_str(action.args, "actor")
        if actor not in ACTORS:
            raise ValueError(f"unknown actor: {actor!r}")
        snap = view(state)
        if actor != snap.active:
            return state
        if action.type != ACTION_WAIT and self._preconditions_met(snap, actor, action):
            return self._apply(snap, actor, action).to_state()
        return _pass_turn(snap).to_state()

    def render(self, state: State) -> str:
        """Render a one-screen text view of the duo museum.

        Args:
            state: Snapshot to print.

        Returns:
            Multi-line string. No UI dependency.
        """
        snap = view(state)
        registry = ", ".join(sorted(snap.registry))
        open_doors = ", ".join(
            door_id for door_id in sorted(snap.doors_open) if snap.doors_open[door_id]
        )
        lines: list[str] = []
        for actor in ACTORS:
            carrying = ", ".join(sorted(snap.carrying[actor])) or "(nothing)"
            marker = " *active*" if actor == snap.active else ""
            lines.append(f"Agent {actor}: {snap.agent_rooms[actor]}  carrying: {carrying}{marker}")
        lines.append(f"Registry: {registry}")
        for obj in sorted(OBJECTS):
            carrier = snap.carrier_of(obj)
            suffix = f" (carried by {carrier})" if carrier is not None else ""
            lines.append(f"{obj}: {snap.loc(obj)}{suffix}")
        lines.append(f"Doors open: {open_doors or '(none)'}")
        return "\n".join(lines) + "\n"

    def mission_for(self, instance: Instance):
        """Return the mission named by ``instance.mission_id``."""
        return mission_for_id(instance.mission_id)

    def _preconditions_met(self, snap: MuseumDuoSnapshot, actor: str, action: Action) -> bool:
        """Return whether physics allows ``action`` by ``actor`` in ``snap``.

        The actor-matches-``active`` check is NOT included here; callers apply
        it first (an out-of-turn action is identity, not a fumble).
        """
        kind = action.type
        if kind == ACTION_MOVE:
            room = _require_str(action.args, "room")
            return _can_move(snap, actor, room)
        if kind == ACTION_OPEN:
            door_id = _require_str(action.args, "door")
            return _can_open(snap, actor, door_id)
        if kind == ACTION_FORCE:
            door_id = _require_str(action.args, "door")
            return _can_force(snap, actor, door_id)
        if kind == ACTION_PICKUP:
            obj = _require_str(action.args, "obj")
            return _can_pickup(snap, actor, obj)
        if kind == ACTION_DROP:
            obj = _require_str(action.args, "obj")
            return _can_drop(snap, actor, obj)
        if kind == ACTION_AMEND:
            room = _require_str(action.args, "room")
            op = _require_str(action.args, "op")
            return _can_amend(snap, actor, room, op)
        if kind == ACTION_WAIT:
            return True
        return False

    def _apply(self, snap: MuseumDuoSnapshot, actor: str, action: Action) -> MuseumDuoSnapshot:
        """Return the successor of a precondition-satisfying in-turn action."""
        kind = action.type
        nxt = other_actor(actor)
        if kind == ACTION_MOVE:
            agent_rooms = dict(snap.agent_rooms)
            agent_rooms[actor] = _require_str(action.args, "room")
            return MuseumDuoSnapshot(
                agent_rooms=agent_rooms,
                carrying=dict(snap.carrying),
                active=nxt,
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
                amended_by=snap.amended_by,
            )
        if kind in {ACTION_OPEN, ACTION_FORCE}:
            door_id = _require_str(action.args, "door")
            doors_open = dict(snap.doors_open)
            doors_open[door_id] = True
            return MuseumDuoSnapshot(
                agent_rooms=dict(snap.agent_rooms),
                carrying=dict(snap.carrying),
                active=nxt,
                object_rooms=dict(snap.object_rooms),
                doors_open=doors_open,
                registry=snap.registry,
                amended_by=snap.amended_by,
            )
        if kind == ACTION_PICKUP:
            obj = _require_str(action.args, "obj")
            carrying = dict(snap.carrying)
            carrying[actor] = snap.carrying[actor] | {obj}
            return MuseumDuoSnapshot(
                agent_rooms=dict(snap.agent_rooms),
                carrying=carrying,
                active=nxt,
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
                amended_by=snap.amended_by,
            )
        if kind == ACTION_DROP:
            obj = _require_str(action.args, "obj")
            carrying = dict(snap.carrying)
            carrying[actor] = snap.carrying[actor] - {obj}
            object_rooms = dict(snap.object_rooms)
            object_rooms[obj] = snap.agent_rooms[actor]
            return MuseumDuoSnapshot(
                agent_rooms=dict(snap.agent_rooms),
                carrying=carrying,
                active=nxt,
                object_rooms=object_rooms,
                doors_open=dict(snap.doors_open),
                registry=snap.registry,
                amended_by=snap.amended_by,
            )
        if kind == ACTION_AMEND:
            room = _require_str(action.args, "room")
            op = _require_str(action.args, "op")
            registry = set(snap.registry)
            if op == REGISTRY_ADD:
                registry.add(room)
            elif op == REGISTRY_REMOVE:
                registry.discard(room)
            return MuseumDuoSnapshot(
                agent_rooms=dict(snap.agent_rooms),
                carrying=dict(snap.carrying),
                active=nxt,
                object_rooms=dict(snap.object_rooms),
                doors_open=dict(snap.doors_open),
                registry=frozenset(registry),
                amended_by=snap.amended_by | {actor},
            )
        return _pass_turn(snap)


def _pass_turn(snap: MuseumDuoSnapshot) -> MuseumDuoSnapshot:
    """Return ``snap`` with only the turn pointer advanced (a pass or fumble)."""
    return MuseumDuoSnapshot(
        agent_rooms=dict(snap.agent_rooms),
        carrying=dict(snap.carrying),
        active=other_actor(snap.active),
        object_rooms=dict(snap.object_rooms),
        doors_open=dict(snap.doors_open),
        registry=snap.registry,
        amended_by=snap.amended_by,
    )


def _require_str(args: dict[str, object] | object, key: str) -> str:
    if not isinstance(args, dict):
        raise TypeError("action args must be a mapping")
    value = args[key]
    if not isinstance(value, str):
        raise TypeError(f"action arg {key!r} must be a string")
    return value


def _can_move(snap: MuseumDuoSnapshot, actor: str, room: str) -> bool:
    here = snap.agent_rooms[actor]
    if room not in LOCATIONS or room == here:
        return False
    for door in DOORS.values():
        if door.connects(here, room) and snap.doors_open.get(door.door_id, False):
            return True
    return False


def _can_open(snap: MuseumDuoSnapshot, actor: str, door_id: str) -> bool:
    door = DOORS.get(door_id)
    if door is None or not door.incident(snap.agent_rooms[actor]):
        return False
    if not door.locked:
        return True
    return door.key is not None and door.key in snap.carrying[actor]


def _can_force(snap: MuseumDuoSnapshot, actor: str, door_id: str) -> bool:
    door = DOORS.get(door_id)
    if door is None or not door.incident(snap.agent_rooms[actor]):
        return False
    return door.locked


def _can_pickup(snap: MuseumDuoSnapshot, actor: str, obj: str) -> bool:
    if obj not in OBJECTS:
        return False
    # No stealing: an object carried by anyone (including the other actor)
    # cannot be picked up (PLAN_MULTIAGENT.md §4.3).
    if snap.carrier_of(obj) is not None:
        return False
    return snap.loc(obj) == snap.agent_rooms[actor]


def _can_drop(snap: MuseumDuoSnapshot, actor: str, obj: str) -> bool:
    return obj in snap.carrying[actor]


def _can_amend(snap: MuseumDuoSnapshot, actor: str, room: str, op: str) -> bool:
    if snap.agent_rooms[actor] != ADMIN_ROOM:
        return False
    if room not in ROOMS or op not in REGISTRY_OPS:
        return False
    return True
