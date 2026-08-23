"""Coalition-requiring duo museum (C4): copy-on-write sibling of ``museum_duo``.

Option B of ``docs/DUO_C4_DESIGN.md`` §3.2: a sibling package so sealed
``museum_duo`` v0 hashes stay byte-identical. State carries ``amended_by``;
the public law is ``museum_duo_public.v1_coalition`` (C1–C3 verbatim + C4).
``core``, ``worlds/museum/``, and ``worlds/museum_duo/`` are untouched.
"""

from proofgym.worlds.museum_duo_c4.constitution import (
    CONSTITUTION_ID,
    public_constitution,
)
from proofgym.worlds.museum_duo_c4.instances import INSTANCES
from proofgym.worlds.museum_duo_c4.intent import MuseumDuoIntentOracle
from proofgym.worlds.museum_duo_c4.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo_c4.traces_io import load_reference_trace, reference_trace_names

__all__ = [
    "CONSTITUTION_ID",
    "INSTANCES",
    "MuseumDuoIntentOracle",
    "MuseumDuoWorld",
    "load_reference_trace",
    "public_constitution",
    "reference_trace_names",
]
