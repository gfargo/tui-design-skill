Yes, add a palette. But don't put it on `/`.

## The command palette

Once you have about 35 actions spread over several screens, nobody will remember all the keybindings. A palette makes every action findable without adding more help screens. To make it work well:

- **Bind it to `:` or `Ctrl+P`.** `:` is the convention in vim, k9s and lazygit-style tools, and it leaves room for typed commands later, like `:level error` or `:since 10m`. `Ctrl+P`/`Ctrl+K` is more familiar to people coming from VS Code or the web. You can bind both.
- **Show each action's keybinding next to its name.** That's how people learn the shortcuts and eventually stop opening the palette.
- **Rank actions by context.** Put the current screen's actions first and global actions after them. Hide actions that don't apply right now, or dim them.
- **Use fuzzy matching and put recent actions first.** "tl" should find "Toggle line wrap", and the last few actions used should appear at the top when the query is empty.
- **Keep it as a second way in, not the only way.** Common actions still need single-key bindings. The palette is for the long tail and for discovery.

## What `/` should do

In a log viewer, `/` should be **search**. Users of `less`, `vim`, `man`, `journalctl` and `k9s` will press `/` expecting search without thinking about it. If it opens something else, it'll feel broken.

Decide early whether search and filter are separate, because they work differently:

| Key | Behavior | Precedent |
|---|---|---|
| `/` | Search forward: highlight matches, keep every line visible | less, vim |
| `?` | Search backward (or help, see below) | less, vim |
| `n` / `N` | Next / previous match | less, vim |
| `&` or `f` | **Filter**: hide lines that don't match | less (`&`) |
| `Esc` | Clear the search or filter | |

I recommend keeping them separate. For logs, you often want to find an error and then read the lines around it, and a filter hides that context. If you only want one, make `/` a live filter and show a clear "filtered: N of M lines" indicator so nobody thinks logs went missing.

**`?` conflict:** you can't use `?` for both backward search and help. Most TUIs today use `?` for help, and backward search is rarely used in a log viewer, so give `?` to help and let `N` handle going backward.

## Summary

- `/`: search (or filter)
- `:` / `Ctrl+P`: command palette
- `?`: help with the keybinding reference

If you share the action list or the code, I can suggest the grouping, which keys get direct bindings, and which actions only need to live in the palette.
