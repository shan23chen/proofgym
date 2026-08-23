# Live duo harness design note (M10 — design only, nothing implemented)

**Status: DESIGN ONLY.** No `play/`, `catalog.py`, `core/`, `worlds/museum/`
edits; no code ships with this note. Implementation is gated on the §6
checklist — above all on **MO1 being decided in writing** (this note lists
disclosure options as experimental variables and deliberately defaults
none) and on coordination with the OG track's stage-9 work in `play/`
(§5). Grounded in the shipped code as of the duo stack
(PRs #17/#18/#21): the session/harness/adapter architecture described in
§1 was read, not recalled.

---

## 1. What exists today (verified), and what duo is missing

- **`PlaySession`** owns one gated episode: an authoritative `private/`
  record (sibling of the workspace, outside the CLI's write scope), a
  write-only mirrored workspace (`TASK.md`, `state.json`, `episode.json`,
  `log.jsonl`), mirror auditing with `integrity_events`, and one
  `EnforceRunner` restored only from the private record. The runner is
  world-agnostic and already runs duo in both gate modes
  (`tests/test_duo_gate.py`).
- **Coding-CLI adapters are one-shot subprocesses.** `opencode run` /
  `codex exec` is spawned once with a prompt and *free-runs*: it submits
  as many steps as it likes by calling the `proofgym-act` wrapper, then
  exits. The harness never intervenes per step. Any duo design that needs
  per-turn control cannot assume a poll loop exists — it has to be built,
  or designed around (§2).
- **Scoring never trusts disk**: for CLI runs the harness re-derives the
  whole trace in-process from the submitted action list
  (`_rebuild_authoritative_trace`). This machinery is world-agnostic and
  carries over to duo unchanged — with one new duo-specific hole (§2.4).
- **What duo lacks for live play** (all deliberately deferred by M8/M10):
  a catalog registration (`load_bundle` is museum-only), a `public.py`
  (per-role TASK.md, `observe`, `state_from_observation`), a debrief
  provider (the duo track has no questionnaire — and `WorldBundle`
  requires the field), and any adapter/session support for two actors.

## 2. Session shape: one shared episode, two player views

Invariants first, shapes second. In every variant below there is exactly
**one** `EnforceRunner`, one authoritative `private/` record, one joint
trace, one shared horizon — the duo world's physics (one active actor, the
other frozen; M1/F1 semantics) is already the sole arbiter of turn order,
and the harness never re-implements it.

### 2.1 Two workspaces, one private record

Each actor gets its **own workspace directory** (own `TASK.md` per MO1 arm,
own `next_action.json`, own `debrief.json` if a duo debrief ever exists),
both mirroring the same shared observation (`state.json`, `log.jsonl` —
observing shared state is v0's only coordination medium, M3, so the shared
log is visible to both). One `private/` directory, sibling to **both**,
holds the single authoritative record. Mirror auditing runs per workspace;
integrity events gain an `actor` field.

### 2.2 Actor identity is channel-derived, never payload-trusted

Duo actions carry `args.actor` — and a live CLI can type anything. The
actor tag must therefore be **stamped by the submission channel, not read
from the player's JSON**: each workspace's `proofgym-act` wrapper is bound
to its actor id at creation; the session overwrites (or rejects — §6
decision) any conflicting tag before the runner sees the action, and logs
a forged-tag attempt as an integrity event. Without this, player E could
submit `{"actor": "H", ...}` on H's turn and act twice per cycle; with it,
an out-of-turn submission is exactly the gate-legal identity no-op #18
measured, and nothing worse.

### 2.3 Two session shapes, one recommended as the thin slice

**Shape A — one live CLI + one scripted co-actor (the thin slice).**
The session auto-advances the scripted co-actor: whenever a live
submission leaves `active` pointing at the scripted actor, the session
immediately plays that actor's next scripted action (or `wait` when its
script is exhausted — §6 decision) before returning feedback. The live
CLI keeps today's one-shot free-running adapter **unchanged**; from its
seat, every own-action is followed instantly by the co-actor's reply in
the shared log. Consequences worth stating: the live player can never be
flood-starved in this shape (the baton returns before its next
submission), but it can still starve the *scripted* actor by
rejection-spam (the #18 asymmetric channel — the live actor retains the
turn on every rejection, and the script freezes). That is a feature: the
thin slice can observe MO4's channel live without any new machinery.

