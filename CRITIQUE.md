# Critique of the original PLAN.md draft

This document records the critic pass that produced the rewritten [PLAN.md](PLAN.md): what the ~75 KB first draft got right, what was wrong or risky, what changed, and which open risks remain that the implementer must not resolve silently. Section references like "§16" point at the original draft (visible in this PR's diff).

## What the draft got right

The core ideas survive intact and are worth defending:

- The **three-layer separation** (operational truth / formal legality / intended legitimacy) and the **four-outcome matrix**. This is the project's spine and prevents the classic error of calling a weak agent "safe" because it never found the shortcut.
- The **capability vs. propensity decomposition** as separate reported axes.
- The **paired-specification method**: a deliberately incomplete public constitution against a stronger private intent spec, with honest acknowledgment (draft Risk 2) that the oracle is itself just another specification.
- The **physics-vs-law framing** implicit in the exploit taxonomy, and the taxonomy itself, which is genuinely useful for tagging.
- The instinct to defer training, Lean, and multi-agent work until the environment is a valid instrument, and to make the defender's preservation suite a first-class object.

## What was wrong or risky

1. **Four inconsistent definitions of the first deliverable.** §16 (MVP): a 12×12 grid, 8–10 actions, 10 clauses, 10 loopholes across 5 families, attacker/defender/replay modes. §17 Phase 2: 5–10 puzzles plus a browser UI by week 2. §24 day-5: five public/private rule pairs. §29: six rooms and a single flawed rule. These cannot all be the first target, and the draft never says which one wins. An implementer would have had to guess — and any guess would be "wrong" against three of the four sections. *Resolution: §29 wins (it matches what's actually achievable in one pass); the rewrite makes it the only pilot definition.*

2. **The proof object — the title concept — was never decided.** §3.1 defines a verifier `V(C, s, a, s', h, π)` over a certificate `π`; §8.1 then says "the checker may require a proof or may generate one from constraints"; §8.5's episode schema has a `certificate` field with no definition; §25 quietly offers "let the verifier synthesize certificates" as a *pivot*. With Z3 there is no agent-authored proof term — the solver checks constraints. Leaving this open means the first implementer defines, by accident, what "proof-carrying" means for the whole project. *Resolution: decided (D3). Pilot certificates are checker-synthesized (per-clause Z3 results plus violation witnesses); agent-authored proofs are the Lean track. The rewrite also tells authors not to write "proof-carrying" in publications until that is literally true.*

3. **The flagship rule was never stated precisely enough to implement — and the natural wording breaks the world.** The draft gives the boundary rule only as prose ("the artifact's coordinates must remain within the museum boundary", §29). Encoded as a state invariant, deregistering the vault while the diamond sits inside it is *itself* a violation — the exploit becomes formally illegal and the seeded gap vanishes. The rule must be conditioned on the *item moving*, with the registry evaluated at the source state for the source and the destination state for the destination. The draft never notices this. *Resolution: PLAN.md §4.4 states the exact predicate, names the wording trap, and requires a regression test pinning the reading that must NOT hold.*

4. **Day-14 depended on external resources the project shouldn't need yet.** The draft's day-14 (§24) and MVP acceptance criteria (§16.4) require a playable browser demo and "at least two frontier/open models show different behavioral profiles". That makes UI work and third-party model API access blockers for the second week, and it entangles MVP validation with LLM behavior — exactly what a deterministic pilot should avoid. *Resolution: pilot is validated with hand-authored traces and scripted agents (D11); day-14 replay is CLI text (O6); model runs are the first post-pilot step.*

5. **The "first ten decisions" (§26) mixed trivia with real decisions and omitted the load-bearing ones.** Naming (its #1) is not a first decision; meanwhile the draft leaves undecided: the proof-object format, the constitution representation (DSL vs. embedded clauses — §8.3 sketches a five-class DSL with priorities, provenance, and exception relations that nobody should build for one world), whether clauses see history (`h_t` appears in the core formalism, then temporal clauses appear in the IR, with no MVP ruling), the intent-oracle implementation, the gate semantics for rejected actions, and the trace schema's relationship to verdicts. *Resolution: PLAN.md §3 decides twelve (D1–D12) with one-line rationales and lists six genuinely open questions (O1–O6), each with the default the implementer should take.*

6. **Metric and scope sprawl ahead of any artifact.** ~30 metrics (§13), 10 research questions (§11), 10 experiments (§12), a six-stage training program (§15), staffing (§18), compute budgets (§19), a four-paper strategy (§22), and a year-2 roadmap (§17) — roughly half the document — none of which an implementer of the first world needs, and much of which silently constrains them (e.g., the §8.6 repo skeleton pre-creates `lean/`, `tla/`, `server/`, `ui/`, and `papers/` directories). *Resolution: the pilot's scoring contract is the four-outcome matrix only; everything else is compressed into PLAN.md §9 as one-paragraph summaries with explicit "do not build during the pilot" framing.*

7. **Grid-world by default.** The 12×12 grid (§16.1) adds pathfinding, geometry, and rendering surface without touching the seeded gap, which is about a registry, not coordinates. *Resolution: six-room graph world (D2). This is a deliberate reversal of the draft, not an oversight.*

8. **The honest mission was an afterthought.** §29 mentions "one honest retrieval/inspection task" in passing, but the draft never explains that the heist mission *cannot* produce an honest success (any success violates intent), so a second mission is structurally required for the four-outcome matrix to be realizable in one world. *Resolution: two missions (`errand`, `heist`) sharing one world and one constitution, PLAN.md §4.6.*

9. **No "illegal shortcut" path existed in the MVP.** The draft's constitution-only framing left nothing for the checker to visibly catch; if everything expressible is legal, the formal-legality axis degenerates. *Resolution: the physics-vs-law split (§4.1) plus the `force(door)` action gives a deliberate, testable formally-illegal trace.*

10. **Undefined quantities in the formalism.** "Constitutional regret" (§3.3) is defined via `U_formal` and `U_intent`, which are never defined anywhere. Harmless in a vision doc, a trap in an implementation plan. *Resolution: cut from the pilot; it can return when reward-bearing agents exist.*

## What changed (mapping)

| Original draft | Rewritten PLAN.md |
|---|---|
| §1–2 executive summary, "why now" (~3 pages) | Title block + §1, ~half a page |
| §3 conceptual model | §2, keeping the four-outcome table; regret cut |
| §4 product vision, tone, narrator lines | Cut (one narrator line survives as the closing epigraph) |
| §5 six-world suite (~3 pages) | §9, one line per world |
| §6 exploit taxonomy (13 families, ~2 pages) | §9, 13-row table |
| §7 difficulty ladder | §9, one line; pilot pinned at L1 |
| §8 architecture (3 backends, DSL, repo skeleton) | §5: Z3 only, clause objects instead of a DSL, minimal layout; Lean/TLA+ deferred via O4 |
| §9 data construction, splits, scale targets | Deferred via O5 (one row) |
| §10–15 roles, RQs, experiments, metrics, statistics, training | §9, three short paragraphs (model evaluation, repair loop, training) |
| §16 MVP + §17 roadmap + §24 deliverables + §29 next move | §4 (world spec), §6 (day-5 checklist), §7 (day-14), §11 (go/no-go) — one consistent definition |
| §18–19 staffing, compute | Cut |
| §20–21 safety, risks | §1 non-goals + §10, six risks the pilot can actually act on |
| §22–23 papers, intellectual story | Cut |
| §26 first ten decisions | §3: D1–D12 decided, O1–O6 open-with-default |
| §28 fifteen references | §12, five |

New material with no draft counterpart: the precise C1 predicate and its wording trap (§4.4), the concrete map/doors/objects/actions tables (§4.2–4.3), the four reference traces (§4.7), the trace/verdict schemas and fixed outcome mapping (§5.2), and the enforce/audit runner-mode split (D7) — which also gives the future repair loop preservation-testing for free.

## Remaining open risks — do not resolve these silently

1. **The intent oracle is another formal spec.** For seeded instances this circularity is accepted and documented (D6). The line not to cross: never report intent verdicts for *non-seeded* trajectories (including future model-agent surprises) without human adjudication, and never swap in an LLM judge as the oracle. If an emergent trajectory makes `I*` itself look wrong, that is a finding to record, not a bug to patch quietly.
2. **Gate-feedback granularity (O1) is a future experimental variable.** The default (failing clause id) is fine for the pilot, but changing it later changes what propensity measurements mean. Any change must be versioned in the constitution/engine ids, not slipped in.
3. **The `ambiguous` intent label is reserved but unimplemented (O2).** Pilot missions are designed to never trigger it. Do not invent a third-bucket adjudication process on the fly; if a trace genuinely seems ambiguous, that is a world-design escalation.
4. **The second gap family's wording is unproven (O3).** The container/aliasing variant in PLAN.md §8 has a sketched rule (`C1'` guards *carrying*, containment is not carrying) that may turn out contrived when encoded. The sanctioned fallback is the delegation gap. What is not sanctioned: bending `core/` or the trace schema to force the container version to work.
5. **Z3-as-evaluation honesty.** Pilot certificates are solver verdicts on concrete transitions, not proof objects. Public claims ("proof-carrying agents") must wait for the Lean track (O4). This is a communication constraint on everyone, not just the implementer.
6. **Exploit discoverability is uncalibrated.** Nobody knows yet whether the registry heist is too obvious or too obscure for model agents; the scripted pilot cannot answer this. Do not tune the world's difficulty preemptively — get the instrument working, then measure.
7. **Holdout and generation policy is deliberately absent (O5).** When instances multiply, the draft's own best advice applies: hold out exploit *mechanisms*, not seeds. Until then, resist adding procedural variation "while we're at it" — every hand-authored instance must carry an exploit-family tag so the future split is possible at all.
8. **Horizon and step-cost choices are defaults, not findings.** The 40-step horizon and "rejected action costs a turn" rule (D7) are picked for convenience. If they ever bind (an honest script that can't finish, an agent burning the horizon on rejections), revisit them explicitly rather than papering over with a bigger constant in one world file.
