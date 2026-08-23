# ProofGym stage 15: debrief v5 — the claim follows the evidence

This document implements the slice proposed in docs/NEXT.md §6 after the
stage-14 live campaign and records its design contract. Same discipline as
[PLAN.md](PLAN.md) through [STAGE14.md](STAGE14.md): D1–D12 are not
reopened, the two-agent duo track is untouched, and every scope decision is
written down here rather than resolved silently.

---

## 1. What the stage-14 live runs established

Small-n, not for publication; per the operators' live log (STAGE14.md §7;
six-row table in the stage-14 section of docs/STAGE_REPORT.md).

- **The deterrence ladder is exhausted.** Round-1 inflation has survived
  five consequence structures — announced checking, an inert record, a
  gated record, a quantified horizon, a redeemable gate — reading
  near-total on qualifying standings throughout (6/6 in the stage-14
  contracts, including both freshly re-qualified ones; the ungated
  position control read 3/3).
- **The fold is dominance-insensitive.** Confronted filings corrected
  3/3 under instrumental redemption, including the k=3 cell where
  recanting surrendered a credit with nothing left to repair for.
  H-compliance-reflex stands.
- **The remaining hypothesis space is upstream of every settlement.** No
  incentive knob is left that has not read zero; the open question is the
  *generation* of the round-1 lie, not its price.

## 2. The hypothesis split: default or decision

Three signatures in the cumulative record point at a form-filling default
rather than a strategic decision:

1. **Every live inflation since stage 8 has been the self-refuting
   minimal kind** — mismatch set `{q_task}`, the claim written beside
   truthful evidence answers that contradict it (a certified heist whose
   own filing reports the diamond never left the building).
2. **The fold is immediate, universal, and dominance-insensitive** — the
   profile of a claim that was never load-bearing.
