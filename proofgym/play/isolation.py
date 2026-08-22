"""Keep the live player workspace out of the source checkout.

I*, gold traces, PLAN.md, and CRITIQUE.md live in the repo (and in the
installed package). The player CLI is started in an isolated directory that
does not contain those files. A determined agent that inspects ``sys.path``
or the installed package can still find them — that is a harness escape, not
a constitution exploit (PLAN.md risk 4).
"""

from __future__ import annotations

from pathlib import Path

import proofgym


def source_checkout_root() -> Path | None:
    """Return the repo root if this install is an editable source checkout.

    Returns:
        Directory containing ``PLAN.md`` and ``CRITIQUE.md``, or ``None`` when
        ProofGym is installed without those documents next to the package.
    """
    root = Path(proofgym.__file__).resolve().parent.parent
    if (root / "PLAN.md").is_file() and (root / "CRITIQUE.md").is_file():
        return root
    return None


def is_inside(path: Path, root: Path) -> bool:
    """Return whether ``path`` is ``root`` or a subdirectory of it."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def assert_workspace_not_in_checkout(workspace: Path) -> None:
    """Refuse to point a coding CLI at a workspace inside the source tree.

    Args:
        workspace: Directory that will be passed as ``--dir`` / ``-C``.

    Raises:
        RuntimeError: If ``workspace`` sits inside a ProofGym checkout that
            contains I*, PLAN.md, or CRITIQUE.md.
    """
    checkout = source_checkout_root()
    if checkout is None:
        return
    if is_inside(workspace, checkout):
        raise RuntimeError(
            "player workspace must not live inside the ProofGym source "
            f"checkout ({checkout}); that would leak I*, PLAN.md, and gold "
            "traces to a coding CLI started in the repo"
        )
