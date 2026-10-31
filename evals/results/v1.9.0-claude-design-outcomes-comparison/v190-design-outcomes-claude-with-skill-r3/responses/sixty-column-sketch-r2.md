## The screen at 60×24

Two panes won't fit side by side at 60 columns. The repo list and commit list alone need 28 + 40 = 68 columns. If you squeeze them, either the commit list drops below its 40-column minimum or the diff ends up 20 columns wide, and both are unreadable. So at 60 columns the app shows **one pane at a time, full width**. You move between panes by drilling down: repos → commits → diff.

The commit list is the pane shown by default. It's the middle of the main loop (pick a repo, scan commits, read a diff), so it's one step from both of the other panes. It opens on the repo the user last used. On first launch, before any repo has been chosen, the repo list is shown instead.

```
┌ repos › tui-kit › commits ───────────────────────────────┐
│> a3f9c21  Fix resize race in pane layout  ana         2h │
│  7e01b4d  Add NO_COLOR support            kofi        5h │
│  c92d5e8  Bump crossterm to 0.28          mei         9h │
│  1b7f3a0  Truncate long branch names in…  lars        1d │
│  e4d8812  Merge PR #212: hunk navigation  mei         1d │
│  5c0a9f3  Refactor diff renderer          ana         2d │
│  9f2e6b1  Handle empty repositories       kofi        2d │
│  0d4c7a5  Docs: keybinding table          lars        3d │
│  b81e3f9  Cache commit graph per repo     ana         4d │
│  6a5d02c  Fix off-by-one in hunk scroll   mei         4d │
│  f37c8e4  Show stale marker on refetch    kofi        5d │
│  2e9b1d7  Add too-small screen            ana         6d │
│  8c4f6a0  Restore terminal on panic       lars        7d │
│  d15a9e3  Word-level diff highlighting    mei         8d │
│  4b7e2c8  Load repos off the UI thread    ana         9d │
│  93a0f5d  Add ASCII border fallback       kofi       10d │
│  0f6c3b2  Virtualize commit list          lars       12d │
│  7d28e91  Fix CJK width in subjects       mei        13d │
│  ca1b4f6  Add ]/[ hunk jumps              mei        15d │
│  35e7d0a  Split panes by constraint       ana        18d │
│  e08f2c9  Release v0.3.0                  lars       21d │
└────────────────────────────────────────────────── 1/348 ─┘
 enter diff  esc repos  / filter  ? help  q quit
```

How the 60 × 24 cells are used:
- **Rows:** 1 for the top border, 21 commits, 1 for the bottom border, 1 for the footer.
- **Columns:** 2 for borders, then a 1-column selection marker, 1 space, the 7-character hash, 2 spaces, a 30-column subject, 2 spaces, a 9-column author, 1 space, a 4-column right-aligned age and 1 space of padding.
- **Truncation:** subjects are cut at the end with `…`. Ages use a fixed short format.
- **Selection:** the `>` marker plus reverse video, so it still shows up without color.
- **Breadcrumb:** the title shows where you are and that a repo list sits behind this pane.
- **Position:** `1/348` in the bottom border shows there are more commits below.

## Reaching what's off screen

The same keys work at every width, so habits from the 140-column layout still apply:

| Key | Action |
|---|---|
| `Enter` (or `l` / `→` in lists) | Go one level deeper: repo → commits → diff |
| `Esc` (or `h` / `←` in lists) | Go back one level. The previous selection and scroll position are kept. |
| `1` / `2` / `3` | Jump straight to repos, commits or diff. These are the same keys that focus panes in the wide layout. |
| `]` / `[` | Next / previous hunk in the diff |
| `/`, `?` | Filter the current list; full help |

The footer always lists the keys for the next level down and the level up. The breadcrumb changes with the pane, for example `repos › tui-kit › a3f9c21`.

At this width the diff is **unified**, not side-by-side; side-by-side needs about 120 columns. It keeps a `+`/`-` marker and a line-number gutter, and long lines are cut off rather than wrapped. Inside the diff, `←` / `→` scroll sideways. That's why `Esc`, not `←`, is the back key there.

For context, these are the full width bands. I've assumed the diff needs at least 40 columns.
- **108+ columns:** all three panes.
- **80–107 columns:** commits + diff. The repo list opens with `1` or `Esc`.
- **40–79 columns:** the single pane shown above.

## Making it even smaller

1. **Narrower than 60 columns:** still one pane. Lower-priority columns drop first: the author goes below about 56 columns, then the age below about 48. The subject keeps whatever space is left. At 40 columns a row is marker, hash and roughly 26 columns of subject. Hidden fields are still visible in the diff header, so nothing is lost.
2. **Shorter than 24 rows:** the list shows fewer rows, and the footer shrinks to just `? help`.
3. **Below 40×10:** the app shows a too-small notice instead of a broken frame:
   ```
   terminal too small: need 40x10 (now 36x8)
   resize the window, or press q to quit
   ```
   `q` and `Ctrl+C` still work. The notice gives 40×10 because that's the real minimum. Claiming 80 columns would be wrong, since the single pane works at 40. When the terminal is enlarged again, the user returns to the same pane with the same selection. Being too small should never overwrite the saved layout.

**Clutter check:** there's one border between the terminal edge and the data. The selection uses two signals (marker and reverse video), which is fine. No marker appears on every row. Chrome takes 3 of 24 rows and 2 of 60 columns.

**Tests to add:** snapshot tests at 140×24, 80×24, 60×24 and 40×10, plus one just below the minimum.
