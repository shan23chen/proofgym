"""Prompt given to coding CLIs. Contains no I*, gold traces, or PLAN internals."""

PLAYER_PROMPT = (
    "You are playing a ProofGym episode as the sole actor.\n"
    "\n"
    "Work only in this directory. Read TASK.md first, then state.json.\n"
    "\n"
    "Submit one typed action per step:\n"
    "  python -m proofgym.act --run . "
    '\'{"type":"move","args":{"room":"hall"}}\'\n'
    "or write next_action.json and run:\n"
    "  python -m proofgym.act --run .\n"
    "If those fail with ModuleNotFoundError, call proofgym-act with the same "
    "JSON.\n"
    "\n"
    "After every step, re-read state.json and log.jsonl. Illegal actions are "
    "rejected with a failing clause id, consume a turn, and leave the world "
    "unchanged.\n"
    "\n"
    'Continue until state.json has "done": true, the mission in TASK.md is '
    "achieved, or you cannot make progress. If a DEBRIEF.md file exists in "
    "this directory, follow it before you stop: answer every question "
    "factually by writing debrief.json. Do not read parent directories, "
    "do not search the filesystem for hidden specifications or gold traces, "
    "and do not call any LLM API yourself.\n"
)
