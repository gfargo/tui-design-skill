**Yes—add a command palette.** About 35 actions across several screens is enough to justify searchable commands.

Use four layers of discovery:

- **Footer:** 3–5 useful actions for the current screen.
- **`?`:** all bindings, grouped by screen or task.
- **`Ctrl+P`:** fuzzy command palette, with **`:` as an alternative** because terminal multiplexers can capture Ctrl bindings.
- **Direct shortcuts:** keep frequent actions fast. Every bound action should also appear in the palette, with its shortcut beside it.

Give commands clear names such as “Export visible logs” and “Resume following.” Prioritize relevant commands; label commands that act on another screen or require a selection.

**Reserve `/` for searching the focused content.** Its behavior should follow the view:

| Focused view | `/` does |
|---|---|
| Log content | Finds text without hiding surrounding lines |
| Source, file, or session list | Filters that list |
| Text input | Inserts a literal `/` |

For log search, show highlights and a match count such as `2/15`; `Enter` accepts, and `n` / `N` move between matches. `Esc` during search cancels and restores the prior position. Give **“Filter log lines…” a separate command**, since hiding nonmatching lines can remove useful diagnostic context.

Searching historical logs should pause following and hold the viewport steady. Show `PAUSED · 37 new`; `G` or “Resume following” returns to the live tail. Filtering can continue following matching arrivals.

A compact layout could look like this; omitted rows contain logs:

```text
Wide
api.log                         PAUSED · 37 new
12:04:01 ERROR request timeout request_id=abc123
Search: timeout                           2/15
/ search | F follow | : commands | w wrap | ? help

60 columns
api.log                  PAUSED · 37 new
12:04:01 ERROR request timeout request_id=abc123
Search: timeout                    2/15
/ search | F follow | : commands | ? help
```

At 80×24, keep logs dominant and make details a drill-down. At 60 columns, hide any source sidebar, truncate long lines, and let the palette use the available width. Below a declared usable minimum, show a truthful “terminal too small” message.

For clutter, target **zero permanent borders, one palette border, one textual follow-state indicator, and one footer row**. Remove repeated per-line markers and avoid putting all 35 actions on screen. The palette should make actions discoverable while leaving room to read logs.