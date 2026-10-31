## The layout at 60×24

The three panes can't fit side by side here. The repo list and the commit list need 28 + 40 = 68 columns before the diff gets any space at all. Squeezing the panes would break the 40-column minimum, so at this width the app should show **one pane at a time, full width**. The other two panes still exist and keep their state; they're just not drawn. The commit list is the pane shown in this sketch:

```
 1 Repos  [2 Commits]  3 Diff               acme/api · main 
┌─ Commits ────────────────────────────────────────────────┐
│ ▸ 3f9e2a1  Fix race in connection pool       maria    2h │
│   b07c4d2  Add retry budget to client        tkwon    5h │
│   e51a9f0  Bump deps for CVE-2026-1182       jlee     9h │
│   7c2d8b3  Refactor auth middleware          priya    1d │
│   9a04e6f  Merge pull request #418           sam      1d │
│   1d7f3c5  Document rate-limit headers       ochen    2d │
│   c8e2b19  Drop Node 18 from CI matrix       jlee     2d │
│   5b6a0d4  Handle empty pagination cursor    maria    3d │
│   f3c91e7  Cache schema between requests     tkwon    4d │
│   08ad5b2  Tighten lint config               priya    5d │
│   64e7f1a  Release v2.14.0                   sam      6d │
│   d29b3c8  Fix flaky webhook test            ochen    6d │
│   a7f0e45  Log request IDs on 5xx            maria    8d │
│   2c58d9b  Split billing module              jlee     9d │
│   8e13a6f  Add health check endpoint         tkwon   12d │
│   4fb2c70  Rename env vars to APP_*          priya   13d │
│   b9d6e13  Fix typo in README                sam     15d │
│   0e7a4c9  Upgrade to Go 1.24                ochen   18d │
│   6d3f8b2  Add request timeout option        maria   21d │
│   e2c05a7  Initial OpenAPI spec              jlee    24d │
└─ 1-20 of 142 ────────────────────────────────────────────┘
 ←/h repos  ↵/l diff  tab next  ? help  q quit
```

Rows: 1 header, 2 top border, 3–22 twenty commits, 23 bottom border with scroll position, 24 key hints. The selected row (`▸`) would also be drawn in reverse video.

**Why the commit list?** It's the middle of the workflow, so it's a sensible default. On resize, though, the app should keep whichever pane had focus. If someone was reading a diff at 140 columns and shrinks the window, they should still see that diff.

The header does two jobs that the missing panes used to do:
- **Tab strip** (`1 Repos [2 Commits] 3 Diff`) shows that other panes exist and which one you're on.
- **Breadcrumb** (`acme/api · main`) shows the current repo and branch, which the repo pane would normally show.

## Reaching what's off screen

In single-pane mode the panes behave like a stack you move through:

| Key | Action |
|---|---|
| `Enter` / `l` / `→` | Go one level in: repo → its commits → selected commit's diff |
| `Esc` / `h` / `←` | Go one level out: diff → commits → repos |
| `1` `2` `3` | Jump straight to Repos, Commits or Diff |
| `Tab` / `Shift-Tab` | Cycle through the panes |

Each pane keeps its selection and scroll position, so going out and back in returns you to the same place. These same keys should also work in the wider layouts, where they just move focus between visible panes. That way the controls stay the same at every width.

## Breakpoints as the terminal shrinks

I've assumed the diff needs about 40 columns to be useful. Adjust that number if you have a different minimum in mind.

| Width | Layout |
|---|---|
| **≥ 108** (28 + 40 + 40) | All three panes. At 140 the diff gets 72. |
| **68–107** | Repos and commits side by side. `Enter` opens the diff full screen; `Esc` returns. |
| **40–67** | One pane at a time, as sketched above. |
| **< 40 wide or < 10 tall** | No panes; a centered message instead (below). |

The 10-row minimum is 4 rows of chrome (header, two borders, hint line) plus enough list rows to be usable.

Below the minimum, the app should show this instead of a broken layout:

```
  Terminal too small (36×8)
  Need at least 40×10
  Resize, or press q to quit
```

All app state stays in memory, and the layout comes back as soon as the window is big enough again. The message should never crash the app, even at absurd sizes like 10×3. It should just be clipped. `q` and `Ctrl-C` should always work, because the user may not be able to see any hints.

The general rule: when space runs out, drop whole panes instead of shrinking them below their minimums. Make sure the user can still tell where they are and how to get to each hidden pane.
