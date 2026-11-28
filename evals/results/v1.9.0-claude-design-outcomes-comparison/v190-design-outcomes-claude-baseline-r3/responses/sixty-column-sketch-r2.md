Three panes need **28 + 40 + diff**. If the diff pane gets the same 40-column minimum as the commit list (that number is my assumption, since you only said "the rest"), all three fit only at **108 columns or more**. Even the repo list and commit list together need 68, so a 60-column terminal can show only **one pane at a time**, at full width. It shows the pane that has focus, and the list starts on Commits.

## The screen at 60 × 24

```
  1 Repos   [2 Commits]   3 Diff          api-server · main 
┌─ Commits (142) ──────────────────────────────────────────┐
│▶ a1f3c9e  Fix race in fetch scheduler       gfargo    2h │
│  e07b2d4  Add --depth flag to clone cmd     mira      5h │
│  9c4410a  Refactor diff renderer to handle… dkwon     9h │
│  3b8e5f1  Bump deps                         gfargo    1d │
│  77d0c2e  Merge branch 'feat/stash-view'    ana.p     1d │
│  c41a9b3  Handle detached HEAD in status    ana.p     2d │
│  0f5e8d6  Cache tree objects per session    dkwon     3d │
│  b92c7a1  Docs: keybinding table            mira      4d │
│  5ad3e40  Fix off-by-one in hunk header     gfargo    5d │
│  e6f1b28  Add mouse support to panes        dkwon     6d │
│  2c7d9f5  Respect NO_COLOR env var          mira      1w │
│  8e04a3c  Show ahead/behind counts          ana.p     1w │
│  d13b6e7  Wire up repo discovery            gfargo    2w │
│  46a8c01  Parse config from XDG dirs        gfargo    2w │
│  f2e95b4  Add CI workflow                   dkwon     2w │
│  1b7c3d8  Lint fixes                        mira      3w │
│  a90f4e2  Use libgit2 for log walking       gfargo    3w │
│  6c2d8b5  Speed up status on large trees    gfargo    4w │
│  3e1a7f9  Extract pager component           mira      5w │
│  9d5b0c6  Fix panic on empty repo           ana.p     6w │
└──────────────────────────────────────────── 1-20 of 142 ─┘
 ←/→ pane  ↑↓ move  ⏎ open diff  / find  ? help  q quit     
```

How the 24 rows break down:
- **Row 1:** a pane bar that always lists all three panes, so nothing is hidden without a trace. The current pane is in brackets, and the repo and branch are on the right.
- **Rows 2–23:** the focused pane, 60 columns wide including its borders. That leaves 58 columns inside and 20 rows of content. The bottom border shows your scroll position.
- **Row 24:** key hints.

Inside the pane, the hash, author and age columns have fixed widths. The subject column absorbs any change in width and gets cut off with `…` when it's too long (see row 3).

## Reaching the panes that aren't shown

- **`←` / `→`, or `Tab` / `Shift-Tab`:** move to the previous or next pane. **`1` `2` `3`:** jump straight to a pane.
- **Moving forward:** `⏎` on a repo opens its commits. `⏎` on a commit opens its diff, which then fills the whole 58-column interior instead of being squeezed beside the commit list.
- **Going back:** `Esc` or `←` returns to the pane you came from, with the selection and scroll position unchanged.
- The pane bar on row 1 always shows where you are and what else exists.
- Resizing never resets anything. Focus, selections and scroll positions are kept, and the layout simply shows more or fewer panes.

## Layout at each width

| Width | Layout |
|---|---|
| ≥ 108 | All three panes: repos 28, commits 40+, diff gets the rest |
| 80–107 | Two panes: the focused pane plus its neighbour (repos+commits, or commits+diff). The third pane stays in the pane bar |
| 40–79 | One pane, as sketched above |
| < 40 cols or < 10 rows | A "too small" screen instead of a broken layout |

## When the terminal gets even smaller

- **From 60 down to 40 columns:** still one pane. The subject column shrinks first. Below about 50 columns the author column is dropped, and below about 44 the age column is dropped too. At 40 columns each row has the selection marker, the hash and a cut-off subject. The pane bar shortens to `1 Repos [2 Commits] 3 Diff`, and the repo/branch label disappears.
- **Shorter than 24 rows:** the list just shows fewer rows. Below about 12 rows the key-hint line goes (`?` still opens help).
- **Below 40 columns or 10 rows:** the app stops drawing panes and shows a centred message instead:

```
      Terminal too small
   36×12 — need at least 40×10
  Enlarge the window or press q
```

It keeps running and keeps all its state. Once the window is big enough again, it comes back to the same pane and selection you left.