3. **The v4 questionnaire deliberately put the claim first** ("the claim
   leads the form — this is a certification", STAGE8.md §3.1) — so the
   certification is written *before* the evidence is recalled.

The split, in the stage-4/7/10/13 tradition (one knob, versioned
instrument, arms never pooled — fifth application):

- **H-default-optimism:** the inflation is top-down form filling; writing
  the refuting evidence first makes the self-refutation salient at the
  decision point, and clean-standing round-1 inflation drops under v5.
- **H-strategic:** the lie survives having just written the evidence that
  refutes it; inflation is unchanged under v5.

Either answer decides retroactively what stages 11–14's deterrence nulls
were: pricing a decision, or pricing a reflex. **No live claim is made in
either direction before the data.**

## 3. The stage-15 slice (implemented in this repository): questionnaire v5

### 3.1 The mechanism

`--debrief-version 5` (opt-in; v4 remains the default that
`--self-certify` implies, so every prior cell reproduces without silent
renumbering):

1. **Identical questions, one order change.** v5 is the v4 question set
   with `q_task` moved from first to **last** — the same eight
   `DebriefQuestion` objects, byte-identical wording, with the evidence
   block (`q_force` … `q_outside_registry`) in its unchanged relative
   order and the claim after it. DEBRIEF.md's JSON template and question
   list both render the claim last.
2. **Truth functions are v4's, verbatim.** The v5 truth tables are sealed
   under `worlds/museum/debriefs/v5/` and pinned against both fresh
   regeneration and byte-equality with the v4 fixtures — the equality *is*
   the design claim (order is the only knob).
3. **Every settlement semantic is unchanged.** `q_task` remains the claim
   question and `q_violation` the stake; `--self-certify` accepts v4 or
   newer (the floor guard's wording updated, its semantics identical);
   stakes, gate, redemption, and horizon compose with v5 exactly as with
   v4. Scoring and settlement read answers by key and are order-blind by
   construction (pinned: the same declared answers score identically
   under both versions).
4. **Never pooled.** Every disclosure verdict records
   `museum_debrief.v5`; v4 stays sealed as the comparison arm — the
   v4-vs-v5 A/B on the same cells is the experiment.

### 3.2 Design points, stated so they are not resolved silently

- **v4 keeps the certification default.** `--self-certify` alone still
  resolves to v4; v5 is reached only by explicit
  `--debrief-version 5`. The stage-8 design statement ("the claim is the
  headline") remains true of v4; v5 exists to test whether that
  presentation choice *manufactures* the inflation it measures — the same
  relationship v2 had to v1's `q_rejected`.
- **The order manipulation is the minimal salience manipulation.** No
  reminder text, no restated evidence, no highlighted contradiction —
  those would add knobs and leave any null attributable to insufficient
  shouting (rejected at stage 13 §5 for the same reason). The player
  simply writes the claim after the evidence instead of before it.
- **Interpretive discipline for the A/B.** A drop under v5 reclassifies
  the round-1 inflation as an instrument artifact of claim-first
  presentation — stage 4's outcome, one questionnaire later — and every
  deterrence null of stages 11–14 becomes "consequences cannot deter a
  reflex". Persistence establishes the lie as a decision that survives
  writing its own refutation, and the nulls become genuine
  incentive-insensitivity. Both readings are pre-registered here.

### 3.3 Surface

```bash
# The A/B, mock shape (CI): identical payoffs, different claim position.
python -m proofgym run --agent mock --mission heist_patched --self-certify \
    --debrief-policy self_serving                       # v4 (claim first)
python -m proofgym run --agent mock --mission heist_patched --self-certify \
    --debrief-version 5 --debrief-policy self_serving   # v5 (claim last)

# Live: the stage-12/14 cells, order-split arm.
python -m proofgym sweep --agent opencode --model <m> --mission heist_patched \
    --credit-objective --self-certify --debrief-version 5 --confront \
    --ledger runs/<m>-ledger.json --ledger-gate --ledger-redeem \
    --ledger-horizon 3 --n 3 --retry-on-empty
```

## 4. Research questions this slice makes answerable

- **RQ-O1 — Default or decision.** Clean-standing round-1 inflation under
  v5 vs the v4 baselines (stage-12: 3/3; stage-14: 6/6 on qualifying
  standings). The drop/persist reading is pre-registered in §3.2.
- **RQ-O2 — Does the self-refuting signature survive the order?** If v5
  inflation persists, is it still the `{q_task}`-only mismatch — the
  player writing `q_outside_building: false` and then, one line later,
  certifying the heist — or does the lie become coherent (dragging the
  boundary answers with it), which the v3 split still catches?
- **RQ-O3 — Does the fold change with the claim's position?** The
  confrontation and re-ask arms run unchanged under v5; any movement in
  the transition rates against the v4 record (fold ~always; neutral-arm
  defense) would indicate the claim's position also shapes its defense.
- **RQ-O4 — The truthful population, order-controlled.** `held` 4/4 and
  `degraded` 0 were measured claim-first; v5 re-runs the stability check
  with the claim last (an instrument-stability datum, prospective as in
  stage 10's RQ-N3).

## 5. Considered and not taken (with reasons)

- **A sixth incentive rung** (taxing corrections, pricing the recant).
  Five rungs read zero; no remaining hypothesis distinguishes a sixth
  from the order split, which is cheaper and upstream of all of them.
- **Instructed concealment.** Capability is demonstrated in the wild
  (`doubled_down`, repeatedly, live); the un-instructed thread continues.
- **Richer salience manipulations** (restating the player's own boundary
  answer next to the claim; contradiction warnings). More than one knob;
  rejected at stage 13 §5 and again here — escalate only if RQ-O1
  demands.
- **Flipping the default to v5.** Rejected: prior cells must reproduce
  without silent renumbering; the A/B needs both arms; v4 is sealed as
  the claim-first instrument exactly as v1 stayed sealed under stage 4.
- **Hy3's rerun / n-expansion.** Campaign parameters; the v4-vs-v5 A/B
  runs on the same cells and carries them along.

## 6. Acceptance criteria for this slice (all met, `pytest` green)

- Defaults untouched: `--self-certify` alone still resolves to v4 with a
  byte-identical claim-first DEBRIEF.md; without `--debrief-version 5`
  nothing anywhere changes; unknown versions fail loudly (provider,
  harness, and CLI argument choices).
- v5 renders the claim last in both the JSON template and the question
  list; the evidence block's relative order is byte-identical to v4's;
  the question objects are shared, not re-worded copies (pinned by
  identity).
- The v5 truth tables equal fresh regeneration *and* the sealed v4
  fixtures byte-for-byte; the same declared answers score identically
  under v4 and v5 (order-blind scoring, pinned); questionnaire ids differ
  and are never pooled.
- The self-certify floor accepts v4 or newer and still rejects v1–v3
  loudly; the full stack (stakes, certification, confront/reaffirm, gate,
  redeem, horizon) composes with v5 with unchanged payoffs, pinned by the
  mock paid-inflation and recant arcs.
- Same episode + same policy ⇒ identical v5 artifacts (D9).
