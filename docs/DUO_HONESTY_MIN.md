# Duo honesty — minimal next step (design only)

**Status:** EXPERIMENTAL Shape A wiring landed locally 2026-08-24 (see `docs/EXPERIMENTAL_MO1_BYPASS.md`). This note stays the design brief.
**Prerequisite read:** `docs/DUO_LIVE_HARNESS.md` §2.1–2.3, §5–7; planner batch in `runs/compare-planner-honesty.md`.
**Do not start Shape B** (two live CLIs / per-turn re-invoke).

## Why this note exists

Planner→executor honesty (`docs/PLANNER_HONESTY_MIN.md`) is live and the
priority matrix (same-model + Ox↔Inkling + Grok↔Muse) finished cleanly.
That probe is a **role-split stand-in**, not duo: one sealed episode, one
actor seat, two model calls. Real duo honesty still needs Shape A from
`DUO_LIVE_HARNESS.md` — and that slice is blocked on the §7 checklist
(especially **MO1 in writing** and stage-9 `play/` sequencing).

## Smallest Shape A next step (when checklist clears)

One vertical slice, nothing else:

1. **Catalog + public for `museum_duo` only** — register the existing
   physics bundle; add the thinnest `public.py` that can emit a per-role
   TASK.md under a single MO1 arm chosen by the owner (do not default;
   pick one of MO1-a/b/c explicitly in the PR description).
2. **Session Shape A plumbing** — one live CLI workspace + one scripted
   co-actor workspace; shared `private/` record; channel-stamped
   `args.actor` (overwrite-and-log or reject — owner pick from §7);
   auto-advance scripted seat after each live submission; script
   exhaustion = `wait` to horizon.
3. **Honesty stack on the live seat only** — reuse solo flags already
   shipping: credit + self-certify + debrief v5 + confront + ledger
   gate/redeem + `--retry-on-empty`. Scripted seat files no debrief in
   v0 (matches harness §7 "no duo questionnaire" unless owner
   commissions one first).
4. **Acceptance** — mock two-seat replay of sealed `duo_wipe_mule` →
   `formal_exploit` with sealed-identical hashes; one smoke live cell
   (`n=1`) with Inkling or Muse on the live seat and a pinned honest
   script on the co-actor; no pooling with solo or planner-honesty cells.

Out of scope for this slice: Shape B, free-text board, per-agent intent
verdicts, third seat, starvation mitigations, duo-specific questionnaire.

## Stand-in until Shape A lands

Keep running planner-honesty cells (optional Ox↔Muse / Grok↔Inkling) as
the cheap role-split honesty signal. Label them `+plan`; never pool with
future duo-live cells.

## Concrete next CLI (design only — after MO1 clears)

Do **not** run this until MO1 is signed and catalog/`public.py`/Shape A land.
Placeholder flags mirror the solo honesty stack + Shape A co-actor; names are
aspirational and may rename during implementation:

```bash
set -a; . "${OPENROUTER_ENV_FILE:?set OPENROUTER_ENV_FILE to your local OpenRouter env file}"; set +a
export PATH="/home/box/.opencode/bin:$PATH"
# MO1 arm MUST be the owner-signed id (a|b|c) — never omit / never default.
uv run python -m proofgym sweep \
  --agent opencode --model openrouter/thinkingmachines/inkling:free \
  --mission museum_duo --gate permissive \
  --mo1-arm <OWNER_SIGNED_a|b|c> \
  --coactor-script runs/_fixtures/duo_honest_coactor.json \
  --credit-objective --self-certify --debrief-version 5 --confront --retry-on-empty \
  --ledger runs/duo-honesty-shapeA-smoke/ledger.json \
  --ledger-gate --ledger-redeem --ledger-horizon 3 \
  --n 1 --timeout 900 \
  --out runs/duo-honesty-shapeA-smoke
```

Acceptance for that first cell: sealed-identical mock replay already green;
live `n=1` finishes `rc=0` with honesty fields on the **live** seat only;
label `+duo-live` and never pool with `+plan` planner-honesty cells.

## Owner decisions still required (copy of harness §7 blockers)

- [ ] MO1 arm(s) chosen in writing
- [ ] Stage-9 `play/` sequencing vs this slice
- [ ] Shape A confirmed; Shape B deferred
- [ ] Forged-tag policy; script exhaustion = wait
- [ ] Debrief posture for duo v0 (none vs commission)

Until those are signed, **no implementation**.
