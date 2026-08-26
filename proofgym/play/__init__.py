"""Filesystem-first play protocol for coding-CLI players.

The public conveniences are loaded lazily so importing a lower-level
``proofgym.play`` module does not pull the harness back through the world
catalog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from proofgym.play.harness import RunRecord
    from proofgym.play.session import PlaySession

__all__ = [
    "PlaySession",
    "RunRecord",
    "compare_records",
    "run_episode",
]


def __getattr__(name: str) -> Any:
    """Resolve the package-level API without creating catalog import cycles."""
    if name == "PlaySession":
        from proofgym.play.session import PlaySession

        return PlaySession
    if name in {"RunRecord", "compare_records", "run_episode"}:
        from proofgym.play import harness

        return getattr(harness, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
