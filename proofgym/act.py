"""Step CLI: ``python -m proofgym.act --run <dir> '<json action>'``.

This is the only way a player submits an action. It talks to the enforce-mode
runner persisted in the player workspace. Hidden I* is never loaded here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from proofgym.core.runner import EpisodeFinishedError
from proofgym.core.types import Action
from proofgym.play.session import PlaySession, read_next_action


def main(argv: list[str] | None = None) -> int:
    """Apply one action to the episode in ``--run``.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` on a completed gate (accept or constitutional reject),
        ``1`` if the horizon is already consumed,
        ``2`` on a parse error.
    """
    parser = argparse.ArgumentParser(
        description="Submit one typed action to a ProofGym player workspace."
    )
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="Player workspace directory (contains TASK.md and state.json).",
    )
    parser.add_argument(
        "action",
        nargs="?",
        default=None,
        help="JSON action object. If omitted, read and consume next_action.json.",
    )
    args = parser.parse_args(argv)
    workspace = args.run.expanduser().resolve()
    try:
        action = _parse_action(workspace, args.action)
    except FileNotFoundError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stdout)
        return 2
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"invalid action: {exc}"}), file=sys.stdout)
        return 2
    try:
        session = PlaySession.load(workspace)
    except FileNotFoundError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stdout)
        return 2
    try:
        feedback = session.submit(action)
    except EpisodeFinishedError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "done": True,
                    "error": str(exc),
                    "state": _state_summary(workspace),
                }
            ),
            file=sys.stdout,
        )
        return 1
    payload = {
        "ok": True,
        "done": session.done,
        "step": session.runner.step_index,
        "horizon": session.runner.horizon,
        **feedback.to_dict(),
    }
    print(json.dumps(payload), file=sys.stdout)
    return 0


def _parse_action(workspace: Path, raw: str | None) -> Action:
    if raw is not None:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise TypeError("action JSON must be an object")
        return Action.from_dict(payload)
    action = read_next_action(workspace)
    if action is None:
        raise FileNotFoundError("no action argument and next_action.json is missing")
    return action


def _state_summary(workspace: Path) -> dict[str, object] | None:
    path = workspace / "state.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return {
        key: payload[key]
        for key in ("step", "horizon", "done", "room", "inventory", "registry")
        if key in payload
    }


if __name__ == "__main__":
    raise SystemExit(main())
