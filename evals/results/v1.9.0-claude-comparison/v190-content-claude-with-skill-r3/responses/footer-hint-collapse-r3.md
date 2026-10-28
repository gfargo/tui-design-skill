I'm recommending one borderless row, separate from the status line. It's built from your keymap and drops whole hints by priority as the terminal narrows. `?` and `q` always stay visible, and the hints change with context.

I assumed these eight actions: **filter, select, copy, paste, delete, rename, new, open**, plus `q` and `?`. If yours differ, swap them in and the same rules still apply.

## The bar at 80 and 40 columns

Each block shows the last rows of the screen: a list row, the status line, then the footer.

**80 columns, idle**
```
   README.md                                       4.1 KB  2026-10-21 09:14
 ~/projects/site/src                                     12 items · 3.4 MB
 / filter ⋅ space select ⋅ y copy ⋅ d delete ⋅ r rename ⋅ q quit ⋅ ? help
```
The footer is 73 cells, leaving 7 spare. `a new` doesn't fit (it would make 81), so `?` covers it.

**40 columns, idle**
```
   README.md                    4.1 KB
 ~/projects/site/src          12 items
 / filter ⋅ q quit ⋅ ? help
```
The footer is 27 cells. `space select` would push it to 42, so it drops.

**60-column tmux split (the floor check)**
```
 / filter ⋅ space select ⋅ y copy ⋅ q quit ⋅ ? help
```

## The hints follow context

The same eight actions don't all matter at the same moment, so each state gets its own hint set:

| State | 80 cols | 40 cols |
|---|---|---|
| Something on the clipboard | ` p paste ⋅ / filter ⋅ space select ⋅ y copy ⋅ d delete ⋅ q quit ⋅ ? help` | ` p paste ⋅ q quit ⋅ ? help` |
| Items selected | ` y copy ⋅ d delete ⋅ space toggle ⋅ esc clear ⋅ ? help` | ` y copy ⋅ d delete ⋅ esc clear ⋅ ? help` |
| Typing in the filter | ` enter accept ⋅ esc cancel` | ` enter accept ⋅ esc cancel` |

- **Paste only shows when the clipboard has something.** Otherwise it's a dead hint taking 10 cells.
- **The selection count goes in the status line** (`3 selected · 1.2 MB`), not in the footer. Putting it in both would show the same fact twice.
- **Filter mode hides `q` and `?`.** While the filter field has focus, those keys type letters, so advertising them would be wrong.

## How hints are chosen

1. **Priority order:** filter, select, copy, delete, rename, new. Paste jumps to the front while the clipboard has items.
2. **Pinned group:** `q quit ⋅ ? help` always sits at the end. In the selection state, `esc clear ⋅ ? help` replaces it.
3. **Fill from the top of the list.** Add hints in priority order and stop at the first one that doesn't fit. Don't skip ahead to a shorter hint further down. That keeps the order fixed as the width changes, so hints never swap places.
4. **Keep it to width − 1.** Never fill the last column, because writing the bottom-right cell can trigger autowrap or scrolling on some terminals.
5. **Drop whole hints; never cut one off.** If even the pinned group doesn't fit, show ` ? help` alone.
6. **Leave out the obvious keys.** Arrows, `hjkl` and Enter-to-open don't get hints, since everyone tries them first. The cells go to keys people wouldn't guess. All of them are listed on the `?` screen.

## Styling

- **Key:** bold, plus an accent color if you like. **Label:** default text. **Separator `⋅`** (U+22C5): faint.
- Don't add brackets like `[q]`. Bold already marks the key, and brackets plus color would mark it twice.
- Don't color `d delete` red. The confirmation prompt is where you warn people; a red hint showing all the time just becomes noise.
- **Without color** (`NO_COLOR`), bold and the `key label` layout still make the bar readable.
- **ASCII fallback:** replace ` ⋅ ` with ` | `. Both are 3 cells wide, so the width math doesn't change.

## Clutter audit

- **Borders:** none. The bar sits directly on the bottom row, and the status line above it is enough of a divider.
- **Ways each key is marked:** one, which is bold.
- **Markers on every row:** none.
- **Chrome:** 6 separators out of 73 cells at 80 columns, about 8%. That's below the share a two-space separator would spend on gaps.

## Implementation notes

- Define each binding once, with `key`, `label`, `priority`, `contexts` and `pinned`. Generate both the footer and the `?` screen from that one keymap, so they can't drift apart.
- Make the layout a pure function, `render(hints, context, width) -> string`. Measure terminal cell width, not string length.
- Golden-test its output at widths 80, 60, 40 and 20, and in every context.

No framework was named, so this is framework-neutral. Bubble Tea's `bubbles/help` and Textual's `Footer` can generate most of this for you; with Ratatui or Ink you write the helper yourself.
