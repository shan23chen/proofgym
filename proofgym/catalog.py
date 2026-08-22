"""Named world bundles for the harness. ``core`` does not import this module."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from proofgym.core.protocols import Clause, IntentOracle, World
from proofgym.core.types import Instance, State
from proofgym.play.debrief import DebriefProvider
from proofgym.worlds.museum.constitution import constitution_for_instance
from proofgym.worlds.museum.debrief import MuseumDebrief
from proofgym.worlds.museum.instances import instance_for_mission
from proofgym.worlds.museum.intent import MuseumIntentOracle
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.public import observe, state_from_observation, task_markdown


class PublicManual(Protocol):
    """Player-visible manual and observation for one world."""

    def task_markdown(self, *, mission_id: str, horizon: int) -> str:
        """Return TASK.md contents (public constitution text, no I*)."""

    def observe(
        self,
        state: State,
        *,
        step: int,
        horizon: int,
        done: bool,
        last_feedback: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Project physics into the player-visible ``state.json``."""

    def state_from_observation(self, observation: Mapping[str, Any]) -> State:
        """Rebuild physics from a player observation."""


@dataclass(frozen=True)
class _CallableManual:
    """Adapter turning module-level functions into a ``PublicManual``."""

    _task: Callable[..., str]
    _observe: Callable[..., dict[str, Any]]
    _restore: Callable[..., State]

    def task_markdown(self, *, mission_id: str, horizon: int) -> str:
        """Return TASK.md contents."""
        return self._task(mission_id=mission_id, horizon=horizon)

    def observe(
        self,
        state: State,
        *,
        step: int,
        horizon: int,
        done: bool,
        last_feedback: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Project physics into the player-visible observation."""
        return self._observe(
            state,
            step=step,
            horizon=horizon,
            done=done,
            last_feedback=last_feedback,
        )

    def state_from_observation(self, observation: Mapping[str, Any]) -> State:
        """Rebuild physics from a player observation."""
        return self._restore(observation)


@dataclass(frozen=True)
class WorldBundle:
    """Everything the harness needs to run one world, including hidden I*.

    The player workspace is built only from ``manual`` plus public instance
    fields (mission id, horizon). Intent and instance parameters stay here.
    A world may ship several constitution versions (for example the flawed v0
    and the patched v1); ``constitution_for_instance`` resolves which one an
    instance is played and evaluated under.
    """

    name: str
    world: World
    constitution_for_instance: Callable[[Instance], tuple[Sequence[Clause], str]]
    intent: IntentOracle
    manual: PublicManual
    instance_for_mission: Callable[[str], Instance]
    debrief: DebriefProvider


def load_bundle(name: str) -> WorldBundle:
    """Load a named world bundle.

    Args:
        name: World id. The pilot ships ``museum`` only.

    Returns:
        Bundle with physics, constitution resolver, hidden intent, and manual.

    Raises:
        KeyError: If ``name`` is unknown.
    """
    if name != "museum":
        raise KeyError(f"unknown world: {name}")
    return WorldBundle(
        name="museum",
        world=MuseumWorld(),
        constitution_for_instance=constitution_for_instance,
        intent=MuseumIntentOracle(),
        manual=_CallableManual(task_markdown, observe, state_from_observation),
        instance_for_mission=instance_for_mission,
        debrief=MuseumDebrief(),
    )
