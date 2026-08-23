"""Two-agent museum (duo): same map and law, two actors, strict alternation.

Copy-on-write sibling of ``worlds/museum`` per PLAN_MULTIAGENT.md M8: the map,
objects, clause texts, and intent formulas are verbatim; the state schema,
physics, and encodings are re-implemented for two actors. ``core`` and the
single-agent museum are untouched.
"""

from proofgym.worlds.museum_duo.constitution import (
    CONSTITUTION_ID,
    public_constitution,
)
from proofgym.worlds.museum_duo.instances import INSTANCES
from proofgym.worlds.museum_duo.intent import MuseumDuoIntentOracle
from proofgym.worlds.museum_duo.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo.traces_io import load_reference_trace, reference_trace_names

__all__ = [
    "CONSTITUTION_ID",
    "INSTANCES",
    "MuseumDuoIntentOracle",
    "MuseumDuoWorld",
    "load_reference_trace",
    "public_constitution",
    "reference_trace_names",
]
