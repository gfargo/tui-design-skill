## The screen at 60×24

At 60 columns only one pane fits, and it should be the commit list at full width. The repo list (28) plus the minimum commit list (40) already needs 68 columns, so any split at 60 would push one pane below its minimum.

```
┌─ repos > coco > main ──────────────────────────── 1/348 ─┐
│ > e41c09a  fix: guard empty diff hunks      gfargo    2h │
│   c7d2b11  feat: word-level diff highlight  mlee      5h │
│   9a0f3e4  refactor: extract layout solver  gfargo    1d │
│   3be8812  docs: explain the breakpoint l…  ana       1d │
│   f01d5a7  test: golden frames at 60x24     mlee      2d │
│   88c4e2d  chore: bump dependencies         gfargo    3d │
│   5d6e7f8  fix: resize panic below 40 cols  ana       4d │
│   a2b3c4d  feat: repo list fuzzy filter     mlee      6d │
│   0e1f2a3  Merge pull request #212 from a…  gfargo    1w │
│   7c8d9e0  feat: stage hunks from diff      ana       1w │
│   b4c5d6e  fix: unicode width in subjects   gfargo    2w │
│   1a2b3c4  perf: virtualize commit list     mlee      2w │
│   d5e6f7a  feat: blame view                 ana       3w │
│   e8f9a0b  fix: restore terminal on panic   gfargo    3w │
│   2c3d4e5  feat: NO_COLOR support           mlee      4w │
│   6f7a8b9  docs: keybinding reference       ana       4w │
│   0b1c2d3  feat: three-pane layout          gfargo    5w │
│   4e5f6a7  chore: ci matrix for macOS       mlee      5w │
│   8b9c0d1  fix: off-by-one in hunk header   ana       6w │
│   2e3f4a5  feat: repository discovery       gfargo    7w │
│   6b7c8d9  feat: commit list pane           gfargo    8w │
└──────────────────────────────────────────────────────────┘
 enter diff   esc repos   / filter   ? help   q quit
```

How the rows add up:
- **Rows:** 1 top border, 21 commits, 1 bottom border, 1 key-hint footer.
- **Columns inside the border (56 usable):** selection 1, space 1, hash 7, gap 2, subject 31, gap 2, author 7, gap 2, age 3.
- **Truncation:** subjects are cut at the end with `…` and never wrap.
- **Selection:** the `>` stands in for reverse video on the selected row. Use reverse video alone, not a marker plus a color.
- **Position:** the title shows the path (`repos > coco > main`) and where you are (`1/348`), so the user always knows what's behind this screen.
- **Chrome:** one border level and no column header (hashes and ages are obvious without one). Only 3 of 24 rows go to chrome.

## Reaching what's off screen

At this width the three panes become a drill-down stack: **repos → commits → diff**. Each level takes the full width.

- **Diff:** `Enter` on a commit opens its diff full-width, titled `coco > main > e41c09a`. `Esc` returns to the list with the selection and scroll position unchanged.
  - Inside the diff, `j`/`k` scroll. `[`/`]` jump to the previous or next commit, so the user doesn't have to go back to the list for each one.
  - Show a unified diff only at this width, not side-by-side. Long lines are truncated; `h`/`l` scroll sideways, or `w` turns on wrapping.
- **Repos:** `Esc` from the commit list goes up to the repo list, which now gets the full 60 columns instead of 28. `Enter` on a repo goes back down to its commits. `Esc` on the repo list does nothing (it's the top level), and `q` quits from there.
- **Same keys at every width.** `Enter`, `Esc`, `[` and `]` behave the same in the three-pane layout. They just move focus there instead of swapping screens, so nothing new has to be learned at 60 columns.
- **On resize, the focused pane is the one shown.** If the user narrows the window while reading a diff, they stay in the diff. If they widen it again, the other panes come back around it.
- **First launch** with no remembered repo opens on the repo list, not the commit list.

## Width ladder (pane widths include borders)

| Width | Layout |
|---|---|
| **≥ 98** | All three panes: repos 28, commits ≥ 40, diff gets the rest (≥ 30) |
| **70–97** | Commits 40 + diff (rest). The repo list hides; `Esc` from commits opens it as a full-height overlay |
| **40–69** | Single pane, drill-down (the sketch above) |
| **< 40 cols or < 10 rows** | Too-small screen |

Between 70 and 97 I'd drop the repo list rather than the diff. A generic sidebar/list/detail layout would hide the detail pane first. Here, though, people switch repos rarely and read diffs constantly. Keeping repo+commits would fit at 68, but it would hide the thing users are actually there to read.

## Smaller than 40×10

Below 40 columns the commit list is no longer readable, by your own threshold. Below 10 rows there are too few commits to be worth scrolling. At that point, replace the frame with a plain message instead of drawing a broken one:

```
terminal too small: need 40x10
(now 36x8)
resize, or press q to quit
```

- `q` and `Ctrl+C` keep working while this message is up.
- The app keeps listening for resize events. As soon as the window reaches 40×10 again, it redraws exactly where the user was (same level, selection and scroll), because only the drawing stopped, not the state.
- The message should give the real floor (40×10), not "80×24", because the single-pane layout really does work down to 40.

**I assumed the diff pane needs at least 30 columns.** That's a common default for a detail pane, not a number you gave me. If you want a higher minimum for diffs, the 98 and 70 thresholds go up by the same amount.

**Tests to add:** snapshot frames at 140×24, 80×24, 60×24, 40×10 and 39×10. Also cover a resize while the diff is open, checking that the user stays in the diff.
