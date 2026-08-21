"""Shared fixtures for the museum pilot tests."""

from __future__ import annotations

import pytest

from proofgym.core.types import Trace
from proofgym.worlds.museum.constitution import public_constitution
from proofgym.worlds.museum.intent import MuseumIntentOracle
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.traces_io import load_reference_trace, reference_trace_names


@pytest.fixture
def world() -> MuseumWorld:
    """Return a museum world."""
    return MuseumWorld()


@pytest.fixture
def constitution():
    """Return the public C1–C3 clause tuple."""
    return public_constitution()


@pytest.fixture
def intent() -> MuseumIntentOracle:
    """Return the hidden museum intent oracle."""
    return MuseumIntentOracle()


@pytest.fixture
def reference_traces() -> dict[str, Trace]:
    """Load the four sealed reference traces."""
    return {name: load_reference_trace(name) for name in reference_trace_names()}
