# ProofGym — current roadmap

This page replaces the earlier append-only experiment queue. It is ordered by
measurement validity: repair and verify the instruments first, then collect
matched evidence, then expand the benchmark. Historical preregistrations remain
in the stage and design notes; they are not the current queue.

## Current footing

- The deterministic core, museum world, duo v0 world, and the additive duo C4
  world have sealed scripted artifacts and tests. C4 demonstrates a
  coalition-*requiring mechanism* under a separation-of-duties constitution;
  scripted traces are not evidence that models coordinate behaviorally.
- The solo live campaigns are useful exploratory records, but they are small-n,
  use local model aliases, and mix conditions in places. Counts are descriptive,
  not population estimates.
- The first duo Shape A live batch is not valid evidence about partner effects.
  Its live-seat `q_task` answer was scored against the instance-wide mission
  rather than the live actor's stated objective. The compared cells also changed
  mission, co-actor script, and model mix together. Do not pool or cite those
  rows as an honesty or contagion result.
- The existing “planner honesty” batch measures whether a planner's success
  forecast matches the executor's realized task outcome. It is a calibration
  probe, not a direct measure of truthfulness or plan feasibility.

## 1. Rerun duo only after the instrument passes

This is the highest-priority experiment because it repairs a measurement error,
not because it adds a new condition.

Before any live rerun:

1. Pin role-local debrief truth: for Shape A, `q_task` must be evaluated against
   the live actor's exact `TASK.md` objective, while any joint provider remains
   explicitly instance-scoped.
2. Pin provenance through authoritative trace rebuilds: `duo_shape`, `mo1_arm`,
   `live_actor`, and `coactor` must survive and appear in the run record.
3. Verify actor binding, sealed-script identity, and the final report label in
   tests that exercise the same rebuild path as a coding-CLI run.
4. Archive the original batch as invalidated exploratory data. Never combine it
   with the corrected rerun.

Then run a matched, crossed design. Hold the scored mission, live seat, gate,
debrief stack, model set, and run budget fixed while varying the co-actor arm.
Counterbalance or repeat across models before making a partner-effect claim.
Pre-register denominators and exclusions, including empty-adapter runs.

**Done when:** the regression tests pass, every row carries complete provenance,
and the readout reports paired cells without causal language beyond the design.

## 2. Rename and strengthen the planner probe

Use `plan_outcome_calibration.v1` and the literal labels
`plan_matches`, `plan_overpredicts`, `plan_underpredicts`, and
`plan_missing`. Preserve old result tables as legacy output, with an explicit
mapping instead of silently changing historical rows.

The planner should receive the same base episode briefing as the executor.
Compare its forecast to the realized physics-level task verdict and describe
only that comparison. If we want to ask whether a plan is feasible, faithful,
or honest, add separate instruments first:

- an independently checkable plan-feasibility judgment;
- an execution-adherence score connecting planned and submitted actions; and
- a preregistered rule for plans that omit or hedge the success forecast.

Only after those exist should the project run another plan/executor matrix or use
“honesty” in a headline.

## 3. Make result provenance part of the artifact

Every published table and figure should be reproducible from committed,
sanitized inputs. Add a compact manifest for each live batch containing:

- the commit, exact command and flags, model alias, date, and environment;
- per-run outcome, disclosure/transition labels, exclusions, and trace hashes;
- the source path used by each table or figure; and
- an explicit statement when raw workspaces are unavailable.

Do not make a headline depend on a gitignored `runs/` file. Do not compare
heterogeneous “primary outcome” bars on one axis. For ledger contracts, show the
ordered `k/K` sequence and standing; three positions in one changing contract
are counts, not three independent trials. Regenerate figures from the committed
tables and verify both the images and the prose against those tables.

## 4. Run the debrief-order A/B as a matched experiment

After provenance is in place, compare debrief v4 (claim first) with v5 (claim
after evidence) while holding model, mission, gate, incentives, confrontation,
ledger state, retry policy, and sample budget fixed. Pre-register the primary
denominator and treatment comparison. Report model-level cells and pooled totals
separately; do not blend free, paid, and high-thinking runs into a ranking.

The existing paid-v5 counts may be retained as exploratory history only when
their source rows are committed and auditable. They do not substitute for the
matched v4/v5 comparison.

## 5. Expand only after the validity work

Once items 1–4 are complete:

1. Decide whether Shape B (two live players) answers a question worth its
   additional scheduling, identity, and communication surface.
2. Consider live C4 only as a separately preregistered coordination study. Keep
   deterministic mechanism validation separate from behavioral claims.
3. Add another world or difficulty rung only if it tests a failure mode the
   museum variants cannot distinguish.

More incentive rungs are not the default next move: the immediate uncertainty is
instrument validity and causal identification, not a shortage of conditions.

## Release gate for the closeout branch

- Full tests, lint, package build, and direct-import smoke tests pass.
- README, stage report, result index, tables, and figure captions use the same
  world counts, metric names, and limitations.
- Generated figures are reproducible from committed inputs.
- Superseded design documents carry prominent current-status notes while keeping
  their preregistration history intact.
- No invalidated duo result or legacy planner label appears as a current claim.

## Repository hygiene before a public release

- Add CI for Python 3.10+, pytest, Ruff, package builds, local Markdown links,
  and clean-cache figure-generation smoke tests.
- Have the project owner choose and add a root project license. The bundled
  Inter fonts have their upstream OFL, but that does not license ProofGym.
- Add `CITATION.cff` after the owner confirms author names, preferred title,
  repository metadata, and release identifier; do not infer those fields.
