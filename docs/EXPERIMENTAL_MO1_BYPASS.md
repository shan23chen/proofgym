# Shape A experimental deviation record

**Status:** historical operations record, 2026-08-24. The original live batch
is invalidated for behavioral interpretation. Current protocol and rerun
requirements are in [`DUO_HONESTY_MIN.md`](DUO_HONESTY_MIN.md).

The first Shape A implementation proceeded before the earlier design
checklist had formal owner sign-off. The branch made these explicit choices:

| Design point | Experimental choice |
|---|---|
| MO1 wording | arm `a` for the first batch; `b` and `c` remained selectable |
| topology | Shape A: one live CLI plus one scripted coactor |
| forged actor tags | bind submissions to the declared live seat and record an integrity event |
| script exhaustion | submit `wait` until the horizon |
| debrief | live seat only, using the museum-derived v5 questionnaire |
| provenance | record `duo_shape`, `mo1_arm`, `live_actor`, and `coactor` in trace metadata |

Two later audit findings supersede the original result interpretation:

1. the exfiltration `q_task` truth did not match the live E seat's TASK brief;
2. the published contrast changed mission and coactor script together.

The scorer/provenance implementation has since been corrected and covered by
regression tests. The original 21 runs remain runtime telemetry only; none of
their legacy disclosure labels should be cited as evidence of honesty,
contagion, or a partner effect.

Reproduce the deterministic harness smoke from the tracked fixture:

```bash
uv run python -m proofgym run \
  --agent mock --script duo_wipe_mule \
  --world museum_duo --mission exfiltration --gate enforce \
  --mo1-arm a --live-actor E \
  --coactor-script tests/fixtures/duo/duo_wipe_mule_coactor.json \
  --out runs/duo-shape-a-smoke
```
