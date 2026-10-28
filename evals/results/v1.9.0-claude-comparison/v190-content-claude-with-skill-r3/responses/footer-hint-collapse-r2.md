I'd use one unboxed line with hints in the form `key action ⋅ key action`. Bold the keys and leave the labels in normal weight. When the line is too narrow, it drops whole hints in a fixed priority order. `? help` is always shown, so the full keymap is never more than one key away.

## Default (browsing)

```
80 columns
--------------------------------------------------------------------------------
 space mark ⋅ / filter ⋅ c copy ⋅ m move ⋅ r rename ⋅ d delete ⋅ q quit ⋅ ? help

40 columns
----------------------------------------
 space mark ⋅ / filter ⋅ q quit ⋅ ? help
```

At 80 columns all eight hints fit, using exactly 80 cells. At 40 only the four most important fit, also using exactly 40.

`enter open` is left out on purpose. Every file manager opens on Enter, so the hint teaches nothing and takes 13 cells. That space is what lets all eight useful hints fit at 80. The `?` help screen still lists Enter.

## How the line drops hints

Order on screen is by how often each action is used, with the exits (`q`, `?`) at the right. Hints are dropped by a separate priority list, lowest first:

| Priority | Hint | Why it ranks here |
|---|---|---|
| pinned | `? help` | The way back to everything that got dropped |
| 1 | `space mark` | Not obvious, and copy, move and delete on several files depend on it |
| 2 | `/ filter` | The fastest way to get around a big directory |
| 3 | `q quit` | Someone who is lost needs a way out |
| 4–7 | `c copy`, `m move`, `d delete`, `r rename` | Expected letters that are easy to guess |

The fitting rule:

```
budget = width - 1                     # one leading space; the line may end flush right
shown  = [help]
for hint in by_priority:               # keep going after a miss: a short hint can still fill a gap
    if cell_width(render(shown + [hint])) <= budget:
        shown.append(hint)
render(sorted(shown, key=display_order))
```

At 60 columns, the floor for a tmux split, the rule gives this:

```
 space mark ⋅ / filter ⋅ c copy ⋅ m move ⋅ q quit ⋅ ? help
```

Measure display cells, not string length. Translated labels will be longer, and the rule should drop them correctly too.

## The footer changes with context

The hints show what the keys do right now, so the footer needs one variant per mode:

```
Files marked (count goes in the status line, not here)
80: c copy ⋅ m move ⋅ d delete ⋅ r rename ⋅ space unmark ⋅ esc clear ⋅ ? help
40: c copy ⋅ m move ⋅ d delete ⋅ ? help

Filter input has focus (letters are typed text now, so no letter hints)
80/40: enter apply ⋅ esc cancel
```

Once something is marked, `d delete` survives even at 40 columns, because that's when it matters. In filter mode, `?` and `q` disappear because they'd be typed into the filter. Showing them there would be wrong.

## Details

- **Separator:** `⋅` (U+22C5) has a fixed width of 1 cell. The middle dot `·` doesn't: some terminals draw it 2 cells wide and break the alignment. The ASCII fallback is `|`, which is the same width.
- **`NO_COLOR`:** bold keys plus the separator still read clearly. Color can tint the keys, but nothing should depend on it. Don't dim the labels so far that they're hard to read.
- **Clutter check:** there's no border, no `Keys:` label and no `[q]` brackets. Brackets would add 16 cells at 80 columns and push `rename` and `delete` off the line. Each hint carries one signal (the bold key), and separators use 21 of the 80 cells.
- **One source of truth:** build the footer from the keymap. Give each binding a label, a priority and a context, so the footer and the `?` screen can't disagree. Bubble Tea's `bubbles/help` and Textual's `Footer` already read from bindings. In Ratatui or Ink you'd write a small helper.
- **Tests:** pin golden frames at 80, 60 and 40 columns for each of the three contexts. The 80-column default fills the line exactly, so a longer label will make it drop `rename`. That's intended, and the test should check it happens.

If you tell me the framework, I can turn this into real binding definitions.