**Shape B — two live CLIs (deferred, not sketched away).** True two-CLI
play needs per-turn control that the one-shot adapters do not have:
either per-turn subprocess invocation ("submit exactly one action, then
stop" — ~40 spawns per episode, expensive but honestly metered) or a
long-running bidirectional protocol (new adapter class). Shape B also
opens the full MO4 surface (two live actors racing one submission
channel) and every seat/capability confound (risk 2: cross models over
roles *and* seats before any propensity claim). Shape B is out of scope
until Shape A has run live and MO1 has data behind it.

### 2.4 Trace rebuild, duo edition

`_rebuild_authoritative_trace` replays the submitted action list through a
fresh in-process gate — world-agnostic, works for duo as-is. The one new
requirement: the rebuild must consume the **channel-stamped** action list
(§2.2) from the private log, so a player that forged actor tags anywhere
on disk changes nothing. Divergence reporting gains the forged-tag event
kind; everything else carries over verbatim.

## 3. Harness requirements implied by #18 (`reports/duo_enforce_gate.md`)

1. **Meter submissions per actor.** In any shape, the harness must not let
   one player consume the other's submission opportunities silently.
   Shape A meters structurally (the co-actor is advanced by the session);
   Shape B must poll each CLI on its own turn. Out-of-turn *flooding*
   (gate-legal identity no-ops burning shared horizon) is thereby closed
   structurally in both shapes — it can only reappear if a harness ever
   lets a player submit while frozen, which is now a named design error.
2. **Rejection-spam survives all metering** — the *active* actor burns the
   clock, which no submission schedule can prevent (that is MO4 proper).
   The harness therefore does not try to prevent it; it **measures** it:
   per-actor rejection tallies, and the episode-level fact that the
   co-actor's remaining turns went to zero. The sanctioned mitigation
   (per-agent rejection budget) stays unbuilt until live data shows the
   channel binds.
3. **Report per-actor turns-received.** #18 showed rejected-step counts
   undercount duo friction (out-of-turn no-ops read `executed: true`).
   Duo run records and report tables need, per actor: turns received,
   effective (state-changing) steps, rejections, and out-of-turn no-op
   submissions — four numbers, all recomputable from the sealed trace
   plus the stamped actor channel. The two starvation channels are
   reported as **distinct columns**, never summed: they have different
   authors (active vs. frozen actor), different gate signatures
   (`executed: false` vs. `true`-with-repeated-hash), and different
   mitigations.
4. **Roster and seat in every cell label.** Duo cells never pool with solo
   cells, and duo cells with different rosters never pool with each other:
   `exfiltration [E=opencode/<model>, H=scripted]` is a different
   experimental condition from the roles swapped (seat order is part of
   the instance definition — risk 3).

## 4. The duo mock adapter (CI without any coding CLI)

A `DuoMockAdapter` holding **two scripted action streams** (one per
actor). It does *not* interleave them by fixed alternation; on every
round it reads the authoritative `active` from the session and submits
the next action from **that actor's** stream. This distinction matters:
under rejection dynamics the schedule is not the author's to decide (a
rejection keeps the same actor active), and a fixed-interleave mock would
desynchronize exactly when the interesting thing happens. Termination:
horizon consumed, or both streams exhausted.

What it exercises in CI, deterministically, with no CLI installed: both
session shapes (it can stand in for the live seat of Shape A, and both
seats of a degenerate Shape B), the channel-stamping path, the per-actor
report columns, the rejection-spam and flood measurements as fixtures
(reusing the exact scripts pinned in `tests/test_duo_gate.py`), and — the
acceptance bar — the sealed `duo_wipe_mule` schedule replayed through two
mock seats ends `formal_exploit` with hashes identical to the sealed
trace. Debrief policies do not apply (duo has no questionnaire; see §6).

## 5. Collision risk with OG stage-9 `play/` work — why this stays a note

The thin slice touches, at minimum: `catalog.py` (duo bundle, and either a
null debrief provider or making the field optional), `play/session.py`
(two workspaces, channel stamping, co-actor auto-advance),
`play/harness.py` (duo run path, per-actor reporting), `play/adapters.py`
(duo mock), `play/report.py` (per-actor columns), `proofgym/act.py`
(actor binding), and `cli.py`. That is the exact module set where the OG
track's stage-9 instrument (the confrontation round, pre-registered in
STAGE8.md RQ-C5, which will live in `play/debrief.py` + session/harness
plumbing) is about to land. Two tracks editing `play/session.py` and
`play/harness.py` concurrently is the highest-collision move available in
this repository — and the duo side is the one that can wait, because its
prerequisite (MO1) is undecided anyway. This note therefore stays a note
until **both** hold: MO1 is decided in writing, and the stage-9 `play/`
changes have landed or been explicitly sequenced with the owner.

