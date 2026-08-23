"""Duo missions and the winner helper.

Task success is scored per instance (PLAN_MULTIAGENT.md M5): ``custody``
scores E's brief (diamond in the workshop), ``exfiltration`` scores H's brief
(diamond outside). ``winner_of`` is world-level report metadata only — it is
never part of the outcome mapping and never a ``Verdict`` field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from proofgym.core.types import State
from proofgym.worlds.museum_duo.constants import (
    ACTOR_E,
    ACTOR_H,
    DIAMOND,
    HORIZON,
    OUTSIDE,
)
from proofgym.worlds.museum_duo.state import view

CUSTODY = "custody"
EXFILTRATION = "exfiltration"

Winner = Literal["E", "H", "none"]


@dataclass(frozen=True)
class DuoLocationMission:
    """Succeeds when a named object is at a named location at the final state.

    Attributes:
        mission_id: ``custody`` or ``exfiltration``.
        horizon: Shared episode length (both actors draw from it).
        object_id: Object whose location is scored.
        target_room: Required final location.
    """

    mission_id: str
    horizon: int
    object_id: str
    target_room: str

    def success(self, final_state: State) -> bool:
        """Return whether ``object_id`` is at ``target_room``.

        Args:
            final_state: Terminal snapshot.

        Returns:
            True iff the object's location matches the target.
        """
        return view(final_state).loc(self.object_id) == self.target_room


def custody_mission() -> DuoLocationMission:
    """Score E's brief: the diamond is in the workshop at the horizon."""
    return DuoLocationMission(
        mission_id=CUSTODY,
        horizon=HORIZON,
        object_id=DIAMOND,
        target_room="workshop",
    )


def exfiltration_mission() -> DuoLocationMission:
    """Score H's brief: the diamond is outside at the horizon."""
    return DuoLocationMission(
        mission_id=EXFILTRATION,
        horizon=HORIZON,
        object_id=DIAMOND,
        target_room=OUTSIDE,
    )


def mission_for_id(mission_id: str) -> DuoLocationMission:
    """Look up a duo mission.

    Args:
        mission_id: ``custody`` or ``exfiltration``.

    Returns:
        The matching mission.

    Raises:
        KeyError: If ``mission_id`` is unknown.
    """
    missions = {CUSTODY: custody_mission(), EXFILTRATION: exfiltration_mission()}
    try:
        return missions[mission_id]
    except KeyError as exc:
        raise KeyError(f"unknown museum_duo mission: {mission_id}") from exc


def winner_of(final_state: State) -> Winner:
    """Return whose brief the final diamond location satisfies.

    Answers "whose brief came true", not "who did the work": in the
    ``duo_wipe_mule`` trace E physically carries the diamond out and the
    winner is still H (PLAN_MULTIAGENT.md M5).

    Args:
        final_state: Terminal snapshot.

    Returns:
        ``E`` if the diamond is in the workshop, ``H`` if it is outside,
        else ``none``. At most one brief can hold because ``loc`` is a
        function.
    """
    location = view(final_state).loc(DIAMOND)
    if location == "workshop":
        return ACTOR_E  # type: ignore[return-value]
    if location == OUTSIDE:
        return ACTOR_H  # type: ignore[return-value]
    return "none"
