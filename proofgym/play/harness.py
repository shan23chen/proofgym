"""Run an episode: create workspace, play, evaluate with hidden I*, write reports."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from proofgym.catalog import load_bundle
from proofgym.core.evaluate import evaluate
from proofgym.core.serialize import dump_trace
from proofgym.play.adapters import (
    CodexAdapter,
    MockAdapter,
    OpenCodeAdapter,
    script_actions,
    write_act_wrapper,
)
from proofgym.play.isolation import assert_workspace_not_in_checkout, source_checkout_root
from proofgym.play.report import RunRecord, format_one_row_report, format_verdict_table
from proofgym.play.session import PlaySession

CLI_AGENTS = frozenset({"opencode", "codex"})


def run_episode(
    *,
    agent: str,
    mission: str,
    model: str | None = None,
    script: str | None = None,
    world_name: str = "museum",
    out_dir: Path,
    live_root: Path | None = None,
    timeout: float | None = None,
) -> RunRecord:
    """Play one mission with one adapter and evaluate the resulting trace.

    Args:
        agent: ``mock``, ``opencode``, or ``codex``.
        mission: ``errand`` or ``heist``.
        model: Required for coding CLIs. Defaults to ``scripted`` for mock.
        script: Mock script id (default: honest_errand / registry_heist).
        world_name: Catalog world.
        out_dir: Where to write verdict.json, trace.json, and the report.
        live_root: Directory for the isolated live workspace. Created with
            ``tempfile.mkdtemp`` when omitted so a coding CLI is never started
            in the repo.
        timeout: Subprocess timeout for coding CLIs.

    Returns:
        Completed run record.

    Raises:
        AdapterNotInstalledError: If a coding CLI is missing from PATH.
        KeyError: If the agent, world, mission, or script is unknown.
        RuntimeError: If a coding-CLI workspace would sit in the checkout.
    """
    model_id = model if model is not None else ("scripted" if agent == "mock" else "")
    if agent in CLI_AGENTS and not model_id:
        raise ValueError(f"--model is required for agent {agent!r}")

    root = live_root if live_root is not None else Path(tempfile.mkdtemp(prefix="proofgym-player-"))
    workspace = root / "workspace"
    bin_dir = root / "bin"
    if agent in CLI_AGENTS:
        assert_workspace_not_in_checkout(workspace)

    meta = {"agent_id": f"{agent}.{model_id}", "mission_id": mission}
    session = PlaySession.create(
        workspace,
        world_name=world_name,
        mission_id=mission,
        meta=meta,
    )
    checkout = source_checkout_root()
    pythonpath = str(checkout) if checkout is not None else None
    write_act_wrapper(bin_dir, workspace, pythonpath=pythonpath)

    adapter_meta: dict[str, Any]
    if agent == "mock":
        actions = script_actions(mission, script)
        adapter_meta = MockAdapter(actions).play(session)
    elif agent == "opencode":
        adapter_meta = OpenCodeAdapter().play(
            session,
            model=model_id,
            timeout=timeout,
            extra_path=(bin_dir,),
        )
        session = PlaySession.load(workspace)
    elif agent == "codex":
        adapter_meta = CodexAdapter().play(
            session,
            model=model_id,
            timeout=timeout,
            extra_path=(bin_dir,),
        )
        session = PlaySession.load(workspace)
    else:
        raise KeyError(f"unknown agent: {agent}")

    bundle = load_bundle(world_name)
    trace = session.to_trace()
    # Evaluation uses hidden I* in *this* process, never in the workspace.
    verdict = evaluate(bundle.world, bundle.constitution, bundle.intent, trace)
    verdict = replace(verdict, trace=str(trace.meta.get("agent_id") or verdict.trace))
    record = RunRecord(
        agent=agent,
        model=model_id,
        mission=mission,
        verdict=verdict,
        trace=trace,
        workspace=str(workspace.resolve()),
        adapter=adapter_meta,
    )
    _write_artifacts(out_dir, record, workspace)
    return record


def compare_records(records: Sequence[RunRecord]) -> str:
    """Return the Markdown comparison table for ``records``."""
    return format_verdict_table(records)


def load_run_record(path: Path) -> RunRecord:
    """Load a previously written ``verdict.json`` as a :class:`RunRecord`.

    Args:
        path: Path to ``verdict.json`` or a run directory containing it.

    Returns:
        Run record. The embedded trace is restored; workspace may be stale.
    """
    from proofgym.core.serialize import trace_from_dict
    from proofgym.core.types import (
        FormalVerdict,
        FormalViolation,
        IntentVerdict,
        IntentViolation,
        Verdict,
    )

    target = path / "verdict.json" if path.is_dir() else path
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError("verdict.json must be an object")
    trace = trace_from_dict(payload["trace"])
    formal_raw = payload["formal"]
    intent_raw = payload["intent"]
    verdict = Verdict(
        trace=str(trace.meta.get("agent_id") or payload.get("trace") or ""),
        task_success=bool(payload["task_success"]),
        formal=FormalVerdict(
            ok=bool(formal_raw["ok"]),
            violations=tuple(
                FormalViolation(
                    step=int(item["step"]),
                    clause_id=str(item["clause_id"]),
                    witness=dict(item.get("witness") or {}),
                )
                for item in formal_raw.get("violations", [])
            ),
        ),
        intent=IntentVerdict(
            verdict=intent_raw["verdict"],
            violations=tuple(
                IntentViolation(
                    step=int(item["step"]),
                    rule_id=str(item["rule_id"]),
                    rationale=str(item.get("rationale") or ""),
                )
                for item in intent_raw.get("violations", [])
            ),
            rationale=str(intent_raw.get("rationale") or ""),
        ),
        outcome=payload["outcome"],
        exploit_family=payload.get("exploit_family"),
    )
    return RunRecord(
        agent=str(payload["agent"]),
        model=str(payload["model"]),
        mission=str(payload["mission"]),
        verdict=verdict,
        trace=trace,
        workspace=str(payload.get("workspace") or ""),
        adapter=dict(payload.get("adapter") or {}),
    )


def _write_artifacts(out_dir: Path, record: RunRecord, workspace: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dump_trace(record.trace, out_dir / "trace.json")
    (out_dir / "verdict.json").write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(format_one_row_report(record), encoding="utf-8")
    snapshot = out_dir / "workspace"
    if snapshot.exists():
        shutil.rmtree(snapshot)
    shutil.copytree(workspace, snapshot)
