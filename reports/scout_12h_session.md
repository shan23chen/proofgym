# Scout session note — duo track (12h window, handoff ~noon ET Aug 23 2026)

Duo-track-only session per the mid-window collision update: the planned
Stage 1–8 frontier synthesis was **dropped before anything was written**
(Random Researcher owns `docs/STAGE_REPORT.md` + `docs/NEXT.md`); no
`reports/frontier_*` files exist on any branch. Nothing in this session
touches `worlds/museum/`, the stage 2–8 ladder, `runs/`, `compare-*.md`,
`core/`, `z3check/`, or `play/`. D1–D12 and M1–M10 unchanged. Nothing was
merged to main; no runs were deleted.

## What shipped

### 1. `museum_duo` rebased onto stage-8 main — PR [#17](https://github.com/shan23chen/proofgym/pull/17)

Branch `cursor/museum-duo-v0-rebase-5445` (supersedes PR #4's base,
`museum-duo-v0` @ `927784cd`, which was rooted before stage 2). All five duo
commits cherry-picked cleanly; **one conflict** (`pyproject.toml`
package-data — main's expanded museum `debriefs/` list vs. the duo traces
line; resolved by keeping both). Zero-diff budget re-verified post-rebase:
`git diff main` over `core/`, `z3check/`, `worlds/museum/`, `play/`, and
all pre-existing tests is empty.

- **pytest: 184 passed** (main baseline 161 + 23 duo tests), no skips.
- **Flip twin re-verified schedule-pure:** sealed twins differ at exactly
  steps 21/23 (H's amend/wait swap), identical per-agent multisets; at E's
  exit (step 22) the registry differs only in lobby membership; C1 fires at
  exactly step 22 in the twin. `formal_exploit` → `illegal_shortcut` on
  the schedule alone.
- `reports/duo_v0_outcome_matrix.md` — the five sealed traces: outcomes,
  winners, flip-twin analysis, reproduction snippet.
- `reports/duo_next.md` — five ranked duo-only next bets with information
  value / cost / collision risk.

### 2. Top next bet, tried and landed — PR [#18](https://github.com/shan23chen/proofgym/pull/18) (stacked on #17)

Branch `cursor/duo-enforce-gate-5445`: Bet 1 from `duo_next.md` — run the
duo world behind the world-agnostic `EnforceRunner` (first gate-mode
exercise of a second world) and quantify the MO4 starvation channels.
Two new files only (`tests/test_duo_gate.py`, `reports/duo_enforce_gate.md`).

- **pytest: 192 passed** (184 + 8 new), ruff clean.
- Findings, all pinned by test: (i) the runner abstraction clears
  PLAN_MULTIAGENT §11 no-go trigger 1 in gate mode with zero core changes —
  a permissive run even seals hashes byte-identical to the sealed audit
  twin; (ii) schedule-relative legality is now a *gate* fact (base schedule
  enforce-clean → `formal_exploit`; flipped twin rejected once, C1 at step
  22 → `honest_failure`), and one rejection cascades because the rejected
  actor stays active; (iii) **MO4 rejection-spam starvation measured**: the
  victim gets 3 of a parity-20 turns and zero after spam starts (18
  rejections, 17 out-of-turn no-ops burned); the spammer needs no
  capability because C2 is action-keyed; (iv) a second, symmetric channel —
  out-of-turn flooding — passes the gate as `executed: true` identity
  no-ops and is invisible to rejected-step counts. MO4's sanctioned
  mitigation deliberately **not** added (measure before mitigating).

### 3. Bet 2 delivered as design note — PR [#21](https://github.com/shan23chen/proofgym/pull/21) (stacked on #18)

Branch `cursor/duo-c4-design-5445`: `docs/DUO_C4_DESIGN.md` — the
coalition-requiring C4 (`museum_duo_public.v1_coalition`) as **design
only**: no constitution code, no state-schema change, no resealing; suite
still 192 passed. Two §6.4 errors found on paper before any code: the
sketch mis-names `duo_relay` as the surviving trace (H amends *and* picks
up at step 15 — the true institutional artifact is `duo_wipe_mule`), and
the one-directional wording has a steal-first hole (the OG surgical-lobby
route stays solo-legal), fixed by a symmetric clause with a solo-closure
proof sketch. Includes the `amended_by` hash-blast options (reseal
pre-merge / sibling package / conditional payload) and the M10 owner
go/no-go checklist. Implementation is gated on that checklist.

### 4. Live-harness design note — PR [#23](https://github.com/shan23chen/proofgym/pull/23) (stacked on #21)

Owner had not greenlit C4 code or MO1, so the next zero-collision item:
`docs/DUO_LIVE_HARNESS.md` on `cursor/duo-live-harness-design-5445` —
**design only**, suite untouched at 192. Specifies the one-runner /
two-workspace session with channel-stamped actor identity (never trust
`args.actor` from a player), Shape A (one live CLI + session-advanced
scripted co-actor; today's one-shot adapters unchanged) as the thin slice
vs. Shape B (two live CLIs, deferred), the #18-implied requirements
(per-actor metering and turns-received reporting, the two starvation
channels as distinct columns), a duo mock adapter that interleaves by
reading authoritative `active`, three MO1 disclosure arms **as
experimental variables with no default taken**, and a ten-item go/no-go
checklist. Stays a note until MO1 is decided and OG stage-9 `play/` work
is sequenced.

## What was tried next / what failed

Nothing failed technically this window: the rebase had a single trivial
conflict, all suites are green, and the top bet landed on the first
attempt (semantics behaved exactly as PLAN_MULTIAGENT predicted on paper —
the prototypes confirmed both starvation channels before any test was
written). The dropped item was the frontier synthesis (ownership collision,
see header), not a technical failure. Bets deliberately not attempted:

- **Bet 2, C4 coalition-requiring constitution** — code deliberately not
  written (`amended_by` moves sealed duo hashes; M10 owner decision
  required); delivered instead as the [#21](https://github.com/shan23chen/proofgym/pull/21)
  design note, which turned up two paper bugs in §6.4 that coding first
  would have baked in.
- **Bet 3, live duo harness thin slice** — mechanically feasible
  (`catalog.py`'s `WorldBundle` protocol is world-agnostic) but touches
  shared `play/`/`catalog.py` surfaces (highest OG-collision risk of any
  bet) and is gated on MO1 (brief disclosure policy), an explicitly
  reserved experimental variable. Also now informed by #18: the harness
  must meter submissions per actor and report per-actor turns-received.
- **Bets 4/5** (duo cell in `proofgym report`; more F1 traces) — skipped as
  low value; reasons in `duo_next.md`.

## Recommended handoff (noon)

1. **Review/merge order: #17 then #18 then #21 then #23** (stacked). #17
   is the base swap for PR #4 — after it lands, close #4 or repoint it.
   Nothing is merged; all are conflict-free against `70ab159` main as of
   this writing.
2. **Owner decisions queued** (M10): (a) the #21 C4 checklist — seven
   written decisions, of which the state plan (reseal-pre-merge vs.
   sibling package) is load-bearing and cheapest to take **before** #17
   merges; (b) live-harness go/no-go with MO1 decided explicitly; #18's §4
   lists the two harness design requirements the starvation measurements
   imply.
3. **If picking up code immediately:** implement C4 per the #21 checklist
   once signed, or the live-harness thin slice per the #23 checklist once
   MO1 is decided and stage-9 sequencing is agreed. Neither was
   implemented this window — both are design-gated on owner decisions,
   and no code was written for either.
4. Baselines for regression checking: main 161 passed; +duo rebase 184;
   +gate probes 192.
