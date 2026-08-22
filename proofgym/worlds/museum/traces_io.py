"""Load and seal the gold traces under ``worlds/museum/traces/``.

Gold traces come in two groups: the four PLAN.md §4.7 reference traces on the
v0 instances, and the stage-2 ``patched_*`` traces on the patched-constitution
heist instance. Each sealed JSON records the constitution id its instance is
evaluated under.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from proofgym.core.replay import replay
from proofgym.core.serialize import dump_trace, load_trace, trace_from_dict, trace_to_dict
from proofgym.core.types import ENGINE_VERSION, Trace, TraceStep
from proofgym.worlds.museum.constitution import constitution_for_instance
from proofgym.worlds.museum.instances import INSTANCES
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.sequences import REFERENCE_TRACES

TRACE_PACKAGE = "proofgym.worlds.museum"
TRACE_DIRNAME = "traces"
REFERENCE_TRACE_NAMES: tuple[str, ...] = (
    "honest_errand",
    "registry_heist",
    "forced_door",
    "lost_visitor",
)
PATCHED_TRACE_NAMES: tuple[str, ...] = (
    "patched_registry_walkout",
    "patched_forced_door",
    "patched_returned_diamond",
)
GOLD_TRACE_NAMES: tuple[str, ...] = REFERENCE_TRACE_NAMES + PATCHED_TRACE_NAMES


def traces_dir() -> Path:
    """Return the on-disk traces directory (source tree or installed package)."""
    return Path(str(files(TRACE_PACKAGE).joinpath(TRACE_DIRNAME)))


def reference_trace_names() -> tuple[str, ...]:
    """Return the four PLAN.md §4.7 trace ids in report order."""
    return REFERENCE_TRACE_NAMES


def gold_trace_names() -> tuple[str, ...]:
    """Return all sealed gold trace ids: reference traces, then patched traces."""
    return GOLD_TRACE_NAMES


def load_reference_trace(name: str) -> Trace:
    """Load a sealed gold trace by stem name.

    Args:
        name: One of :func:`gold_trace_names`.

    Returns:
        Parsed trace.

    Raises:
        FileNotFoundError: If the JSON file is missing.
        KeyError: If ``name`` is not a gold trace.
    """
    if name not in GOLD_TRACE_NAMES:
        raise KeyError(f"unknown gold trace: {name}")
    path = traces_dir() / f"{name}.json"
    return load_trace(path)


def build_reference_trace(name: str) -> Trace:
    """Build a sealed trace (actions + recomputed hashes) from the sequence table.

    Args:
        name: Gold trace id.

    Returns:
        Trace with integrity hashes from a deterministic replay. The recorded
        constitution id is the one the trace's instance is evaluated under.

    Raises:
        KeyError: If ``name`` is unknown.
    """
    instance_id, agent_id, actions = REFERENCE_TRACES[name]
    _, constitution_id = constitution_for_instance(INSTANCES[instance_id])
    steps = tuple(TraceStep(action=action, executed=True) for action in actions)
    unsigned = Trace(
        instance_id=instance_id,
        engine_version=ENGINE_VERSION,
        constitution_id=constitution_id,
        seed=0,
        steps=steps,
        state_hashes=(),
        meta={"agent_id": agent_id, "trace_id": name},
    )
    world = MuseumWorld()
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
    """Write every sealed gold trace JSON to ``directory``.

    Args:
        directory: Destination. Defaults to the package traces folder.

    Returns:
        Paths written.
    """
    target = directory if directory is not None else traces_dir()
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in GOLD_TRACE_NAMES:
        path = target / f"{name}.json"
        dump_trace(build_reference_trace(name), path)
        written.append(path)
    return written


# Re-export for callers that want a dict view of a freshly built trace.
__all__ = [
    "GOLD_TRACE_NAMES",
    "PATCHED_TRACE_NAMES",
    "REFERENCE_TRACE_NAMES",
    "build_reference_trace",
    "gold_trace_names",
    "load_reference_trace",
    "reference_trace_names",
    "trace_from_dict",
    "trace_to_dict",
    "traces_dir",
    "write_reference_traces",
]
