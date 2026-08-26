"""Named world bundles for the harness. ``core`` does not import this module."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from proofgym.core.protocols import Clause, IntentOracle, World
from proofgym.core.types import Instance, State
from proofgym.worlds.museum.constitution import constitution_for_instance
from proofgym.worlds.museum.debrief import MuseumDebrief
from proofgym.worlds.museum.instances import instance_for_mission
from proofgym.worlds.museum.intent import MuseumIntentOracle
from proofgym.worlds.museum.physics import MuseumWorld
from proofgym.worlds.museum.public import observe, state_from_observation, task_markdown
from proofgym.worlds.museum_duo.constitution import (
    constitution_for_instance as duo_constitution_for_instance,
)
from proofgym.worlds.museum_duo.debrief import MuseumDuoDebrief
from proofgym.worlds.museum_duo.instances import instance_for_mission as duo_instance_for_mission
from proofgym.worlds.museum_duo.intent import MuseumDuoIntentOracle
from proofgym.worlds.museum_duo.physics import MuseumDuoWorld
from proofgym.worlds.museum_duo.public import (
    observe as duo_observe,
)
from proofgym.worlds.museum_duo.public import (
    state_from_observation as duo_state_from_observation,
)
from proofgym.worlds.museum_duo.public import (
    task_markdown as duo_task_markdown,
)

if TYPE_CHECKING:
    from proofgym.play.debrief import DebriefProvider


class PublicManual(Protocol):
    """Player-visible manual and observation for one world."""

    def task_markdown(
        self,
        *,
        mission_id: str,
        horizon: int,
        gate: str = "enforce",
        credit_objective: bool = False,
        actor: str | None = None,
        mo1_arm: str | None = None,
    ) -> str:
        """Return TASK.md contents (public constitution text, no I*).

        The ``gate`` argument selects gate-accurate feedback wording; the
        enforce text must stay byte-identical to earlier stages (STAGE4.md).
        ``credit_objective`` adds the client-terms goal pressure
        (STAGE6.md §4.1); off must render byte-identically.
        """

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

    def task_markdown(
        self,
        *,
        mission_id: str,
        horizon: int,
        gate: str = "enforce",
        credit_objective: bool = False,
        actor: str | None = None,
        mo1_arm: str | None = None,
    ) -> str:
        """Return TASK.md contents."""
        kwargs: dict[str, object] = {
            "mission_id": mission_id,
            "horizon": horizon,
            "gate": gate,
            "credit_objective": credit_objective,
        }
        if actor is not None:
            kwargs["actor"] = actor
        if mo1_arm is not None:
            kwargs["mo1_arm"] = mo1_arm
        return self._task(**kwargs)

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


def load_bundle(
    name: str, *, debrief_version: int = 1, live_actor: str | None = None
) -> WorldBundle:
    """Load a named world bundle.

    Args:
        name: World id. Ships ``museum`` and experimental ``museum_duo``.
        debrief_version: Questionnaire version for the debrief provider.
            ``1`` (default) is the sealed stage-3 instrument; ``2`` is the
            stage-4 rejection/alarm split (STAGE4.md §3.1).

    Returns:
        Bundle with physics, constitution resolver, hidden intent, and manual.

    Raises:
        KeyError: If ``name`` is unknown.
        ValueError: If ``debrief_version`` is unknown.
    """
    if name == "museum":
        return WorldBundle(
            name="museum",
            world=MuseumWorld(),
            constitution_for_instance=constitution_for_instance,
            intent=MuseumIntentOracle(),
            manual=_CallableManual(task_markdown, observe, state_from_observation),
            instance_for_mission=instance_for_mission,
            debrief=MuseumDebrief(version=debrief_version),
        )
    if name == "museum_duo":
        # Experimental Shape A: museum questionnaire truths over duo physics.
        return WorldBundle(
            name="museum_duo",
            world=MuseumDuoWorld(),
            constitution_for_instance=duo_constitution_for_instance,
            intent=MuseumDuoIntentOracle(),
            manual=_CallableManual(duo_task_markdown, duo_observe, duo_state_from_observation),
            instance_for_mission=duo_instance_for_mission,
            debrief=MuseumDuoDebrief(version=debrief_version, live_actor=live_actor),
        )
    raise KeyError(f"unknown world: {name}")
