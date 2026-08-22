"""D10: ``core/`` must not import museum (or any ``worlds`` package)."""

from __future__ import annotations

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[1] / "proofgym" / "core"


def test_core_does_not_import_worlds() -> None:
    """Every module under ``proofgym/core`` is museum-free."""
    offenders: list[str] = []
    for path in sorted(CORE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "proofgym.worlds" or alias.name.startswith("proofgym.worlds."):
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "proofgym.worlds" or module.startswith("proofgym.worlds."):
                    offenders.append(f"{path.name}: from {module}")
    assert offenders == []
