**Yes, add a palette, but don't put it on `/`.** In a log viewer, `/` should mean search.

## What `/` should do

People who use log viewers already expect `/` to search. That habit comes from `less`, `vim`, `man`, `k9s` and `lnav`. Someone tailing logs will hit `/` without thinking, and if a palette opens instead, the tool feels broken.

So `/` should search the current view:
- Matches highlight as you type.
- `Enter` confirms, `n` jumps to the next match, `N` to the previous one.
- `Esc` cancels and puts the scroll position back where it was.
- Plain text by default. Add a regex toggle if you need it, since regex is less forgiving for quick searches.

Decide early whether `/` **searches** (jumps between matches) or **filters** (hides lines that don't match). They're different operations and people will want both. A common split is `/` for search and `&` for filter (`less` uses `&`), or `f` for filter if you want something easier to remember. Show active filters somewhere that stays on screen, like the status bar. Otherwise a hidden filter makes the logs look like they're missing lines.

## Where the palette goes

Use `:` or `Ctrl+P` (or `Ctrl+K`). `:` fits a vim-style, keyboard-heavy tool, and `k9s` uses it the same way. `Ctrl+P` will feel familiar to people coming from VS Code. You can bind both.

## Why a palette pays off at ~35 actions

That's too many to keep in a help screen people actually read, and too many single-key bindings to remember. A palette fixes the "I know it can do this, but how?" problem. To get the most from it:

1. **Show each action's keybinding next to its name** (`Toggle wrap   w`). This is the biggest win: users learn the shortcuts and stop needing the palette for common actions.
2. **Make it depend on the current screen.** Show actions for this screen first, then global ones. Hide actions that can't run here, or show them dimmed.
3. **Use fuzzy matching on names plus aliases**, so "wrap", "line wrap" and "soft wrap" all find the same action.
4. **Put recently used actions at the top** when the query is empty.
5. **Allow arguments where they make sense**, for example `:goto 14:32`, `:level error` or `:export json`. This is where `:` beats `Ctrl+P`, because it feels like typing a command.

## What it doesn't replace

- **Direct keys for the 8–12 most frequent actions**: scrolling, follow/tail toggle, search, filter, level toggles, wrap, switching screens. Nobody should need the palette for these.
- **`?` for a help overlay** with the bindings for the current screen, grouped by category. The palette is for finding a specific action. Help is for browsing what's available.
- **A one-line hint in the status bar**, like `/ search  : commands  ? help`, so all three are visible from the start.

## Summary

| Key | Action |
|---|---|
| `/` | Search the current view (`n`/`N` for next/previous match) |
| `&` or `f` | Filter lines |
| `:` / `Ctrl+P` | Command palette, depends on the screen, shows keybindings |
| `?` | Help overlay for the current screen |
| single keys | The dozen most frequent actions |

If you share the action list or your current keymap, I can help sort out which actions get direct keys and which are fine living only in the palette.
