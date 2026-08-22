"""Coding-CLI adapters: missing binaries fail loudly; argv matches the docs."""

from __future__ import annotations

import os
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from proofgym.play.adapters import (
    CODEX_INSTALL_HINT,
    OPENCODE_INSTALL_HINT,
    AdapterNotInstalledError,
    OpenCodeAdapter,
    require_binary,
)
from proofgym.play.harness import run_episode
from proofgym.play.session import PlaySession


def test_opencode_missing_binary_has_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing OpenCode binary fails with an install hint; it does not skip."""
    monkeypatch.setattr("proofgym.play.adapters.shutil.which", lambda _name: None)
    with pytest.raises(AdapterNotInstalledError) as exc:
        require_binary("opencode", OPENCODE_INSTALL_HINT)
    assert "opencode.ai/install" in str(exc.value)
    assert "opencode auth login" in str(exc.value)


def test_codex_missing_binary_has_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing Codex binary fails with an install hint; it does not skip."""
    monkeypatch.setattr("proofgym.play.adapters.shutil.which", lambda _name: None)
    with pytest.raises(AdapterNotInstalledError) as exc:
        require_binary("codex", CODEX_INSTALL_HINT)
    assert "CODEX_API_KEY" in str(exc.value)
    assert "workspace-write" in str(exc.value)


def test_run_opencode_without_binary_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``run --agent opencode`` does not silently skip when the CLI is absent."""
    monkeypatch.setattr("proofgym.play.adapters.shutil.which", lambda _name: None)
    with pytest.raises(AdapterNotInstalledError):
        run_episode(
            agent="opencode",
            mission="heist",
            model="openai/gpt-4.1",
            out_dir=tmp_path / "out",
            live_root=tmp_path / "live",
        )


def test_opencode_argv_and_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenCode is invoked with ``run --dir <workspace> --model --auto``."""
    captured: list[tuple[list[str], Path]] = []

    def fake_which(name: str) -> str | None:
        return "/usr/bin/opencode" if name == "opencode" else None

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured.append((list(argv), Path(str(kwargs["cwd"]))))
        return CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    live = tmp_path / "live"
    record = run_episode(
        agent="opencode",
        mission="heist",
        model="openai/gpt-4.1",
        out_dir=tmp_path / "out",
        live_root=live,
    )
    assert captured
    argv, cwd = captured[0]
    workspace = (live / "workspace").resolve()
    assert argv[0] == "/usr/bin/opencode"
    assert argv[1] == "run"
    assert "--dir" in argv
    assert argv[argv.index("--dir") + 1] == str(workspace)
    assert argv[argv.index("--model") + 1] == "openai/gpt-4.1"
    assert "--auto" in argv
    assert cwd == workspace
    assert record.workspace == str(workspace)
    checkout = Path(__file__).resolve().parents[1]
    assert not str(cwd).startswith(str(checkout) + os.sep)


def test_codex_argv_sandbox_and_skip_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Codex is invoked with workspace-write, skip-git-repo-check, and ``-C``."""
    captured: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        return "/usr/bin/codex" if name == "codex" else None

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[str]:
        del kwargs
        captured.append(list(argv))
        return CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr("proofgym.play.adapters.shutil.which", fake_which)
    monkeypatch.setattr("proofgym.play.adapters.subprocess.run", fake_run)
    live = tmp_path / "live"
    run_episode(
        agent="codex",
        mission="errand",
        model="gpt-5",
        out_dir=tmp_path / "out",
        live_root=live,
    )
    argv = captured[0]
    workspace = str((live / "workspace").resolve())
    assert argv[0] == "/usr/bin/codex"
    assert argv[1:4] == ["exec", "--sandbox", "workspace-write"]
    assert "--skip-git-repo-check" in argv
    assert "-C" in argv
    assert argv[argv.index("-C") + 1] == workspace
    assert argv[argv.index("--model") + 1] == "gpt-5"


def test_cli_adapter_refuses_workspace_inside_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A coding CLI must not be started on a workspace inside the source tree."""
    fake_checkout = tmp_path / "repo"
    fake_checkout.mkdir()
    (fake_checkout / "PLAN.md").write_text("plan\n", encoding="utf-8")
    (fake_checkout / "CRITIQUE.md").write_text("critique\n", encoding="utf-8")
    session = PlaySession.create(
        fake_checkout / "workspace",
        world_name="museum",
        mission_id="heist",
    )
    monkeypatch.setattr(
        "proofgym.play.isolation.source_checkout_root",
        lambda: fake_checkout,
    )
    monkeypatch.setattr(
        "proofgym.play.adapters.shutil.which",
        lambda name: "/usr/bin/opencode" if name == "opencode" else None,
    )
    with pytest.raises(RuntimeError, match="must not live inside"):
        OpenCodeAdapter().play(session, model="openai/gpt-4.1")
