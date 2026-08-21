"""Trace serialization. Verdicts are derived and are never stored in a trace."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from proofgym.core.types import Trace, TraceStep


def trace_to_dict(trace: Trace) -> dict[str, Any]:
    """Convert a trace to a JSON-ready mapping.

    Args:
        trace: In-memory trace.

    Returns:
        Mapping matching PLAN.md §5.2.
    """
    return {
        "instance_id": trace.instance_id,
        "engine_version": trace.engine_version,
        "constitution_id": trace.constitution_id,
        "seed": trace.seed,
        "steps": [step.to_dict() for step in trace.steps],
        "state_hashes": list(trace.state_hashes),
        "meta": dict(trace.meta),
    }


def trace_from_dict(data: Mapping[str, Any]) -> Trace:
    """Parse a trace from a mapping.

    Args:
        data: Serialized trace.

    Returns:
        Parsed trace.

    Raises:
        KeyError: If a required field is missing.
        TypeError: If a field has the wrong type.
    """
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list):
        raise TypeError("steps must be a list")
    steps = tuple(TraceStep.from_dict(step) for step in raw_steps)
    hashes = data.get("state_hashes", [])
    if hashes is None:
        hashes = []
    if not isinstance(hashes, list) or not all(isinstance(item, str) for item in hashes):
        raise TypeError("state_hashes must be a list of strings")
    meta = data.get("meta", {})
    if meta is None:
        meta = {}
    if not isinstance(meta, Mapping):
        raise TypeError("meta must be a mapping")
    return Trace(
        instance_id=str(data["instance_id"]),
        engine_version=str(data["engine_version"]),
        constitution_id=str(data["constitution_id"]),
        seed=int(data["seed"]),
        steps=steps,
        state_hashes=tuple(hashes),
        meta=meta,
    )


def load_trace(path: str | Path) -> Trace:
    """Load a trace from a JSON file.

    Args:
        path: Filesystem path.

    Returns:
        Parsed trace.

    Raises:
        OSError: If the file cannot be read.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    text = Path(path).read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise TypeError("trace JSON must be an object")
    return trace_from_dict(payload)


def dump_trace(trace: Trace, path: str | Path) -> None:
    """Write a trace to a JSON file.

    Args:
        trace: In-memory trace.
        path: Destination path. Parent directories are created as needed.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(trace_to_dict(trace), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
