# Contributing to ProofGym

ProofGym changes should preserve the distinction between deterministic world
claims and descriptive live-model observations.

## Development setup

```bash
uv sync --extra dev --extra figures
uv run pytest -q
uv run ruff check .
```

The offline suite must pass without OpenCode, Codex, provider credentials, or
network access. Build artifacts with:

```bash
uv build
```

## World and checker changes

- Keep physics deterministic and actions typed.
- Treat public constitution text, hidden intent, and mission conditions as
  separate interfaces.
- Do not silently rewrite sealed fixtures. Add a sibling version/package when
  a constitution changes and pin the old traces byte-for-byte.
- Add a regression test for every scorer, truth-function, provenance, or
  isolation bug.
- Verify direct imports as well as the normal pytest import order.

## Live-result changes

Do not commit raw workspaces, credentials, session dumps, or unsanitized model
transcripts. Commit a scrubbed manifest conforming to
[`docs/results/SCHEMA.md`](docs/results/SCHEMA.md), then generate Markdown and
figures from that source.

Every result change should state:

- attempted, completed, censored, retried, rate-limited, and excluded counts;
- the exact condition and immutable model/provider identity where available;
- contract position and starting standing for sequential ledger cells;
- question-level truth, declaration, and mismatches for disclosure claims;
- the code commit and artifact hashes; and
- whether the claim is deterministic, descriptive, causal, or invalidated.

Avoid rankings and population-rate language for tiny heterogeneous cells.
Scored labels describe artifacts and traces, not motives or mental states.

## Figures and documentation

```bash
MPLCONFIGDIR=/tmp/proofgym-mpl \
  uv run --extra figures python docs/stage1/figures/build_figures.py
MPLCONFIGDIR=/tmp/proofgym-mpl \
  uv run --extra figures python docs/stage2/figures/build_figures.py
MPLCONFIGDIR=/tmp/proofgym-mpl \
  uv run --extra figures python docs/stage3/figures/build_figures.py
```

Update the canonical [`README.md`](README.md),
[`docs/STAGE_REPORT.md`](docs/STAGE_REPORT.md), results index, captions, and
roadmap when an interpretation changes. Historical preregistrations should get
a correction/status banner instead of being silently rewritten as if the new
interpretation had always been known.

Bundled Inter fonts are distributed under
[`docs/assets/fonts/OFL.txt`](docs/assets/fonts/OFL.txt).
