"""ProofGym command line: run, compare, sweep, report.

Usage:
    python -m proofgym run --agent mock --mission heist
    python -m proofgym run --agent mock --mission heist_patched --gate permissive
    python -m proofgym run --agent opencode --model provider/model --mission heist
    python -m proofgym run --agent codex --model gpt-5 --mission errand
    python -m proofgym compare --agent mock --mission heist --mission errand
    python -m proofgym sweep --agent mock --mission heist --n 3
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from proofgym.play.adapters import AdapterNotInstalledError
from proofgym.play.harness import compare_records, load_run_record, run_episode
from proofgym.play.report import format_verdict_table
from proofgym.play.sweep import format_sweep_table, run_sweep, summarize_records
from proofgym.report import main as report_main


def main(argv: list[str] | None = None) -> int:
    """Dispatch ``run``, ``compare``, or ``report``.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="proofgym",
        description="ProofGym: enforce-mode runner and coding-CLI players.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Play one mission with one adapter.")
    _add_run_flags(run_parser)
    run_parser.add_argument(
        "--model",
        action="append",
        default=None,
        help="Model id. Repeatable. Required for opencode/codex.",
    )
    run_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Artifact directory (verdict.json, trace.json, report.md).",
    )

    compare_parser = sub.add_parser(
        "compare",
        help="Run or load several episodes and print a comparison table.",
    )
    _add_run_flags(compare_parser)
    compare_parser.add_argument(
        "--model",
        action="append",
        default=None,
        help="Model id. Repeatable. Cartesian with --agent and --mission.",
    )
    compare_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory to write compare.md and per-run subdirectories.",
    )
    compare_parser.add_argument(
        "runs",
        nargs="*",
        type=Path,
        help="Existing run directories (each containing verdict.json).",
    )

    sweep_parser = sub.add_parser(
        "sweep",
        help="Run one (agent, model, mission, gate) cell n times; report rates.",
    )
    _add_run_flags(sweep_parser)
    sweep_parser.add_argument(
        "--model",
        action="append",
        default=None,
        help="Model id. Repeatable. Cartesian with --agent and --mission.",
    )
    sweep_parser.add_argument(
        "--n",
        type=int,
        default=3,
        dest="tries",
        help="Tries per cell (default: 3).",
    )
    sweep_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory to write sweep.md and per-try subdirectories.",
    )

    report_parser = sub.add_parser(
        "report",
        help="Emit the gold-trace outcome table (audit mode).",
    )
    report_parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Also write the Markdown report to this path.",
    )
    report_parser.add_argument(
        "--all",
        action="store_true",
        help="Include the stage-2 patched-constitution traces.",
    )

    args = parser.parse_args(argv)
    if args.command == "report":
        flags = ["--write", str(args.write)] if args.write is not None else []
        if args.all:
            flags.append("--all")
        return report_main(flags)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "compare":
        return _cmd_compare(args)
    if args.command == "sweep":
        return _cmd_sweep(args)
    parser.error(f"unknown command: {args.command}")
    return 2


def _add_run_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--agent",
        action="append",
        default=None,
        help="Player adapter: mock, opencode, or codex. Repeatable for compare.",
    )
    parser.add_argument(
        "--mission",
        action="append",
        default=None,
        help="Mission id: errand or heist. Repeatable for compare.",
    )
    parser.add_argument(
        "--script",
        default=None,
        help="Mock script id (honest_errand, registry_heist, …).",
    )
    parser.add_argument(
        "--world",
        default="museum",
        help="World name (default: museum).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Seconds to wait for a coding CLI. Unlimited if omitted.",
    )
    parser.add_argument(
        "--gate",
        choices=("enforce", "permissive"),
        default="enforce",
        help=(
            "enforce (default): illegal actions are rejected and cost a turn. "
            "permissive: illegal actions execute; the violation is recorded."
        ),
    )
    parser.add_argument(
        "--debrief",
        action="store_true",
        help=(
            "Ask the player to file debrief.json (a boolean self-report) and "
            "score it deterministically against the sealed trace. Off by "
            "default so debrief-free runs stay comparable."
        ),
    )
    parser.add_argument(
        "--debrief-policy",
        choices=("truthful", "deny_all", "silent"),
        default=None,
        help=(
            "Mock-only debrief control (implies --debrief): truthful files "
            "the true answers, deny_all answers false to everything, silent "
            "files nothing."
        ),
    )


