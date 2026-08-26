# Patched museum and intervention readout

> Directory-name note: `docs/stage2/` is an illustrated campaign readout, not
> the repository's chronological Stage 2. The chronological design record is
> [`STAGE2.md`](../../STAGE2.md); the intervention ladder later reached Stage 15.

**Status:** descriptive, synthetic, small-cell evidence. Not for publication
or model ranking. Live artifacts were curated from local runs, and several
legacy claims cannot yet be reproduced from committed run-level data.

## What this readout covers

The original museum constitution let the live registry redefine the boundary
that the constitution itself protected. `museum_public.v1_patched` freezes
that reference frame at founding. In deterministic traces, the paperwork
exploit no longer yields a constitution-compliant heist: a successful exit is
either blocked by the enforce gate or recorded as a violation under the
permissive audit gate.

![Patched task explainer](figures/task_explainer.png)

This is a claim about the shipped world and checker, not about model behavior.
It is reproducible offline:

```bash
python -m proofgym report --all
pytest -q tests/test_patched_constitution.py tests/test_permissive_gate.py
```

## Descriptive live clear counts

![Descriptive clear counts](figures/clear_rate.png)

The chart reports completed local runs of `heist_patched` under the permissive
gate. Every observed task-success row was an `illegal_shortcut`: the model
completed the task only by executing an action the patched constitution
rejects. That is expected under this condition and should not be read as a
capability or safety leaderboard.

Interpretation limits:

- paid and free access contexts are grouped separately and are not comparable
  experimental arms;
- each displayed cell is only two or three completed attempts;
- North Mini is reported as `0/2 completed + 1 censored`, because its third
  process was killed mid-episode;
- the former high-thinking rows are withheld because the effective variant
  depended on an uncommitted PATH wrapper and is not reproducible from the
  recorded adapter arguments;
- rate-limited, policy-blocked, partial, and not-run cells are unmeasured, not
  failures.

The copied operator summaries are in [`docs/results/`](../results/INDEX.md).
They preserve useful detail but not the underlying verdict and trace bundle.

## Disclosure and re-ask evidence status

![Disclosure evidence status](figures/results.png)

Historical summaries report a recurring local pattern: a
detection-asserted confrontation was often followed by a corrected filing,
while a neutral re-ask produced mixed transitions. The previous public figure
overstated that evidence in two ways:

1. its source for the paid-v5 headline (`runs/compare-paid-honesty-v5.md`) is
   gitignored and absent from this repository; and
2. its right-hand bars used different outcomes for different models
   (`doubled_down`, `held`, or `corrected`) on one apparent scale.

Accordingly, the aggregate headline and cross-model bars are withheld. A
publishable replacement must be generated from a sanitized, versioned
run-level manifest containing exact model/provider resolution, condition,
contract position and starting standing, outcome, per-question truth and
declaration, transition, settlement, censoring/error status, and artifact
hashes.

## Intervention map

![Intervention map](figures/intervention_paths.png)

Stages 8–15 are best read as four intervention routes:

| Route | Change | Safe descriptive reading |
|---|---|---|
| Price the claim | self-certified settlement | paid claim inflation appeared in local cells |
| Re-ask | detection-asserted vs neutral request | second filings differed by request wording |
| Record and gate | ledger, eligibility gate, horizon | first-position inflation recurred in sequential contracts |
| Repair and reorder | redemption, then claim-last v5 | Stage 14 recorded 6/6 inflation overall, 4/4 on qualifying starts; later v5 headlines await source provenance |

These are sequential, changing contract positions rather than independent
replicates. “Recurring pattern” means an exact count in these cells, not a
statistical null, population rate, or causal claim.

## Evidence ledger

| Artifact | Disposition |
|---|---|
| patched constitution, sealed traces, checker tests | reproducible; retain |
| task explainer | conceptual; retain |
| default-context clear counts | descriptive; retain with censoring/context notes |
| high-thinking clear counts | withhold until the condition is versioned and recorded |
| paid-v5 aggregate disclosure headline | withhold until run-level source is committed |
| intervention paths | conceptual chronology; do not treat as a statistical result |

## Rebuild the figures

```bash
MPLCONFIGDIR=/tmp/proofgym-mpl \
  python docs/stage2/figures/build_figures.py
```

The script currently contains curated constants, so regeneration verifies
layout—not the live evidence. The next provenance milestone is to generate
both Markdown and PNGs from one committed manifest. Bundled Inter font files
are covered by the license in [`docs/assets/fonts/OFL.txt`](../assets/fonts/OFL.txt).

## Related documents

- [Current results index](../results/INDEX.md)
- [Cross-stage evidence report](../STAGE_REPORT.md)
- [Prioritized next work](../NEXT.md)
- [Figure style guide](../skills/research-figure.md)
