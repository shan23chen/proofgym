"""Trace (de)serialization round-trips."""

from __future__ import annotations

import json
from pathlib import Path

from proofgym.core.serialize import dump_trace, load_trace, trace_from_dict, trace_to_dict
from proofgym.worlds.museum.traces_io import load_reference_trace, reference_trace_names


def test_trace_dict_roundtrip() -> None:
    """dict → Trace → dict preserves actions, hashes, and meta."""
    for name in reference_trace_names():
        original = load_reference_trace(name)
        restored = trace_from_dict(trace_to_dict(original))
        assert restored.instance_id == original.instance_id
        assert restored.engine_version == original.engine_version
        assert restored.constitution_id == original.constitution_id
        assert restored.seed == original.seed
        assert restored.state_hashes == original.state_hashes
        assert restored.meta == original.meta
        assert len(restored.steps) == len(original.steps)
        for left, right in zip(restored.steps, original.steps, strict=True):
            assert left.action == right.action
            assert left.executed == right.executed


def test_trace_file_roundtrip(tmp_path: Path) -> None:
    """JSON file dump/load preserves a reference trace."""
    original = load_reference_trace("registry_heist")
    path = tmp_path / "registry_heist.json"
    dump_trace(original, path)
    restored = load_trace(path)
    assert restored == original
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["instance_id"] == "museum.v0.heist.base"
    assert payload["steps"][0]["action"]["type"] == "amend_registry"
