"""Shape A helpers: live seat + scripted co-actor on one shared episode.

Experimental local bypass of unsigned MO1 paperwork — see
``docs/EXPERIMENTAL_MO1_BYPASS.md``. Channel-stamps ``args.actor``; auto-advances
the scripted seat whenever ``active`` points at it after a live submission.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofgym.core.types import Action
from proofgym.worlds.museum_duo.constants import ACTOR_E, ACTOR_H, ACTORS
from proofgym.worlds.museum_duo.public import MO1_ARMS
from proofgym.worlds.museum_duo.state import view

COACTOR_SCRIPT_NAME = "coactor_script.json"
ACTOR_BINDING_NAME = "actor_binding.json"


def validate_mo1_arm(arm: str) -> str:
    if arm not in MO1_ARMS:
        raise ValueError(f"unknown --mo1-arm {arm!r}; known: {sorted(MO1_ARMS)}")
    return arm


def validate_live_actor(actor: str) -> str:
    if actor not in ACTORS:
        raise ValueError(f"unknown --live-actor {actor!r}; known: {sorted(ACTORS)}")
    return actor


def load_coactor_script(path: Path) -> dict[str, Any]:
    """Load a Shape A co-actor script JSON.

    Expected shape::

        {"coactor": "H", "live_actor": "E", "actions": [{"type": "...", "args": {...}}, ...]}

    ``args`` may omit ``actor`` (stamped at play time).
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"coactor script must be an object: {path}")
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError(f"coactor script needs a non-empty actions list: {path}")
    coactor = str(payload.get("coactor") or ACTOR_H)
    live = str(payload.get("live_actor") or ACTOR_E)
    validate_live_actor(coactor)
    validate_live_actor(live)
    if coactor == live:
        raise ValueError("coactor and live_actor must differ")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(actions):
        if not isinstance(raw, dict):
            raise ValueError(f"coactor action {index} must be an object")
        if "type" not in raw:
            raise ValueError(f"coactor action {index} missing type")
        args = dict(raw.get("args") or {})
        args["actor"] = coactor
        normalized.append({"type": str(raw["type"]), "args": args})
    return {
        "coactor": coactor,
        "live_actor": live,
        "actions": normalized,
        "source": str(path),
        "meta": {k: v for k, v in payload.items() if k not in {"actions"}},
    }


def write_actor_binding(private_dir: Path, *, live_actor: str, coactor: str) -> None:
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / ACTOR_BINDING_NAME).write_text(
        json.dumps({"live_actor": live_actor, "coactor": coactor}, indent=2) + "\n",
        encoding="utf-8",
    )


def read_actor_binding(private_dir: Path) -> dict[str, str] | None:
    path = private_dir / ACTOR_BINDING_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"live_actor": str(data["live_actor"]), "coactor": str(data["coactor"])}


def write_coactor_script_private(private_dir: Path, script: dict[str, Any]) -> None:
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / COACTOR_SCRIPT_NAME).write_text(
        json.dumps(script, indent=2) + "\n",
        encoding="utf-8",
    )


def read_coactor_script_private(private_dir: Path) -> dict[str, Any] | None:
    path = private_dir / COACTOR_SCRIPT_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def stamp_live_actor(action: Action, live_actor: str) -> tuple[Action, bool]:
    """Overwrite ``args.actor`` to the channel-bound live seat.

    Returns:
        ``(stamped_action, forged)`` where ``forged`` is True when the player
        supplied a conflicting actor tag (overwrite-and-log policy).
    """
    args = dict(action.args)
    prior = args.get("actor")
    forged = prior is not None and str(prior) != live_actor
    args["actor"] = live_actor
    return Action(type=action.type, args=args), forged


def coactor_action_at(script: dict[str, Any], index: int) -> Action:
    """Return the next scripted action, or ``wait`` when the script is exhausted."""
    actions = script["actions"]
    coactor = script["coactor"]
    if index < len(actions):
        raw = actions[index]
        return Action(type=str(raw["type"]), args=dict(raw["args"]))
    return Action(type="wait", args={"actor": coactor})


def advance_coactor(session: Any) -> list[dict[str, Any]]:
    """Auto-play the scripted seat while it is ``active`` and the episode runs.

    Exhaustion rule: scripted ``wait`` to horizon (harness §7 recommended).
    """
    script = read_coactor_script_private(session.private_dir)
    binding = read_actor_binding(session.private_dir)
    if script is None or binding is None:
        return []
    coactor = binding["coactor"]
    played: list[dict[str, Any]] = []
    # Index = how many coactor turns already in the sealed log.
    index = sum(1 for step in session.runner.steps if step.action.args.get("actor") == coactor)
    while not session.done:
        snap = view(session.runner.state)
        if snap.active != coactor:
            break
        action = coactor_action_at(script, index)
        feedback = session.runner.submit(action)
        session.last_feedback = feedback
        session._append_log(action, feedback)
        session.save(append_log=False)
        played.append(
            {
                "index": index,
                "action": action.to_dict(),
                "feedback": feedback.to_dict(),
            }
        )
        index += 1
        # Safety: avoid infinite wait loops if wait somehow fails to toggle.
        if len(played) > session.runner.horizon + 2:
            break
    return played


def mirror_coactor_workspace(live_workspace: Path, session: Any) -> Path | None:
    """Refresh the sibling coactor workspace mirrors (TASK.md already seeded)."""
    coactor_ws = live_workspace.parent / "coactor"
    if not coactor_ws.is_dir():
        return None
    for name in ("state.json", "episode.json", "log.jsonl"):
        src = live_workspace / name
        if src.is_file():
            (coactor_ws / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return coactor_ws


def ensure_coactor_starts_if_needed(session: Any) -> list[dict[str, Any]]:
    """If the live seat is H and E is active at t=0, play E's scripted openers."""
    binding = read_actor_binding(session.private_dir)
    if binding is None:
        return []
    if binding["live_actor"] == ACTOR_E:
        return []
    # Live is H: E starts — advance until H is active (or done).
    return advance_coactor(session)
