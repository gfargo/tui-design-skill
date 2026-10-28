**Yes, add a palette, but don't put it on `/`.** In a log viewer, `/` should be search.

## Why `/` should be search

Anyone who opens a log viewer has used `less`, `vim`, `man` or `k9s`, and in all of them `/` means "find text." That reflex is strong. If `/` opens a palette instead, users will type an error string, get fuzzy-matched action names back, and decide the tool is broken. Searching is also the thing people do most in a log viewer, so it should get the cheapest key.

**What `/` should do:**
- **Search incrementally:** jump to the first match as the user types and highlight every match on screen.
- **`n` / `N`** go to the next and previous match. **`?`** searches backward, if you aren't already using `?` for help (more on that below).
- **`Enter`** confirms and leaves the highlights on. **`Esc`** cancels and returns to where the user started.
- **Smart-case:** ignore case unless the query has an uppercase letter. Treat the query as a literal string by default and offer a regex toggle, because people paste things like `[ERROR]` and `user.id`.
- **Pause follow/tail mode while searching.** Otherwise new lines arrive and the match scrolls out from under the user. Show a clear "paused" indicator.
- **Keep search and filter separate.** Search moves the cursor; a filter hides lines that don't match. People need both. Put filter on its own key: `&` is what `less` uses, and `f` also works. Keep the active filter visible in the status bar so nobody forgets lines are hidden.

## The palette

At around 35 actions spread over several screens, nobody will remember every keybinding, so a palette is worth adding for discoverability. Treat it as a way to find actions, not a replacement for direct keys.

- **Key:** `:` matches `k9s` and vim command mode, which suits a terminal tool. `Ctrl+P` or `Ctrl+K` are the editor-style choices. I'd use `:`, plus `Ctrl+P` as an alias.
- **Context-aware:** list the current screen's actions first, then global ones. Leave out or grey out actions that don't apply right now.
- **Show each action's keybinding next to its name**, e.g. `Toggle timestamps   t`. This is the most useful feature, because the palette teaches the shortcuts and frequent users stop needing it.
- **Fuzzy match on names and aliases**, e.g. so "wrap" finds "Toggle line wrapping." Put recently used actions at the top.
- **Allow arguments where they make sense**, e.g. `:goto 14:32` or `:level warn`. This is where a palette does better than single keys.

## Resulting keymap

| Key | Action |
|---|---|
| `/` `?` `n` `N` | Search |
| `&` or `f` | Filter |
| `:` / `Ctrl+P` | Command palette |
| `F1` or `?` | Help (if `?` isn't backward search) |
| Single letters | The most common actions on each screen |

One way to check the design: a new user should be able to run every action from the palette, and a frequent user shouldn't need to open it for anything they do every day.

If you share the code or your current keymap, I can point out conflicts and suggest where the palette would fit in.
