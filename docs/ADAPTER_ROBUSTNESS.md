# Adapter robustness: zero-step CLI casualties

**Motivation.** The live logs show a recurrent failure class: a coding CLI
exits with code 1 having submitted zero actions and filed nothing (first
recorded as the stage-5 "adapter casualty", STAGE6.md §1; recurrent for
several models per the operators' log). Scored by the normal rules, such a
run reads `honest_failure` / `missing` / `no_claim` — correct bookkeeping of
an absent player, but noise in every live rate, and the precondition item
for the stage-8 campaign in [NEXT.md](NEXT.md).

## The distinction this adds

A coding-CLI attempt is an **adapter error** only when all three hold:

1. the CLI exited nonzero,
2. no action was ever submitted,
3. no `debrief.json` was filed.

That combination means the process died before engaging the episode at all.
Everything short of it is player behavior and is deliberately left alone:

| Attempt looked like | Classified as | Why |
|---|---|---|
| exit ≠ 0, zero steps, nothing filed | **adapter error** | absent player |
| exit 0, zero steps | player silence | a measured strategy (STAGE3.md RQ-D4, STAGE5.md RQ-S5) |
| exit ≠ 0, zero steps, `debrief.json` filed | refusal that reported itself | the stage-6 escape route (STAGE6.md §4.3) |
| exit ≠ 0 after submitting steps | partial episode | the player engaged; the return code is recorded |

## What is recorded (always on)

- `verdict.json` carries a top-level `adapter_error` boolean (restored by
  `load_run_record`).
- `report.md` appends an explicit adapter-error note.
- Compare tables gain an `Adapter` column (`ok` / `error`); sweep tables
  gain an `Adapter errors` count per cell, next to `Flagged`.

Scoring is untouched: the outcome, disclosure label, and settlement of an
adapter-error run are computed exactly as before (the settlement arithmetic
must not depend on why a filing is absent). The marker exists so analysts
can exclude absent players from disclosure and settlement denominators —
`missing` no longer conflates "crashed before playing" with "chose not to
file".

## `--retry-on-empty` (opt-in, default off)

With `--retry-on-empty` (run / compare / sweep), an adapter-error attempt is
discarded wholesale — fresh workspace, fresh private record, fresh episode —
and the episode is started exactly once more. The discarded attempt's return
code and a stderr tail are preserved in the adapter metadata
(`failed_attempts`), never hidden; a run whose second attempt also dies is
marked `adapter_error` as usual.

```bash
python -m proofgym sweep --agent opencode --model <m> --mission heist_patched \
    --credit-objective --self-certify --n 5 --retry-on-empty
```

Why **off by default**, written down so it is not flipped as an oversight:

- **A retry is a condition, not a fix.** Replacing crashed attempts
  resamples the player and can bias any rate correlated with crash timing.
  Runs with and without the flag are different experimental conditions;
  the flag is recorded in the adapter metadata (`retry_on_empty`, present
  only when enabled) so they are never pooled silently — the same rule as
  gate modes and questionnaire versions.
- **The trigger is deliberately narrow.** Only the absent-player class is
  retried. Silence, refusals, and post-play crashes are behavior; retrying
  them would erase data the disclosure instruments exist to measure.
- **Exactly one retry.** The goal is to stop sweeps being thinned by
  transient CLI failures, not to guarantee a played episode; unbounded
  retries would hide a systematically broken adapter instead of surfacing
  it in the `Adapter errors` column.
- **Mock runs reject the flag loudly.** The mock adapter cannot fail to
  start, and CI must stay deterministic (D9); an inert-but-recorded
  condition flag on mock cells would be misinformation.
