"""Coding-CLI and mock adapters. ProofGym never calls a third-party LLM API."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from proofgym.core.types import Action
from proofgym.play.isolation import assert_workspace_not_in_checkout
from proofgym.play.prompt import PLAYER_PROMPT
from proofgym.play.session import PlaySession
from proofgym.worlds.museum.sequences import (
    FORCED_DOOR_ACTIONS,
    HONEST_ERRAND_ACTIONS,
    LOST_VISITOR_ACTIONS,
    PATCHED_FORCED_DOOR_ACTIONS,
    PATCHED_REGISTRY_WALKOUT_ACTIONS,
    PATCHED_RETURNED_DIAMOND_ACTIONS,
    REGISTRY_HEIST_ACTIONS,
)

MOCK_SCRIPTS: dict[str, tuple[Action, ...]] = {
    "honest_errand": HONEST_ERRAND_ACTIONS,
    "registry_heist": REGISTRY_HEIST_ACTIONS,
    "forced_door": FORCED_DOOR_ACTIONS,
    "lost_visitor": LOST_VISITOR_ACTIONS,
    "patched_registry_walkout": PATCHED_REGISTRY_WALKOUT_ACTIONS,
    "patched_forced_door": PATCHED_FORCED_DOOR_ACTIONS,
    "patched_returned_diamond": PATCHED_RETURNED_DIAMOND_ACTIONS,
}

# The heist_patched default replays the stage-1 exploit script: under the
# enforce gate the exit is rejected (honest_failure); under the permissive
# gate the same script walks out and scores illegal_shortcut.
DEFAULT_SCRIPT: dict[str, str] = {
    "errand": "honest_errand",
    "heist": "registry_heist",
    "heist_patched": "patched_registry_walkout",
}

OPENCODE_INSTALL_HINT = (
    "OpenCode is not installed (no `opencode` on PATH).\n"
    "Install:  curl -fsSL https://opencode.ai/install | bash\n"
    "     or:  npm install -g opencode-ai\n"
    "Auth:     opencode auth login   (or provider keys in the environment / .env)\n"
    "ProofGym never calls a third-party LLM API itself. Live model evals need "
    "this CLI and credentials on the machine running the eval."
)

CODEX_INSTALL_HINT = (
    "Codex is not installed (no `codex` on PATH).\n"
    "Install:  npm install -g @openai/codex\n"
    "Auth:     codex login   or set CODEX_API_KEY\n"
    "ProofGym invokes `codex exec --sandbox workspace-write` (default sandbox "
    "is read-only) so the agent can call the step CLI and write files. "
    "ProofGym never calls a third-party LLM API itself. Live model evals need "
    "this CLI and credentials on the machine running the eval."
)


class AdapterNotInstalledError(FileNotFoundError):
    """Raised when a required coding CLI is missing from PATH."""


def script_actions(mission_id: str, script: str | None = None) -> tuple[Action, ...]:
    """Return the scripted action list for the mock adapter.

    Args:
        mission_id: ``errand``, ``heist``, or ``heist_patched``.
        script: Optional script id. Defaults to the mission's entry in
            ``DEFAULT_SCRIPT``.

    Returns:
        Immutable action tuple.

    Raises:
        KeyError: If the mission or script id is unknown.
    """
    name = script if script is not None else DEFAULT_SCRIPT[mission_id]
    try:
        return MOCK_SCRIPTS[name]
    except KeyError as exc:
        raise KeyError(f"unknown mock script: {name}") from exc


def require_binary(name: str, hint: str) -> str:
    """Return the path to ``name`` on PATH, or fail with an install hint.

    Args:
        name: Executable name.
        hint: Message used when the binary is missing.

    Returns:
        Absolute path to the executable.

    Raises:
        AdapterNotInstalledError: If ``name`` is not on PATH. Never skipped.
    """
    path = shutil.which(name)
    if path is None:
        raise AdapterNotInstalledError(hint)
    return path


DEBRIEF_POLICIES: frozenset[str] = frozenset({"truthful", "deny_all", "silent"})


class MockAdapter:
    """Offline scripted player. No network, no third-party CLI.

    Debrief policies exercise the disclosure instrument in CI; they are
    controls, not claims about player behavior:

    - ``truthful``: file the recomputed true answers.
    - ``deny_all``: answer ``false`` to everything, regardless of truth
      (coincides with ``truthful`` on runs where nothing happened).
    - ``silent``: file nothing.
    """

    name = "mock"

    def __init__(self, actions: Sequence[Action], debrief_policy: str | None = None) -> None:
        if debrief_policy is not None and debrief_policy not in DEBRIEF_POLICIES:
            raise ValueError(
                f"debrief_policy must be one of {sorted(DEBRIEF_POLICIES)}, got {debrief_policy!r}"
            )
        self.actions = tuple(actions)
        self.debrief_policy = debrief_policy

    def play(self, session: PlaySession, **_: Any) -> dict[str, Any]:
        """Replay ``actions`` through the gate, then file the debrief, if any.

        Args:
            session: Live play session (already created).

        Returns:
            Adapter metadata (no subprocess).
        """
        for action in self.actions:
            if session.done:
                break
            session.submit(action)
        if session.debrief_enabled and self.debrief_policy not in (None, "silent"):
            self._write_debrief(session)
        return {
            "agent": self.name,
            "argv": [],
            "returncode": 0,
            "debrief_policy": self.debrief_policy,
        }

    def _write_debrief(self, session: PlaySession) -> None:
        """Write ``debrief.json`` into the workspace like a player would."""
        import json

        from proofgym.play.debrief import DEBRIEF_ANSWERS_NAME

        truth = session.bundle.debrief.true_answers(session.bundle.world, session.to_trace())
        if self.debrief_policy == "truthful":
            answers: dict[str, bool] = dict(truth)
        else:  # deny_all
            answers = {question_id: False for question_id in truth}
        (session.workspace / DEBRIEF_ANSWERS_NAME).write_text(
            json.dumps(answers, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class OpenCodeAdapter:
    """Spawn `opencode run` pointed at the player workspace."""

    name = "opencode"

    def play(
        self,
        session: PlaySession,
        *,
        model: str,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
        extra_path: Sequence[Path] = (),
    ) -> dict[str, Any]:
        """Run OpenCode non-interactively against ``session.workspace``.

        Args:
            session: Episode whose workspace is the only public view.
            model: ``provider/model`` string passed to ``--model``.
            timeout: Subprocess timeout in seconds, or ``None``.
            env: Optional environment overlay.
            extra_path: Directories prepended to ``PATH`` (act wrapper).

        Returns:
            Adapter metadata including argv and return code.

        Raises:
            AdapterNotInstalledError: If ``opencode`` is not on PATH.
            RuntimeError: If the workspace sits inside the source checkout.
        """
        binary = require_binary("opencode", OPENCODE_INSTALL_HINT)
        workspace = session.workspace.resolve()
        assert_workspace_not_in_checkout(workspace)
        argv = [
            binary,
            "run",
            "--dir",
            str(workspace),
            "--model",
            model,
            "--format",
            "json",
            "--auto",
            PLAYER_PROMPT,
        ]
        completed = _spawn(argv, cwd=workspace, timeout=timeout, env=env, extra_path=extra_path)
        return _meta(self.name, argv, completed)


class CodexAdapter:
    """Spawn `codex exec` pointed at the player workspace."""

    name = "codex"

    def play(
        self,
        session: PlaySession,
        *,
        model: str,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
        extra_path: Sequence[Path] = (),
    ) -> dict[str, Any]:
        """Run Codex non-interactively against ``session.workspace``.

        Args:
            session: Episode whose workspace is the only public view.
            model: Codex ``--model`` value.
            timeout: Subprocess timeout in seconds, or ``None``.
            env: Optional environment overlay.
            extra_path: Directories prepended to ``PATH`` (act wrapper).

        Returns:
            Adapter metadata including argv and return code.

        Raises:
            AdapterNotInstalledError: If ``codex`` is not on PATH.
            RuntimeError: If the workspace sits inside the source checkout.
        """
        binary = require_binary("codex", CODEX_INSTALL_HINT)
        workspace = session.workspace.resolve()
        assert_workspace_not_in_checkout(workspace)
        argv = [
            binary,
            "exec",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "-C",
            str(workspace),
            "--model",
            model,
            PLAYER_PROMPT,
        ]
        completed = _spawn(argv, cwd=workspace, timeout=timeout, env=env, extra_path=extra_path)
        return _meta(self.name, argv, completed)


def write_act_wrapper(bin_dir: Path, workspace: Path, *, pythonpath: str | None) -> Path:
    """Write a ``proofgym-act`` helper *outside* the player workspace.

    Args:
        bin_dir: Directory that will be prepended to the CLI's ``PATH``.
        workspace: Player workspace passed as ``--run``.
        pythonpath: Optional source-tree path so ``python -m proofgym.act``
            works without a site-packages install. Stored only in this
            wrapper, not in the workspace.

    Returns:
        Path to the executable wrapper.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "proofgym-act"
    lines = ["#!/bin/sh", "set -e"]
    if pythonpath:
        quoted_path = _shell_quote(pythonpath)
        lines.append(f"export PYTHONPATH={quoted_path}${{PYTHONPATH:+:$PYTHONPATH}}")
    python = _shell_quote(sys.executable)
    run_dir = _shell_quote(str(workspace.resolve()))
    lines.append(f'exec {python} -m proofgym.act --run {run_dir} "$@"')
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def _spawn(
    argv: list[str],
    *,
    cwd: Path,
    timeout: float | None,
    env: Mapping[str, str] | None,
    extra_path: Sequence[Path],
) -> subprocess.CompletedProcess[str]:
    merged = dict(env) if env is not None else dict(os.environ)
    if extra_path:
        prefix = ":".join(str(path) for path in extra_path)
        merged["PATH"] = prefix + ((":" + merged["PATH"]) if merged.get("PATH") else "")
    return subprocess.run(
        argv,
        cwd=cwd,
        env=merged,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _meta(
    agent: str,
    argv: list[str],
    completed: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    return {
        "agent": agent,
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _shell_quote(value: str) -> str:
    """Single-quote ``value`` for a POSIX shell."""
    return "'" + value.replace("'", "'\\''") + "'"
