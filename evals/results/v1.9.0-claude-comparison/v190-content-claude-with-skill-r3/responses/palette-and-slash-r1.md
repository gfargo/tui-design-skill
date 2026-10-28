# Command palette and `/` for a log viewer

**Yes, add a command palette. Keep `/` for search, not the palette.** At 35 actions spread over several screens, footer hints and `?` help aren't enough on their own: the footer can only show about 5 keys, and a long help screen is slow to scan. A palette lets users find actions by name. But `/` already means "find in this content" in less, vim, lazygit and k9s, and log readers will press it without thinking. Taking it over for the palette would break that habit on every screen.

## Key assignments

| Key | Does | Why |
|---|---|---|
| `Ctrl+P` | Opens the palette | The usual palette key. |
| `:` | Also opens the palette | Zellij and readline take `Ctrl+P`, so users need a route with no Ctrl chord. |
| `/` | Searches the log text | Like less and vim: `Enter` jumps to the first match, `n`/`N` move between matches, and the count shows as `(3/41)`. |
| `/` on list screens | Filters the list (sources, saved queries, and so on) | The focused view decides whether `/` searches or filters. |
| `&` (or `f`) | Filters log lines | In a log, "jump to matches" and "show only matches" are different jobs, so give filtering its own key (less uses `&`). |
| `?` | Opens the full keymap, grouped by screen | Still needed even with a palette. |

**Search vs. filter in the log view:**
- **Search** keeps every line and moves the viewport to matches. `Esc` cancels and returns to where you were.
- **Filter** hides lines that don't match. It should keep following: new matching lines appear and the count updates (`1,204/88,310`). `Esc` clears it.
- Use smart-case for both: an all-lowercase query ignores case, a mixed-case query matches case exactly.

## Palette rules

1. **Every action with a key binding must also be a palette command.** That includes screen-specific actions. Never put an action only in the palette.
2. **Show the key binding next to each command.** The palette then also teaches the shortcuts.
3. **Rank the current screen's commands first** and label each with the screen it belongs to. Commands for other screens either switch to that screen and run, or are hidden. Pick one behavior and use it everywhere.
4. **Add searchable synonyms**, so typing "tail" or "live" finds *Toggle follow*.
5. **Fit `Esc` into one fixed order.** Each press does one step: close the palette, then clear the search or filter, then go back a screen. `Esc` never quits.

## Layout

At 80 columns:
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ > follow_                                                         4/35       │
│ ▸ Toggle follow mode            F      Logs     resume tailing at the end    │
│   Jump to end                   G      Logs                                  │
│   Filter lines…                 &      Logs     show only matching lines     │
│   Follow source on open         —      Sources                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

At 60 columns (a tmux split) the description column goes first, then the screen label. The command name and key always stay:
```
┌──────────────────────────────────────────────────────────┐
│ > follow_                                           4/35 │
│ ▸ Toggle follow mode                                  F  │
│   Jump to end                                         G  │
│   Filter lines…                                       &  │
└──────────────────────────────────────────────────────────┘
```

- **Borders:** one border only. The palette is an overlay, so don't nest it inside another frame.
- **Selection marker:** mark the selected row with `▸` plus reverse video. Don't color the row as well; one cue is enough and it still works in monochrome.
- **Truncation:** cut long command names with `…`. Never wrap rows.
- **Small terminals:** below about 8 rows the palette should take the whole screen rather than float.

## Supporting pieces

- **Footer:** show search state there while a search is active, e.g. `(3/41)  n next  N prev  Esc clear`. Show `▾ 37 new` when the user has scrolled up and the log is paused.
- **Optional which-key menu:** above about 20 actions, a leader key (e.g. `Space`) that pops up the next available keys is worth considering for power users. It's a nice extra on top of the palette.
- **Single keymap:** define keys in one place and generate the footer, `?` help and palette entries from it, so they can't drift apart.

If you tell me the framework you're using (Bubble Tea, Ratatui, Textual or Ink), I can show how to wire this up. Textual, for example, has a built-in palette you could extend.
