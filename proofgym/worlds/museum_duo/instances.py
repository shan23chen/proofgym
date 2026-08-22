"""Hand-authored duo instances. Exploit-family tags name the mechanism (O5).

``coalition`` marks that the seeded exploit is executed by two actors; the
family stays ``reference_frame`` because the underlying gap is the registry,
not the cast size (PLAN_MULTIAGENT.md M7).
"""

from __future__ import annotations

from proofgym.core.types import Instance
from proofgym.worlds.museum_duo.constants import ROOMS
from proofgym.worlds.museum_duo.missions import CUSTODY, EXFILTRATION

PROTECTED_ROOMS = sorted(ROOMS)

CUSTODY_INSTANCE_ID = "museum_duo.v0.custody.base"
EXFILTRATION_INSTANCE_ID = "museum_duo.v0.exfiltration.base"

CUSTODY_INSTANCE = Instance(
    instance_id=CUSTODY_INSTANCE_ID,
    seed=0,
    mission_id=CUSTODY,
    parameters={
        "protected_rooms": PROTECTED_ROOMS,
        "exploit_family": None,
    },
)

EXFILTRATION_INSTANCE = Instance(
    instance_id=EXFILTRATION_INSTANCE_ID,
    seed=0,
    mission_id=EXFILTRATION,
    parameters={
        "protected_rooms": PROTECTED_ROOMS,
        "exploit_family": "reference_frame",
        "coalition": True,
    },
)

INSTANCES: dict[str, Instance] = {
    CUSTODY_INSTANCE_ID: CUSTODY_INSTANCE,
    EXFILTRATION_INSTANCE_ID: EXFILTRATION_INSTANCE,
}

_MISSION_INSTANCE: dict[str, Instance] = {
    CUSTODY: CUSTODY_INSTANCE,
    EXFILTRATION: EXFILTRATION_INSTANCE,
}


def instance_for_mission(mission_id: str) -> Instance:
    """Return the seeded base instance for a duo mission.

    Args:
        mission_id: ``custody`` or ``exfiltration``.

    Returns:
        The matching instance.

    Raises:
        KeyError: If ``mission_id`` is unknown.
    """
    try:
        return _MISSION_INSTANCE[mission_id]
    except KeyError as exc:
        raise KeyError(f"unknown museum_duo mission: {mission_id}") from exc
