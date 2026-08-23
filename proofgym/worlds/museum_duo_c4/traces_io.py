"""Load and seal the duo C4 reference traces under ``worlds/museum_duo_c4/traces/``."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from proofgym.core.replay import replay
from proofgym.core.serialize import dump_trace, load_trace, trace_from_dict, trace_to_dict
from proofgym.core.types import ENGINE_VERSION, Trace, TraceStep
from proofgym.worlds.museum_duo_c4.constants import ACTOR_E, ACTOR_H
from proofgym.worlds.museum_duo_c4.constitution import CONSTITUTION_ID
from proofgym.worlds.museum_duo_c4.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo_c4.sequences import REFERENCE_TRACES

TRACE_PACKAGE = "proofgym.worlds.museum_duo_c4"
TRACE_DIRNAME = "traces"
REFERENCE_TRACE_NAMES: tuple[str, ...] = (
    "duo_c4_wipe_mule",
    "duo_c4_solo_steal_first",
    "duo_c4_solo_amend_first",
    "duo_c4_relay",
    "duo_c4_honest_custody",
    "duo_c4_wipe_mule_flipped",
)


def traces_dir() -> Path:
    """Return the on-disk traces directory (source tree or installed package)."""
    return Path(str(files(TRACE_PACKAGE).joinpath(TRACE_DIRNAME)))


def reference_trace_names() -> tuple[str, ...]:
    """Return the DUO_C4_DESIGN.md §2.2 trace ids in report order."""
    return REFERENCE_TRACE_NAMES


def load_reference_trace(name: str) -> Trace:
    """Load a sealed reference trace by stem name."""
    if name not in REFERENCE_TRACE_NAMES:
        raise KeyError(f"unknown reference trace: {name}")
    path = traces_dir() / f"{name}.json"
    return load_trace(path)


def build_reference_trace(name: str) -> Trace:
    """Build a sealed trace (actions + recomputed hashes) from the sequence table."""
    instance_id, agent_id, actions = REFERENCE_TRACES[name]
    steps = tuple(TraceStep(action=action, executed=True) for action in actions)
    unsigned = Trace(
        instance_id=instance_id,
        engine_version=ENGINE_VERSION,
        constitution_id=CONSTITUTION_ID,
        seed=0,
        steps=steps,
        state_hashes=(),
        meta={
            "agent_id": agent_id,
            "trace_id": name,
            "roster": {ACTOR_E: "scripted", ACTOR_H: "scripted"},
        },
    )
    world = MuseumDuoWorld()
    states = replay(world, unsigned, verify_hashes=False)
    return Trace(
        instance_id=unsigned.instance_id,
        engine_version=unsigned.engine_version,
        constitution_id=unsigned.constitution_id,
        seed=unsigned.seed,
        steps=unsigned.steps,
        state_hashes=tuple(state.state_hash() for state in states),
        meta=unsigned.meta,
    )


def write_reference_traces(directory: Path | None = None) -> list[Path]:
    """Write the sealed JSON traces to ``directory``."""
    target = directory if directory is not None else traces_dir()
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in REFERENCE_TRACE_NAMES:
        path = target / f"{name}.json"
        dump_trace(build_reference_trace(name), path)
        written.append(path)
    return written


__all__ = [
    "REFERENCE_TRACE_NAMES",
    "build_reference_trace",
    "load_reference_trace",
    "reference_trace_names",
    "trace_from_dict",
    "trace_to_dict",
    "traces_dir",
    "write_reference_traces",
]
