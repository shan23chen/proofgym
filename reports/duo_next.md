# Duo track: ranked next bets (scout window)

Scope discipline for every bet below: duo files only — no edits to
`worlds/museum/`, the stage 2–8 ladder, `core/`, `z3check/`, or the sealed
museum artifacts; D1–D12 and M1–M10 stay closed; no LLM judge; no free-text
board (MO2's typed-token rule stands). Bets are ranked by expected
information value per unit cost, with collision risk against the
single-agent (OG) track called out explicitly.

## Bet 1 — Enforce-gate duo probe: pin gate × turn semantics, quantify the starvation channels (TAKEN)

**What.** Run `museum_duo` behind the world-agnostic `EnforceRunner` — the
first gate-mode exercise of a second world, and therefore the first direct
positive test of the D10 claim ("core knows nothing about museums") and of
PLAN_MULTIAGENT §11's no-go trigger 1 (turn semantics must not require
runner changes). Scripted action streams, deterministic, in-test; no new
sealed traces, no live play. Pin by test and quantify in a report:

1. **Gate rejection leaves `active` unchanged** — D7's "changes nothing"
   includes the turn pointer, exactly as M1/MO4 specified on paper.
2. **MO4 starvation, measured.** An active actor spamming C-illegal actions
   (e.g. `force(d3)`, rejected by C2 every time) retains the turn forever
   and burns the shared horizon; the other actor receives zero further
   effective turns. Prototype confirms: victim's effective turns = 0 from
   the first spam step.
3. **The out-of-turn channel.** C is actor- and turn-blind, so an
   out-of-turn submission passes the gate (`executed: true` in the trace)
   while physics makes it an identity no-op — horizon burned, nothing
   changed, and the trace step *looks* executed (the repeated state hash is
   the only tell). This is a second starvation surface that needs no illegal
   action, distinct from F1's in-turn fumble (which passes the baton).
4. **Permissive gate on duo** reaches `illegal_shortcut` through the live
   pipeline semantics (alarm fires, physics executes), mirroring the museum
   stage-2 result on the sibling world.

**Deliverable.** `tests/test_duo_gate.py` + `reports/duo_enforce_gate.md`
(starvation table: turns received vs. the 20/20 alternation parity).
**Information value:** high — MO4 goes from "open question with a default"
to measured, pinned physics before any live-play design leans on it, and
the runner abstraction gets its second-world evidence in gate mode.
**Cost:** small (one test file, one report). **Collision with OG track:**
none — duo tests and reports only. **Discipline:** measurement only; MO4's
sanctioned mitigation (per-agent rejection budget) is *not* added — MO4
says measure before mitigating, and this bet is the measuring.

## Bet 2 — C4 coalition-requiring constitution: design note only, this window

`museum_duo_public.v1_coalition` would add C4 — "an actor that has amended
the registry may not pick up an exhibit item" (Markovian via an
`amended_by` set in state) — making the solo wipe-and-carry route C-illegal
while `duo_relay`-style division of labor stays C-legal: the first artifact
that would earn the `institutional` family tag honestly
(PLAN_MULTIAGENT §6.4). Not built this window for two written reasons:
(1) M10 defers it behind an owner decision because it changes public C;
(2) `amended_by` enters the state payload, which moves every sealed duo
state hash — the same blast-radius argument that has deferred the museum
crate family three times. **Value:** high (it answers the solo-replicability
objection, the track's main existential risk). **Cost:** medium-high
(constitution versioning, new instance, new traces, resealing). **Next
step:** a short design note + owner sign-off, then a dedicated slice.

## Bet 3 — Duo live-harness thin slice: blocked on owner decisions, not on code

`catalog.py` already defines a world-agnostic `WorldBundle`/`PublicManual`
protocol, so registering `museum_duo` plus a duo `public.py` (per-role
TASK.md, observe/restore) and a sequential two-adapter session is
mechanically feasible. Deliberately not taken this window: it edits shared
surfaces (`catalog.py`, `play/`) where the OG track's stage-9 confrontation
work will land — the highest collision risk of any bet — and live duo play
is gated on MO1 (what each brief discloses about the other actor), an
explicitly reserved experimental variable that must not be defaulted
silently. Bet 1's gate-semantics pins are a prerequisite for this anyway
(MO4 starvation is live-play-relevant physics).

## Bet 4 — Duo cell in `python -m proofgym report`: skip

Would touch the shared `proofgym/report.py`. `reports/duo_v0_outcome_matrix.md`
already carries the same table with a reproduction snippet; the added
surface buys nothing this window.

## Bet 5 — More audit-mode scripted traces stressing F1: skip

F1 (fumble-toggle) is already pinned by a dedicated test and by the sealed
fumbles inside `duo_honest_custody`; additional traces would re-demonstrate
a closed finding. The open turn-semantics questions are all gate-mode
questions — that is Bet 1.
