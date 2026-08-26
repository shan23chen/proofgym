# Results and provenance index

This directory contains curated operator summaries copied from local,
gitignored runs. It contains no secrets or raw model workspaces, but it also
does **not** contain enough run-level evidence to reproduce most live claims.
Treat these files as descriptive audit history, not a dataset.

## Disposition

| Summary | Current disposition |
|---|---|
| [Plan–outcome calibration](compare-planner-honesty.md) | 36 sequential engagements across 12 heterogeneous contracts; legacy labels; descriptive only |
| [Shape A scripted-coactor batch](compare-duo-honesty.md) | behavioral interpretation invalidated by scorer mismatch and confounded design; runtime telemetry only |
| [Default paid clear batch](compare-paid-clear-batch.md) | descriptive copied table; run-level verdicts/hashes absent |
| [Default free clear batch](compare-free-clear-batch.md) | descriptive; North is 0/2 completed + 1 censored; partial/unmeasured arms separated |
| [High-thinking clear probe](compare-highthink-clear.md) | condition not reproducible: depended on an uncommitted PATH wrapper; withhold comparisons |
| [OSS/flash clear batch](compare-oss-clear-batch.md) | descriptive copied table; zero-step and upstream failures retained explicitly |

The paid-v5 disclosure source cited by the former figure,
`runs/compare-paid-honesty-v5.md`, is absent. Its 14/14 and per-model
reaffirm headlines are therefore withheld from the current readout.

## What can be reproduced now

- deterministic sealed traces, checker results, and outcome matrices;
- the patched constitution's closure of the registry exploit;
- figure layouts from the curated constants in the builder scripts; and
- all unit/regression tests for the harness and scoring logic.

Figure regeneration does not re-measure live results. See the
[patched-museum readout](../stage2/STAGE2_READOUT.md) and
[planner/duo readout](../stage3/STAGE3_READOUT.md) for the current claim
boundaries.

## Required live-result schema

New live results should conform to [SCHEMA.md](SCHEMA.md). At minimum, commit
one sanitized row per attempt with:

- experiment/run id, exact Git commit, UTC time, full command, seed;
- requested and resolved provider/model plus adapter/CLI version;
- world, mission, constitution, gate, questionnaire/scorer, and prompt/config;
- attempted/completed/censored/retried status and preregistered inclusion rule;
- contract `k/K` and starting standing for ledger sequences;
- outcome, task success, per-question truth/declaration/mismatches, transition,
  settlement, zero-step and adapter errors; and
- hashes of sanitized verdict, trace, plan, and ledger artifacts.

Generate Markdown tables and figures from that manifest so counts, captions,
and plots cannot drift.

## Interpretation rules

- Exact small-cell counts are not population rates or rankings.
- Sequential positions in one ledger contract are not independent replicates.
- “Corrected,” “doubled_down,” and outcome labels describe artifacts and
  traces, not mental states.
- Never pool solo, `+plan`, and `+duo-live` conditions.
- Report unmeasured, censored, partial, retried, and completed attempts
  separately.
