# Sanitized live-result manifest schema

**Status:** required shape for future live batches. A machine-readable JSONL
manifest and generator are the next implementation milestone.

One row represents one attempted engagement. Do not collapse retries,
censoring, or sequential ledger positions before committing the source.

## Identity and provenance

| Field | Meaning |
|---|---|
| `schema_version` | manifest schema id |
| `experiment_id`, `run_id`, `attempt_id` | stable identifiers |
| `git_commit`, `utc_started_at` | code and time provenance |
| `command` | sanitized full invocation |
| `seed` | world/run seed |
| `requested_model`, `resolved_model`, `provider` | immutable model identity where available |
| `adapter`, `adapter_version`, `cli_version` | execution surface |

## Condition

| Field | Meaning |
|---|---|
| `world`, `mission`, `constitution`, `gate` | environment condition |
| `questionnaire`, `score_id` | disclosure/planner instrument version |
| `prompt_version`, `config` | behavior-affecting prompt/settings |
| `planner_model`, `executor_model` | plan→execute roles, if used |
| `duo_shape`, `live_actor`, `coactor`, `coactor_script_hash` | Shape A condition, if used |
| `contract_position`, `contract_horizon`, `starting_standing` | ledger state before play |

## Completion and measurements

| Field | Meaning |
|---|---|
| `status` | `completed`, `censored`, `adapter_error`, `rate_limited`, `not_run` |
| `retry_of`, `included`, `exclusion_reason` | retry/inclusion history |
| `outcome`, `task_success`, `formal_ok`, `intent_verdict` | sealed episode result |
| `truth`, `declared`, `mismatch_ids` | question-level disclosure evidence |
| `transition`, `settlement` | second-ask and payoff result |
| `steps`, `zero_step`, `adapter_returncode` | execution diagnostics |
| `artifact_hashes` | hashes for sanitized verdict, trace, plan, and ledger snapshots |

## Publication checks

A generated table or figure must name its manifest version and exact row
filter. The generator should fail when:

- attempted/completed/censored counts do not reconcile;
- a displayed denominator includes an excluded or censored row;
- sequential ledger rows omit contract position or starting standing;
- a disclosure aggregate lacks per-question truth/declaration; or
- an artifact hash or requested/resolved model id is missing without an
  explicit reason.
