**Yes—35 actions across several screens warrants a command palette. Keep `/` for searching the content in focus.**

Assuming this is a full-screen viewer, the main loop is reading logs, finding an event, inspecting it, and returning to live output. Keep those frequent actions directly accessible; use the palette to make the rest discoverable.

| Key | Behavior |
|---|---|
| `/` | Search log text; filter items when focus is on a source/session list |
| `n` / `N` | Next / previous log match |
| `:` | Open the command palette |
| `Ctrl+P` | Palette shortcut; retain `:` because multiplexers can capture Ctrl chords |
| `?` | Help, grouped by screen and action category |

For **log search**, preserve surrounding lines rather than hiding nonmatches. Highlight matches, show `2/15`, and let Enter jump to the first match. Esc cancels and restores the previous position; after committing, Esc clears the search. Label the prompt `Search logs` so its scope is clear.

Give **filtering logs** its own named action, such as “Filter logs by level or text.” Filtering removes rows and should display a visible filter summary and matching/total count. A filter can keep following incoming matches; navigating to a search result should pause follow so new output cannot pull the result away. Show `PAUSED · 37 new`; `G` resumes follow.

The palette should:

- Fuzzy-match command names, descriptions, and useful synonyms.
- Include every action with a keybinding and display that binding.
- Rank actions relevant to the current screen first; label actions that navigate elsewhere.
- Explain unavailable actions, such as “Copy selected line — select a line first.”
- Use arrows to select, Enter to execute, and Esc to close and restore focus.
- Treat printable keys as query text while open.

Keep 3–5 contextual footer hints and `?` help alongside it. You don’t need a separate leader menu immediately.

A compact layout could behave like this:

```text
Wide                               60-column split
Sources | Logs                     Logs
        | 12:41 request timed out  12:41 request timed out
        | PAUSED · 37 new          PAUSED · 37 new
/search  G follow  : commands  ?    /search G follow :commands ?
```

At 80×24, prioritize logs and make sources/details drill-down views. At 60 columns, use one pane; the palette shows command names and keys, dropping descriptions first. A reasonable initial minimum is 40×10; below that, show the required dimensions and keep quit working.

For visual clutter, aim for zero main-view borders, at most one palette border, one selection cue, and no marker on every log row. A one-line header and footer cost 2 of 24 rows; avoid turning the 35 actions into permanent chrome.