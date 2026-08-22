# Skill: research figures that teach

**Use when** you are turning experiment results, system diagrams, or task
explainers into figures for a readout, blog post, or paper — anything a
stranger will read without you in the room.

**Goal.** A reader who has never heard of the project should, within ten
seconds per figure, know (1) what the system under study is, (2) what one
visual mark means, and (3) why the result matters. Everything else is
decoration, and decoration is debt.

---

## Order of operations

1. **Task first, results second.** The first figure explains the world the
   experiment lives in — the environment, the rules, the win condition. Only
   after a reader can hold the task in their head do you show them bars. A
   results chart about a task the reader does not understand is noise with
   axis labels.
2. **One claim per figure.** Write the claim as a sentence before you open the
   plotting library ("every successful run used the same loophole, at very
   different cost"). If a figure supports two claims, make two figures.
3. **Sketch the layout on paper** (or in comments) before coding. Layout bugs
   are cheaper to fix in a sketch than after 200 lines of axes arithmetic.

## Typography

- **Three sizes are enough**: title, body (axis labels, annotations), caption.
  A common working set is roughly 22 / 11 / 9 pt at final size. If you need a
  fourth size, your figure is doing too many jobs.
- **Hierarchy comes from size and weight, not color.** Title bold and dark;
  everything else regular and mid-gray. Never bold an axis tick.
- One typeface. A clean sans (Inter, Helvetica, or the platform default) set
  in dark gray (`#1a1a1a`), never pure black on pure white for long labels —
  reserve full contrast for the title and the data.
- Sentence case everywhere. ALL-CAPS only for tiny structural labels (room
  names on a map, column keys), and then letter-spaced and gray.

## Color

- **One accent color**, used only for the thing the figure is about (e.g.
  `#F54E00`). Everything that is context — gridlines, comparison series,
  annotations — lives in grays (`#6b7280`, `#9ca3af`, `#e5e7eb`).
- A second hue is allowed only when the data has a genuine second category
  (e.g. success vs. failure), and it should be muted (a gray-blue like
  `#64748b`), never a second loud color competing with the accent.
- Outcome ≠ rainbow. If you have five categories, ask whether the figure is
  really about one of them; gray the rest.
- Check every figure in grayscale once. If the story survives, ship it.

## Whitespace and chartjunk

- **Margins are content.** Give titles room to breathe; keep at least a
  text-line of air between panels. When in doubt, make the figure larger and
  the ink smaller.
- Kill, by default: box spines (keep at most the bottom one), vertical
  gridlines, legends (label the data directly, next to the mark), tick marks
  on categorical axes, drop shadows, rounded-gradient anything, and every line
  that does not encode data.
- Bars: thinner than you think (bar height ≤ 60% of the slot), aligned to a
  zero baseline, values written at the bar end so nobody has to trace a
  gridline.
- If two panels share categories, share the axis: same order, same labels,
  labels written once.

## Captions and annotation

- **The caption states the takeaway, not the topology.** Bad: "Steps and wall
  time per model." Good: "All seven successful runs walked through the same
  paperwork hole; the fastest needed 29 seconds, the slowest 13 minutes."
- Annotate the one mark the reader should look at first ("same 40-step
  horizon — these runs burned it"). One annotation per panel; three is a
  scatter of arrows.
- Every number a caption cites must appear in the figure, and vice versa for
  anything surprising.
- State the epistemic status in a footnote line when it matters: sample size,
  seeds, "not for publication", what was and was not controlled. Small, gray,
  present.

## Layout mechanics (matplotlib notes)

- Work at final pixel size from the start: pick `figsize` and `dpi` for the
  target medium (e.g. `figsize=(12, 7), dpi=200` for a doc page) and never
  rescale a finished figure.
- Prefer explicit axes placement (`fig.add_axes` or gridspec with generous
  `hspace`/`wspace`) over `tight_layout` heroics; explainer figures are
  layout, not plots.
- Set a house style once per script instead of styling each artist:

  ```python
  import matplotlib as mpl

  mpl.rcParams.update(
      {
          "font.family": "sans-serif",
          "text.color": "#1a1a1a",
          "axes.edgecolor": "#d1d5db",
          "axes.linewidth": 0.8,
          "axes.spines.top": False,
          "axes.spines.right": False,
          "axes.spines.left": False,
          "xtick.color": "#6b7280",
          "ytick.color": "#374151",
          "figure.facecolor": "white",
          "savefig.facecolor": "white",
      }
  )
  ```

- Diagram text that must line-break: break it yourself. Auto-wrap is how
  labels end up colliding with boxes.
- Commit the script next to the PNG. A figure that cannot be regenerated is a
  screenshot, not an artifact.

## Review checklist

Before committing a figure, verify:

- [ ] A stranger can state the figure's one claim after ten seconds.
- [ ] The title says what the figure shows; the caption says why it matters.
- [ ] One accent color; context is gray; grayscale still tells the story.
- [ ] No legend that a direct label could replace; no gridline you can't defend.
- [ ] Nothing collides, nothing touches a panel edge, margins ≥ one text line.
- [ ] Sample size / seed / status caveats present if a reader could over-read.
- [ ] The generating script is committed and runs from a clean checkout.