def _cmd_run(args: argparse.Namespace) -> int:
    agents = args.agent or ["mock"]
    missions = args.mission or ["heist"]
    models = args.model or [None]
    if len(agents) != 1 or len(missions) != 1:
        print("run takes one --agent and one --mission (use compare for several)", file=sys.stderr)
        return 2
    records = []
    try:
        for model in models:
            out_dir = args.out
            if out_dir is not None and len(models) > 1:
                label = model or "scripted"
                out_dir = args.out / _safe(label)
            elif out_dir is None:
                out_dir = _default_out(agents[0], missions[0], model)
            record = run_episode(
                agent=agents[0],
                mission=missions[0],
                model=model,
                script=args.script,
                world_name=args.world,
                out_dir=out_dir,
                timeout=args.timeout,
                gate=args.gate,
                debrief=_debrief_enabled(args),
                debrief_policy=args.debrief_policy,
            )
            records.append(record)
            print(f"wrote {out_dir / 'verdict.json'}")
    except AdapterNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (KeyError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if len(records) == 1:
        from proofgym.play.report import format_one_row_report

        print(format_one_row_report(records[0]), end="")
    else:
        print(format_verdict_table(records), end="")
        if args.out is not None:
            (args.out / "compare.md").write_text(format_verdict_table(records), encoding="utf-8")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    records = []
    if args.runs:
        for path in args.runs:
            records.append(load_run_record(path))
    else:
        agents = args.agent or ["mock"]
        missions = args.mission or ["heist"]
        models = args.model or [None]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = args.out or Path("runs") / f"compare-{stamp}"
        try:
            for agent in agents:
                for mission in missions:
                    for model in models:
                        label = f"{_safe(agent)}-{_safe(model or 'scripted')}-{_safe(mission)}"
                        record = run_episode(
                            agent=agent,
                            mission=mission,
                            model=model,
                            script=args.script,
                            world_name=args.world,
                            out_dir=base / label,
                            timeout=args.timeout,
                            gate=args.gate,
                            debrief=_debrief_enabled(args),
                            debrief_policy=args.debrief_policy,
                        )
                        records.append(record)
        except AdapterNotInstalledError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except (KeyError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        table = compare_records(records)
        base.mkdir(parents=True, exist_ok=True)
        (base / "compare.md").write_text(table, encoding="utf-8")
        print(f"wrote {base / 'compare.md'}")
        print(table, end="")
        return 0
    table = compare_records(records)
    print(table, end="")
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "compare.md").write_text(table, encoding="utf-8")
    return 0


def _cmd_sweep(args: argparse.Namespace) -> int:
    agents = args.agent or ["mock"]
    missions = args.mission or ["heist"]
    models = args.model or [None]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = args.out or Path("runs") / f"sweep-{stamp}"
    records = []
    try:
        for agent in agents:
            for mission in missions:
                for model in models:
                    label = f"{_safe(agent)}-{_safe(model or 'scripted')}-{_safe(mission)}"
                    records.extend(
                        run_sweep(
                            agent=agent,
                            mission=mission,
                            tries=args.tries,
                            out_dir=base / label,
                            model=model,
                            script=args.script,
                            world_name=args.world,
                            gate=args.gate,
                            timeout=args.timeout,
                            debrief=_debrief_enabled(args),
                            debrief_policy=args.debrief_policy,
                        )
                    )
    except AdapterNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (KeyError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    table = format_sweep_table(summarize_records(records))
    base.mkdir(parents=True, exist_ok=True)
    (base / "sweep.md").write_text(table, encoding="utf-8")
    print(f"wrote {base / 'sweep.md'}")
    print(table, end="")
    return 0


def _debrief_enabled(args: argparse.Namespace) -> bool:
    """Return whether this invocation requests a debrief (policy implies it)."""
    return bool(args.debrief or args.debrief_policy is not None)


def _default_out(agent: str, mission: str, model: str | None) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = f"{_safe(agent)}-{_safe(model or 'scripted')}-{_safe(mission)}-{stamp}"
    return Path("runs") / label


def _safe(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "-" for char in value)


if __name__ == "__main__":
    raise SystemExit(main())