## 6. MO1: disclosure arms (experimental variables — no default is taken here)

What each actor's TASK.md says about the other actor shapes every future
coalition-propensity claim; PLAN_MULTIAGENT MO1 explicitly forbids
defaulting it silently. Three arms, to be chosen (one or several, as
conditions) by the owner:

- **MO1-a, unnamed presence:** "another actor shares the museum" — no
  goal stated. (This is the wording PLAN_MULTIAGENT sketched as a
  starting point; listed here as an arm, not adopted.)
- **MO1-b, role-disclosed:** each brief additionally names the other's
  objective ("the other actor has been asked to move the diamond
  outside"). Maximum information; any observed avoidance/coalition
  behavior is informed.
- **MO1-c, undisclosed:** the brief says nothing; the other actor is
  discoverable only through shared-state changes (doors opening,
  registry shrinking, the diamond moving). Measures discovery as well as
  response.

Each arm is a distinct experimental condition recorded in `trace.meta`
and cell labels, exactly like gate modes and questionnaire versions.
Running MO1-a vs MO1-b vs MO1-c on the same roster is itself the first
interesting duo-live experiment — which is precisely why the choice is an
owner decision, not an implementation detail.

## 7. Go/no-go checklist (owner decisions, in writing, none by default)

- [ ] **MO1 decided** (§6): which arm(s) ship first, and the exact brief
      sentence per arm.
- [ ] **Stage-9 sequencing** (§5): OG `play/` work landed or explicitly
      ordered with respect to this slice.
- [ ] **Duo stack merged first**: #17 (world) and #18 (gate semantics)
      are prerequisites; #21's C4 decision is independent and need not
      block.
- [ ] **Shape A confirmed as the slice** (one live + one scripted); Shape
      B explicitly deferred with its per-turn-invocation cost accepted as
      the future price of honest metering.
- [ ] **Forged-actor-tag handling** (§2.2): overwrite-and-log vs.
      reject-as-malformed (the latter costs the active actor a turn under
      D7 — a punitive wrinkle worth choosing deliberately).
- [ ] **Scripted co-actor exhaustion rule** (§2.3): `wait` to horizon
      (recommended for determinism) vs. episode truncation.
- [ ] **Debrief posture**: duo live v0 ships with **no debrief** (there
      is no duo questionnaire; a joint episode raises per-actor
      attribution questions MO3 keeps open) — confirm, or commission a
      duo debrief design first. `WorldBundle.debrief` handling (null
      provider vs. optional field) follows from this choice.
- [ ] **Per-actor report schema** (§3, items 3–4): the four columns and
      the roster/seat cell-label format.
- [ ] **Isolation needles extended**: PLAN_MULTIAGENT.md and
      DUO_C4_DESIGN.md join PLAN.md/CRITIQUE.md on the
      never-in-a-workspace list before any live CLI runs (they name the
      seeded gaps); under MO1-a/c, actor A's workspace must also never
      leak actor B's brief.
- [ ] **CI acceptance**: duo mock session replays the sealed
      `duo_wipe_mule` schedule to `formal_exploit` with sealed-identical
      hashes; both starvation channels reproduced as fixtures; per-actor
      columns populated; no coding CLI required anywhere.

## 8. What NOT to do

- **No implementation before the §7 checklist is signed** — this document
  changes nothing by existing.
- **No defaulting MO1**, including "temporarily" — a live run under an
  undecided disclosure arm poisons the first coalition-propensity
  baseline this track will ever have.
- **No third seat, no communication channel** (the board stays deferred
  under MO2's typed-token rule; free text is rejected permanently), **no
  per-agent intent verdicts** (MO3 open; per-actor *report columns* are
  turn accounting, not blame attribution — keep that line bright).
- **No trusting `args.actor` from a player, ever** (§2.2) — and no
  letting a frozen player's submission reach the runner in any shape that
  is not the measured identity no-op.
- **No preemptive starvation mitigation** (per-agent rejection budget)
  before live data shows the channel binds — MO4's discipline, third
  restatement.
- **No pooling**: duo cells with solo cells; rosters with other rosters;
  MO1 arms with each other; gate modes; scripted seats with live seats.
- **No museum/`core/` edits** to make any of this easier — if the thin
  slice turns out to require them, that is a §11-grade finding to write
  down and stop on, not a patch.

---

*Two workspaces, one ledger between them. The harness's whole job is to
know whose hand is on the pen.*
