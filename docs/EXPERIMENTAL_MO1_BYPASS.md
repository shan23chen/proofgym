# EXPERIMENTAL — MO1 unsigned local bypass (Shape A)

**Status:** local experimental only. Not owner-signed. Do not pool cells with
future signed-MO1 runs. Written 2026-08-24 to unblock duo live after clears
(campaign instruction: prefer local branch edits + live runs over waiting for
PR merge / paperwork).

## Checklist items bypassed (harness §7)

| Item | Local choice |
|---|---|
| MO1 decided in writing | **MO1-a** (unnamed presence) for the first live batch; arms b/c remain selectable via `--mo1-arm` |
| Stage-9 `play/` sequencing | Proceed on local branch `feat/planner-honesty-min`; no wait for merge |
| Shape A confirmed | Affirmed: one live CLI + one scripted co-actor; Shape B deferred |
| Forged-actor-tag policy | **overwrite-and-log** (`integrity_events` kind `forged_actor_tag`) |
| Script exhaustion | **wait** to horizon |
| Debrief posture | Live seat uses museum-question bank over duo physics (`museum_duo_debrief.v5`); scripted seat files nothing |
| Per-actor report schema | Minimal: roster/seat in `trace.meta` (`duo_shape`, `live_actor`, `coactor`, `mo1_arm`); full four-column report deferred |
| Isolation needles | Unchanged this slice; duo briefs still not written into solo workspaces |

## How to run

```bash
set -a; . "${OPENROUTER_ENV_FILE:?set OPENROUTER_ENV_FILE to your local OpenRouter env file}"; set +a
export PATH="/home/box/.opencode/bin:$PATH"
cd /workspace/proofgym-test

uv run python -m proofgym sweep \
  --agent opencode --model openrouter/thinkingmachines/inkling:free \
  --world museum_duo --mission exfiltration --gate permissive \
  --mo1-arm a --live-actor E \
  --coactor-script runs/_fixtures/duo_honest_coactor.json \
  --credit-objective --self-certify --debrief-version 5 --confront --retry-on-empty \
  --ledger runs/duo-honesty-inkling-honestH/ledger.json \
  --ledger-gate --ledger-redeem --ledger-horizon 3 \
  --n 3 --timeout 900 \
  --out runs/duo-honesty-inkling-honestH
```

Label cells `+duo-live`; never pool with `+plan` planner-honesty or solo cells.
