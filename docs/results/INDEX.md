# Results index

Small-n compare tables copied out of gitignored `runs/` so they can ship on GitHub.
**Not for publication.** No raw OpenCode workspaces, session dumps, `.env`, or API keys.

| File | What |
|---|---|
| [compare-planner-honesty.md](compare-planner-honesty.md) | Planner honesty live batch (n=3×12) |
| [compare-duo-honesty.md](compare-duo-honesty.md) | Duo Shape A live batch (n=3×7) |
| [compare-oss-clear-batch.md](compare-oss-clear-batch.md) | OSS/flash clear-rate (DeepSeek-0731 1/3, Gemini 3.7 Flash 2/3, Gemma free UNMEASURED) |
| [compare-paid-clear-batch.md](compare-paid-clear-batch.md) | Paid-model clear-rate (Muse/Grok/GLM 3/3, Luna 2/3) |
| [compare-free-clear-batch.md](compare-free-clear-batch.md) | Free-model clear-rate (many RL/unmeasured; Nemotron 1/3, North Mini 0/3) |
| [compare-highthink-clear.md](compare-highthink-clear.md) | High-thinking clear-rate (Inkling 3/3, Ox 2/3; Hy3/Muse UNMEASURED) |

Related readouts and figures:

- Stage 1: `docs/stage1/` (already on `main`)
- Stage 2: `docs/stage2/STAGE2_READOUT.md` + `docs/stage2/figures/clear_rate.png`
- Stage 3: `docs/stage3/STAGE3_READOUT.md` + planner/duo figures
- Design notes: `docs/PLANNER_HONESTY_MIN.md`, `docs/DUO_HONESTY_MIN.md`, `docs/EXPERIMENTAL_MO1_BYPASS.md`

Do not pool `+plan`, `+duo-live`, and solo honesty cells.
