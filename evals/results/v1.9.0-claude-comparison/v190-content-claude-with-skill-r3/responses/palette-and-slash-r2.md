**Yes, add one.** At 35 actions spread across several screens you're past the point where a footer and `?` are enough on their own. **Don't put the palette on `/`, though.** In a log viewer `/` is the most-used key and it means "find" everywhere else, so it should stay find.

## What `/` should do

What `/` does depends on the focused view, but it's always some kind of find:

| Focused view | `/` does | Details |
|---|---|---|
| Log stream / document | **Search**: jump to matches | `Enter` goes to the first match, `n`/`N` cycle, show `(2/15)`, highlight all matches, `Esc` returns to where you were |
| Lists (sources, saved queries, files) | **Filter**: narrow the rows | Update in under 100 ms, show `123/45678`, highlight the matched text, `Esc` clears |

Use smart-case in both: an all-lowercase query ignores case, a query with capitals matches case.

Log-specific details:
- **Search pauses follow mode.** Jumping to a match moves the view, and any upward move should stop the tail. Show the backlog (`▾ 37 new`) so the user knows they're paused. `G` or `F` resumes following.
- **A filter keeps following.** New lines that match appear and the count updates.
- If you want both search and filter on the log view, keep `/` for search and give filter its own key, for example `&` (as in `less`) or `f`. Don't make one key do two things in the same view.

## How to open the palette

- **`Ctrl+P` as the main key**, plus **`:` as a second route that needs no Ctrl key.** Zellij takes `Ctrl+P` by default and readline uses it for history, so some users will never see that key arrive. `:` also gives power users a k9s-style command line (`:errors`, `:export`).
- **Every action that has a key binding goes in the palette.** Show the key next to each command name so the palette also documents the shortcuts.
- **Put the current screen's actions first**, then the others with a screen label. Picking a command from another screen takes you there and runs it.
- If an action can't run right now, show it dimmed with the reason (`no selection`) rather than hiding it. Otherwise people search for it, find nothing, and decide it doesn't exist.

```
Wide (120 cols): palette ~60% wide, centered, slightly above middle
┌ app-api ▸ live ─────────────────────────────────────────────────────────────── FOLLOWING ┐
│ 12:01:03 INFO  req id=81 200 12ms                                                        │
│ 12:01:03 WARN  ┌ Commands ─────────────────────────────────────────┐                     │
│ 12:01:04 INFO  │ : exp_                                            │                     │
│ 12:01:04 ERROR │ ▸ Export visible lines to file     e   This screen│                     │
│ 12:01:05 INFO  │   Export filter as saved query     S   This screen│                     │
│ 12:01:05 INFO  │   Expand JSON fields               x   This screen│                     │
│ 12:01:06 INFO  │   Export sources list                  Sources    │                     │
│                └───────────────────────────────────── 4/35 ────────┘                     │
└ ↑↓ choose  enter run  esc close ─────────────────────────────────────────────────────────┘

60 cols (tmux split): fit to content, drop the screen column, key stays
┌ Commands ──────────────────────────────────────┐
│ : exp_                                         │
│ ▸ Export visible lines to file              e  │
│   Export filter as saved query              S  │
│   Expand JSON fields                        x  │
│   Export sources list (Sources)                │
└──────────────────────────────────── 4/35 ──────┘
 ↑↓ choose  enter run  esc close
```

Below about 34 columns, the palette takes the whole screen as a plain list. When it opens, the footer switches to the palette's own hints. That way you can tell you're in a dialog even with `NO_COLOR` or a terminal that doesn't dim the background.

## The palette doesn't replace the other help

1. **Footer hints**: the 3–5 most-used keys for the current screen, built from the same keymap as everything else. For a log screen, that's something like `/ search  F follow  w wrap  : commands  ? help`. Put `:` or `Ctrl+P` in the footer so people find the palette.
2. **`?` help**: every binding, grouped by screen.
3. **Palette**: search by name for the actions people use rarely.
4. *Optional:* a which-key leader (`Space` opens a menu of follow-up keys) if you have groups of related actions like export or view settings. It's worth it above about 20 actions, but only add it if the groups are real.

Define every action once (id, name, key, screen, whether it can run now, reason if not). Then the footer, `?`, and the palette all come from that one list and can't drift apart.

## `Esc` order with the palette open

Each `Esc` press does one step: cancel a running export, then close the palette, then clear the search or filter, then go back one screen. At the top level, `Esc` does nothing. It never quits. While the palette's text field has focus, `q` and `/` are just letters you type.

If you tell me your framework, I can point you to its parts. Textual has a built-in palette, Bubble Tea's `bubbles/help` can build the footer, and in Ratatui or Ink you'd build both from your keymap.
