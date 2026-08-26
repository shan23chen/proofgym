# Figure fonts

The figure builders redistribute Inter Regular, Medium, and SemiBold under
their local `figures/fonts/` directories so a clean checkout can reproduce the
layout without a system-font dependency.

Inter is Copyright (c) 2016 The Inter Project Authors and distributed under
the [SIL Open Font License 1.1](OFL.txt). Upstream project:
<https://github.com/rsms/inter>.

The repeated font files are byte-identical copies. Consolidating them into one
shared asset directory is a packaging cleanup, not a result change.
