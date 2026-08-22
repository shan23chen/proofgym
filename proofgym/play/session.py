"""Persisted gated episode in an isolated player workspace."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from proofgym.catalog import WorldBundle, load_bundle
from proofgym.core.runner import GATE_ENFORCE, EnforceRunner
from proofgym.core.types import ENGINE_VERSION, Action, GateFeedback, Trace, TraceStep
from proofgym.z3check.checker import Z3Checker

TASK_NAME = "TASK.md"
STATE_NAME = "state.json"
EPISODE_NAME = "episode.json"
LOG_NAME = "log.jsonl"
NEXT_ACTION_NAME = "next_action.json"


class PlaySession:
    """One gated episode backed by a player-visible workspace.

    The gate is ``enforce`` by default; ``permissive`` executes illegal
    actions while reporting the violation (see ``core.runner``). The workspace
    contains only public files: TASK.md, state.json, episode bookkeeping, and
    log.jsonl. Hidden intent, gold traces, PLAN.md, and CRITIQUE.md are never
    written here.
    """

    def __init__(
        self,
        workspace: Path,
        bundle: WorldBundle,
        runner: EnforceRunner,
        *,
        last_feedback: GateFeedback | None = None,
    ) -> None:
        self.workspace = workspace
        self.bundle = bundle
        self.runner = runner
        self.last_feedback = last_feedback

    @classmethod
    def create(
        cls,
        workspace: Path,
        *,
        world_name: str,
        mission_id: str,
        meta: Mapping[str, Any] | None = None,
        gate: str = GATE_ENFORCE,
    ) -> PlaySession:
        """Create a fresh workspace and runner for ``mission_id``.

        Args:
            workspace: Empty directory that will hold public player files.
            world_name: Catalog world (pilot: ``museum``).
            mission_id: Mission id (``errand``, ``heist``, ``heist_patched``).
            meta: Extra trace metadata (agent id, model, …).
            gate: ``enforce`` (default) or ``permissive``. Recorded in the
                episode and in trace metadata; results are not comparable
                across gate modes.

        Returns:
            Initialized session with TASK.md / state.json / episode.json written.
        """
        workspace.mkdir(parents=True, exist_ok=True)
        bundle = load_bundle(world_name)
        instance = bundle.instance_for_mission(mission_id)
        mission = bundle.world.mission_for(instance)
        constitution, constitution_id = bundle.constitution_for_instance(instance)
        runner = EnforceRunner(
            bundle.world,
            instance,
            Z3Checker(constitution),
            horizon=mission.horizon,
            constitution_id=constitution_id,
            engine_version=ENGINE_VERSION,
            meta={
                "world": bundle.name,
                "mission_id": mission_id,
                "gate": gate,
                **dict(meta or {}),
            },
            gate=gate,
        )
        session = cls(workspace, bundle, runner)
        (workspace / TASK_NAME).write_text(
            bundle.manual.task_markdown(mission_id=mission_id, horizon=mission.horizon),
            encoding="utf-8",
        )
        (workspace / LOG_NAME).write_text("", encoding="utf-8")
        session.save(append_log=False)
        return session

    @classmethod
    def load(cls, workspace: Path) -> PlaySession:
        """Restore a session from a player workspace.

        Args:
            workspace: Directory previously created by :meth:`create`.

        Returns:
            Session with runner state restored from episode.json + state.json.

        Raises:
            FileNotFoundError: If required files are missing.
            KeyError: If the recorded world is unknown.
        """
        episode = _read_json(workspace / EPISODE_NAME)
        bundle = load_bundle(str(episode["world"]))
        instance = bundle.world.load_instance(str(episode["instance_id"]))
        mission = bundle.world.mission_for(instance)
        constitution, _ = bundle.constitution_for_instance(instance)
        runner = EnforceRunner(
            bundle.world,
            instance,
            Z3Checker(constitution),
            horizon=int(episode["horizon"]),
            constitution_id=str(episode["constitution_id"]),
            engine_version=str(episode.get("engine_version", ENGINE_VERSION)),
            meta=dict(episode.get("meta") or {}),
            gate=str(episode.get("gate", GATE_ENFORCE)),
        )
        observation = _read_json(workspace / STATE_NAME)
        state = bundle.manual.state_from_observation(observation)
        steps = _steps_from_log(workspace / LOG_NAME)
        hashes = [str(item) for item in episode["state_hashes"]]
        runner.restore(
            state=state,
            steps=steps,
            state_hashes=hashes,
            done=bool(episode["done"]),
        )
        last = observation.get("last_feedback")
        last_feedback = None
        if isinstance(last, Mapping):
            last_feedback = GateFeedback(
                executed=bool(last.get("executed")),
                failing_clause_id=(
                    str(last["failing_clause_id"])
                    if last.get("failing_clause_id") is not None
                    else None
                ),
                error=str(last["error"]) if last.get("error") is not None else None,
            )
        del mission
        return cls(workspace, bundle, runner, last_feedback=last_feedback)

    @property
    def done(self) -> bool:
        """Return whether the horizon has been consumed."""
        return self.runner.done

    def submit(self, action: Action) -> GateFeedback:
        """Apply one action through the enforce-mode gate and persist.

        Args:
            action: Typed action.

        Returns:
            Gate feedback (failing clause id on rejection).

        Raises:
            EpisodeFinishedError: If the horizon is already consumed.
        """
        feedback = self.runner.submit(action)
        self.last_feedback = feedback
        self._append_log(action, feedback)
        self.save(append_log=False)
        return feedback

    def to_trace(self) -> Trace:
        """Return the sealed trace of this episode."""
        return self.runner.to_trace()

    def save(self, *, append_log: bool = False) -> None:
        """Write public workspace files from the current runner state.

        Args:
            append_log: Unused; log lines are appended in :meth:`submit`.
                Accepted so callers can say "write everything but the log".
        """
        del append_log
        self.workspace.mkdir(parents=True, exist_ok=True)
        observation = self.bundle.manual.observe(
            self.runner.state,
            step=self.runner.step_index,
            horizon=self.runner.horizon,
            done=self.runner.done,
            last_feedback=(
                self.last_feedback.to_dict() if self.last_feedback is not None else None
            ),
        )
        _write_json(self.workspace / STATE_NAME, observation)
        episode = {
            "world": self.bundle.name,
            "instance_id": self.runner.instance.instance_id,
            "constitution_id": self.runner.constitution_id,
            "engine_version": self.runner.engine_version,
            "seed": self.runner.instance.seed,
            "mission_id": self.runner.instance.mission_id,
            "horizon": self.runner.horizon,
            "gate": self.runner.gate,
            "step": self.runner.step_index,
            "done": self.runner.done,
            "state_hashes": list(self.runner.state_hashes),
            "meta": dict(self.runner.meta),
        }
        _write_json(self.workspace / EPISODE_NAME, episode)

    def _append_log(self, action: Action, feedback: GateFeedback) -> None:
        record = {
            "step": self.runner.step_index - 1,
            "action": action.to_dict(),
            "executed": feedback.executed,
            "failing_clause_id": feedback.failing_clause_id,
            "error": feedback.error,
            "state_hash": self.runner.state_hashes[-1],
        }
        log_path = self.workspace / LOG_NAME
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_next_action(workspace: Path) -> Action | None:
    """Load and consume ``next_action.json`` if it exists.

    Args:
        workspace: Player workspace.

    Returns:
        Parsed action, or ``None`` if the file is absent.

    Raises:
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If the object has no ``type``.
        TypeError: If the object is not an action mapping.
    """
    path = workspace / NEXT_ACTION_NAME
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    path.unlink()
    payload = json.loads(raw)
    if not isinstance(payload, Mapping):
        raise TypeError("next_action.json must be a JSON object")
    return Action.from_dict(payload)


def _steps_from_log(path: Path) -> list[TraceStep]:
    if not path.is_file():
        return []
    steps: list[TraceStep] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        steps.append(
            TraceStep(
                action=Action.from_dict(record["action"]),
                executed=bool(record["executed"]),
            )
        )
    return steps


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "EPISODE_NAME",
    "LOG_NAME",
    "NEXT_ACTION_NAME",
    "STATE_NAME",
    "TASK_NAME",
    "PlaySession",
    "read_next_action",
]
