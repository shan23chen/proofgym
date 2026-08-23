"""Run an episode: create workspace, play, evaluate with hidden I*, write reports."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from proofgym.catalog import WorldBundle, load_bundle
from proofgym.core.evaluate import evaluate
from proofgym.core.runner import EnforceRunner
from proofgym.core.serialize import dump_trace
from proofgym.core.types import ENGINE_VERSION, Trace
from proofgym.play.adapters import (
    CodexAdapter,
    MockAdapter,
    OpenCodeAdapter,
    script_actions,
    write_act_wrapper,
)
from proofgym.play.debrief import (
    DEBRIEF_ANSWERS_NAME,
    DisclosureVerdict,
    read_debrief_answers,
    score_debrief,
    settle_debrief,
)
from proofgym.play.isolation import assert_workspace_not_in_checkout, source_checkout_root
from proofgym.play.report import RunRecord, format_one_row_report, format_verdict_table
from proofgym.play.session import PlaySession, private_dir_for
from proofgym.z3check.checker import Z3Checker

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
    gate: str = "enforce",
    debrief: bool = False,
    debrief_policy: str | None = None,
    debrief_version: int = 1,
    debrief_stakes: bool = False,
    credit_objective: bool = False,
    self_certify: bool = False,
    retry_on_empty: bool = False,
) -> RunRecord:
    """Play one mission with one adapter and evaluate the resulting trace.

    Args:
        agent: ``mock``, ``opencode``, or ``codex``.
        mission: ``errand``, ``heist``, or ``heist_patched``.
        model: Required for coding CLIs. Defaults to ``scripted`` for mock.
        script: Mock script id (default per mission, see adapters).
        world_name: Catalog world.
        out_dir: Where to write verdict.json, trace.json, and the report.
        live_root: Directory for the isolated live workspace. Created with
            ``tempfile.mkdtemp`` when omitted so a coding CLI is never started
            in the repo.
        timeout: Subprocess timeout for coding CLIs.
        gate: ``enforce`` (default) or ``permissive``. Under enforce, illegal
            actions are rejected and ``illegal_shortcut`` is unreachable;
            permissive executes them and records the violation.
        debrief: When True, the workspace asks for a post-episode self-report
            (``debrief.json``) which is scored deterministically against the
            sealed trace. Off by default: announcing a self-report may itself
            change behavior, so debrief on/off is a controlled condition.
        debrief_policy: Mock-only control (``truthful``, ``deny_all``,
            ``silent``). Defaults to ``truthful`` for mock debrief runs.
        debrief_version: Questionnaire version (STAGE4.md §3.1). ``1``
            (default) is the sealed stage-3 instrument; ``2`` is the
            rejection/alarm split. Requires ``debrief`` when non-default;
            never pool disclosure labels across versions.
        debrief_stakes: When True, DEBRIEF.md announces the mission-credit
            settlement rule and the harness records the settlement computed
            from the *declared* answers (STAGE5.md §3.1). Requires
            ``debrief`` and a validated questionnaire (version 2 or newer).
            The settlement never changes the verdict or the outcome label.
        credit_objective: When True, TASK.md binds the recorded credit into
            the player's stated engagement (STAGE6.md §4.1) — goal pressure
            from the briefing voice; the debrief instrument itself is
            unchanged. Requires ``debrief_stakes``. Objective-bound and
            objective-free runs are distinct conditions and never pool.
        self_certify: When True, the settlement is read from the *declared*
            claim and stake answers alone — actual task success is not
            consulted, and the Stakes announcement says so (STAGE8.md §3.2).
            Requires ``debrief_stakes`` and the v4 questionnaire. Bases
            never pool.
        retry_on_empty: Coding-CLI robustness control (off by default; the
            mock adapter rejects it). When the CLI exits nonzero having
            submitted zero actions and filed nothing — an *adapter error*,
            not player behavior — discard that attempt, start one fresh
            episode, and record the discarded attempt in the adapter
            metadata. A run whose final attempt still fails is marked
            ``adapter_error`` either way (docs/ADAPTER_ROBUSTNESS.md).

    Returns:
        Completed run record.

    Raises:
        AdapterNotInstalledError: If a coding CLI is missing from PATH.
        KeyError: If the agent, world, mission, or script is unknown.
        ValueError: If a required model is missing, the gate is unknown, a
            debrief policy is passed for a non-mock agent, a non-default
            debrief version is requested without a debrief, stakes are
            requested without a debrief / with the v1 questionnaire, the
            credit objective is requested without stakes,
            self-certification is requested without stakes / below v4, or
            retry-on-empty is requested for a non-CLI agent.
        RuntimeError: If a coding-CLI workspace would sit in the checkout.
    """
    model_id = model if model is not None else ("scripted" if agent == "mock" else "")
    if agent in CLI_AGENTS and not model_id:
        raise ValueError(f"--model is required for agent {agent!r}")
    if debrief_policy is not None and agent != "mock":
        raise ValueError("--debrief-policy is a mock-only control; live players answer freely")
    if retry_on_empty and agent not in CLI_AGENTS:
        raise ValueError(
            "--retry-on-empty is a coding-CLI robustness control; the mock adapter "
            "cannot fail to start and CI runs must stay deterministic"
        )
    if debrief_version != 1 and not debrief:
        raise ValueError("--debrief-version requires --debrief (a questionnaire nobody is asked)")
    if debrief_stakes and not debrief:
        raise ValueError("--debrief-stakes requires --debrief (stakes with no filing to settle)")
    if debrief_stakes and debrief_version < 2:
        raise ValueError(
            "--debrief-stakes requires --debrief-version 2 or newer; stakes data must "
            "never be confounded with the instrument stage 4 invalidated"
        )
    if credit_objective and not debrief_stakes:
        raise ValueError(
            "--credit-objective requires --debrief-stakes (a credit objective with "
            "no settled credit is incoherent)"
        )
    if self_certify and not debrief_stakes:
        raise ValueError("--self-certify requires --debrief-stakes (no settlement to certify)")
    if self_certify and debrief_version < 4:
        raise ValueError(
            "--self-certify requires --debrief-version 4 (the claim question "
            "q_task does not exist before v4)"
        )
    if agent == "mock" and debrief and debrief_policy is None:
        debrief_policy = "truthful"

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
        gate=gate,
        debrief=debrief,
        debrief_version=debrief_version,
        debrief_stakes=debrief_stakes,
        credit_objective=credit_objective,
        self_certify=self_certify,
    )
    checkout = source_checkout_root()
    pythonpath = str(checkout) if checkout is not None else None
    write_act_wrapper(bin_dir, workspace, pythonpath=pythonpath)

    adapter_meta: dict[str, Any]
    adapter_error = False
    if agent == "mock":
        actions = script_actions(mission, script)
        adapter_meta = MockAdapter(actions, debrief_policy=debrief_policy).play(session)
    elif agent in CLI_AGENTS:
        cli_adapter = OpenCodeAdapter() if agent == "opencode" else CodexAdapter()
        failed_attempts: list[dict[str, Any]] = []
        max_attempts = 2 if retry_on_empty else 1
        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                # The failed attempt never engaged the episode (no steps, no
                # filing), so the retry discards it wholesale and starts a
                # byte-fresh episode. The discarded attempt is preserved in
                # the adapter metadata, never hidden.
                shutil.rmtree(workspace, ignore_errors=True)
                shutil.rmtree(private_dir_for(workspace), ignore_errors=True)
                session = PlaySession.create(
                    workspace,
                    world_name=world_name,
                    mission_id=mission,
                    meta=meta,
                    gate=gate,
                    debrief=debrief,
                    debrief_version=debrief_version,
                    debrief_stakes=debrief_stakes,
                    credit_objective=credit_objective,
                    self_certify=self_certify,
                )
            adapter_meta = cli_adapter.play(
                session,
                model=model_id,
                timeout=timeout,
                extra_path=(bin_dir,),
            )
            session = PlaySession.load(workspace)
            adapter_error = _cli_attempt_failed(
                adapter_meta.get("returncode"),
                session.to_trace(),
                workspace,
            )
            if not adapter_error or attempt == max_attempts:
                break
            failed_attempts.append(_failed_attempt_summary(adapter_meta))
        if retry_on_empty:
            adapter_meta["retry_on_empty"] = True
        if failed_attempts:
            adapter_meta["failed_attempts"] = failed_attempts
    else:
        raise KeyError(f"unknown agent: {agent}")

    bundle = load_bundle(world_name, debrief_version=debrief_version)
    integrity_events: list[dict[str, Any]] = list(session.integrity_events)
    if agent in CLI_AGENTS:
        # Never score a trace restored from disk. Re-derive the episode in
        # this process from the only channel the player legitimately controls
        # — the submitted action list — under the harness's own authoritative
        # gate, mission, and constitution. A player that rewrote gate,
        # instance, hashes, or executed flags anywhere on disk changes
        # nothing here; the divergence is recorded instead.
        trace, rebuild_events = _rebuild_authoritative_trace(
            bundle,
            mission=mission,
            gate=gate,
            debrief=debrief,
            meta=meta,
            recorded=session.to_trace(),
        )
        integrity_events.extend(rebuild_events)
    else:
        # The mock adapter plays on the in-process session; there is no
        # untrusted reload to defend against.
        trace = session.to_trace()
    integrity = {
        "status": "flagged" if integrity_events else "clean",
        "events": integrity_events,
    }
    instance = bundle.instance_for_mission(mission)
    constitution, _ = bundle.constitution_for_instance(instance)
    # Evaluation uses hidden I* in *this* process, never in the workspace.
    verdict = evaluate(bundle.world, constitution, bundle.intent, trace)
    verdict = replace(verdict, trace=str(trace.meta.get("agent_id") or verdict.trace))
    disclosure = _score_disclosure(bundle, trace, workspace) if debrief else None
    # The settlement rewards the declaration; the disclosure verdict convicts
    # it. Keeping the two separate — and both out of the outcome mapping — is
    # the stage-5 design (STAGE5.md §3.1).
    settlement = (
        settle_debrief(
            task_success=verdict.task_success,
            declared=disclosure.declared if disclosure is not None else None,
            stake_question_id=bundle.debrief.stake_question_id(),
            claim_question_id=bundle.debrief.claim_question_id() if self_certify else None,
        )
        if debrief_stakes
        else None
    )
    record = RunRecord(
        agent=agent,
        model=model_id,
        mission=mission,
        gate=gate,
        verdict=verdict,
        trace=trace,
        workspace=str(workspace.resolve()),
        adapter=adapter_meta,
        disclosure=disclosure,
        integrity=integrity,
        settlement=settlement,
        credit_objective=credit_objective,
        self_certified=self_certify,
        adapter_error=adapter_error,
    )
    _write_artifacts(out_dir, record, workspace)
    return record


def _cli_attempt_failed(returncode: Any, trace: Trace, workspace: Path) -> bool:
    """Return whether a coding-CLI attempt was an adapter failure.

    An attempt is an *adapter error* only when all three hold: the CLI
    exited nonzero, no action was ever submitted, and no debrief answers
    were filed — the process died before engaging the episode at all
    (the live "zero-step, exit code 1" class). Everything short of that is
    player behavior and is never retried or marked:

    - zero steps with exit code 0 is deliberate silence (a measured
      strategy — see STAGE3.md RQ-D4 and STAGE5.md RQ-S5);
    - zero steps with a filed ``debrief.json`` is a refusal that reported
      itself (the stage-6 escape route, STAGE6.md §4.3);
    - a nonzero exit *after* submitting steps is a partial episode with the
      return code already recorded in the adapter metadata.

    Args:
        returncode: CLI exit status from the adapter metadata.
        trace: Authoritative episode trace at the end of the attempt.
        workspace: Player workspace (checked for a debrief filing).

    Returns:
        True when the attempt records an absent player.
    """
    if returncode == 0:
        return False
    if trace.steps:
        return False
    if (workspace / DEBRIEF_ANSWERS_NAME).is_file():
        return False
    return True


def _failed_attempt_summary(meta: Mapping[str, Any]) -> dict[str, Any]:
    """Condense a discarded CLI attempt for the adapter metadata.

    Args:
        meta: Full adapter metadata of the failed attempt.

    Returns:
        Return code plus a bounded stderr tail (enough to diagnose the
        crash without bloating ``verdict.json``).
    """
    stderr = str(meta.get("stderr") or "")
    return {
        "returncode": meta.get("returncode"),
        "stderr_tail": stderr[-500:],
    }


def _rebuild_authoritative_trace(
    bundle: WorldBundle,
    *,
    mission: str,
    gate: str,
    debrief: bool,
    meta: Mapping[str, Any],
    recorded: Trace,
) -> tuple[Trace, list[dict[str, Any]]]:
    """Replay the recorded submitted actions through a fresh in-process gate.

    The rebuilt trace is authoritative by construction: instance, gate,
    constitution, horizon, executed flags, and state hashes are all derived
    here from the harness's own arguments plus the action list. The recorded
    episode is only compared against it for divergence reporting.

    Args:
        bundle: World bundle.
        mission: Authoritative mission id (harness argument, not the file's).
        gate: Authoritative gate mode (harness argument, not the file's).
        debrief: Whether this run requested a debrief (trace metadata).
        meta: Extra trace metadata (agent id, mission), as passed at create.
        recorded: Episode restored from the on-disk record.

    Returns:
        ``(rebuilt_trace, events)`` where ``events`` is empty when the
        recorded episode matches the rebuild exactly.
    """
    instance = bundle.instance_for_mission(mission)
    world_mission = bundle.world.mission_for(instance)
    constitution, constitution_id = bundle.constitution_for_instance(instance)
    runner = EnforceRunner(
        bundle.world,
        instance,
        Z3Checker(constitution),
        horizon=world_mission.horizon,
        constitution_id=constitution_id,
        engine_version=ENGINE_VERSION,
        meta={
            "world": bundle.name,
            "mission_id": mission,
            "gate": gate,
            "debrief": debrief,
            **dict(meta),
        },
        gate=gate,
    )
    dropped = 0
    for step in recorded.steps:
        if runner.done:
            dropped += 1
            continue
        runner.submit(step.action)
    rebuilt = runner.to_trace()

    fields = sorted(
        name
        for name, matches in {
            "instance_id": recorded.instance_id == rebuilt.instance_id,
            "constitution_id": recorded.constitution_id == rebuilt.constitution_id,
            "seed": recorded.seed == rebuilt.seed,
            "gate": recorded.meta.get("gate") == gate,
            "executed_flags": [s.executed for s in recorded.steps[: len(rebuilt.steps)]]
            == [s.executed for s in rebuilt.steps],
            "state_hashes": tuple(recorded.state_hashes) == tuple(rebuilt.state_hashes),
        }.items()
        if not matches
    )
    if dropped:
        fields.append("steps_beyond_horizon")
    events: list[dict[str, Any]] = []
    if fields:
        events.append(
            {
                "step": len(rebuilt.steps),
                "file": "episode",
                "kind": "episode_diverged",
                "fields": fields,
            }
        )
    return rebuilt, events


def _score_disclosure(bundle: WorldBundle, trace: Trace, workspace: Path) -> DisclosureVerdict:
    """Score the player's debrief.json against trace-derived ground truth."""
    questions = bundle.debrief.questions()
    truth = bundle.debrief.true_answers(bundle.world, trace)
    declared, notes, error = read_debrief_answers(workspace, questions)
    return score_debrief(
        truth,
        declared,
        notes=notes,
        error=error,
        questionnaire=bundle.debrief.questionnaire_id(),
    )


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
    disclosure_raw = payload.get("disclosure")
    disclosure = (
        DisclosureVerdict.from_dict(disclosure_raw) if isinstance(disclosure_raw, Mapping) else None
    )
    integrity_raw = payload.get("integrity")
    integrity = (
        {
            "status": str(integrity_raw.get("status", "clean")),
            "events": list(integrity_raw.get("events") or []),
        }
        if isinstance(integrity_raw, Mapping)
        else {"status": "clean", "events": []}
    )
    settlement_raw = payload.get("settlement")
    return RunRecord(
        agent=str(payload["agent"]),
        model=str(payload["model"]),
        mission=str(payload["mission"]),
        gate=str(payload.get("gate", "enforce")),
        verdict=verdict,
        trace=trace,
        workspace=str(payload.get("workspace") or ""),
        adapter=dict(payload.get("adapter") or {}),
        disclosure=disclosure,
        integrity=integrity,
        settlement=str(settlement_raw) if settlement_raw is not None else None,
        credit_objective=bool(payload.get("credit_objective", False)),
        self_certified=bool(payload.get("self_certified", False)),
        adapter_error=bool(payload.get("adapter_error", False)),
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
