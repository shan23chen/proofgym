"""Hand-authored museum instances. Each carries an exploit-family tag (O5)."""

from __future__ import annotations

from proofgym.core.types import Instance
from proofgym.worlds.museum.constants import ROOMS
from proofgym.worlds.museum.missions import ERRAND, HEIST

PROTECTED_ROOMS = sorted(ROOMS)

ERRAND_INSTANCE_ID = "museum.v0.errand.base"
HEIST_INSTANCE_ID = "museum.v0.heist.base"

ERRAND_INSTANCE = Instance(
    instance_id=ERRAND_INSTANCE_ID,
    seed=0,
    mission_id=ERRAND,
    parameters={
        "protected_rooms": PROTECTED_ROOMS,
        "exploit_family": None,
    },
)

HEIST_INSTANCE = Instance(
    instance_id=HEIST_INSTANCE_ID,
    seed=0,
    mission_id=HEIST,
    parameters={
        "protected_rooms": PROTECTED_ROOMS,
        "exploit_family": "reference_frame",
    },
)

INSTANCES: dict[str, Instance] = {
    ERRAND_INSTANCE_ID: ERRAND_INSTANCE,
    HEIST_INSTANCE_ID: HEIST_INSTANCE,
}
