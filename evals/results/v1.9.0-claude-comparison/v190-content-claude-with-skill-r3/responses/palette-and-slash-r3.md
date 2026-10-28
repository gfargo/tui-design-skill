**Yes, add a palette.** At 35 actions spread over several screens you're past the point (around 20 actions, or actions spanning several contexts) where footer hints plus `?` help are enough. **Keep `/` for search and filter in the current view, not for the palette.** Open the palette with `:` and use `Ctrl+P` as an alias.

## Why `/` shouldn't open the palette

In a log viewer, `/` is the most practised key your users have. In `less`, vim, lazygit and k9s it means "find in what I'm looking at", and people will press it without thinking. If it opens a list of actions instead, your app breaks that habit on the action they repeat most often.

`/` does two related jobs, and the focused view picks which one:

| Focused view | `/` does | Details |
|---|---|---|
| Log stream / document | **Search**: jump between matches | `Enter` goes to the first match, `n`/`N` cycle, show `(2/15)`, highlight all matches, `Esc` returns to where you were |
| Lists (sources, saved queries, hosts) | **Filter**: narrow the rows | Update in under 100 ms, show `123/45678`, `Esc` clears |

Use smart-case for both: an all-lowercase query ignores case, and mixed case matches it.

One log-specific rule: a filter on a live stream keeps following. New matching lines appear and the count updates. Search, on the other hand, moves the viewport, which pauses follow mode. Show that it's paused (`▾ 37 new`), and let `G` or `F` re-pin to the bottom.

## How the palette should work

- **Keys:** `:` opens it, with `Ctrl+P` as an alias. Don't make `Ctrl+P` the only route, because Zellij takes it in its default mode and readline uses it for history. `:` has neither problem and matches the k9s/helix command model, which suits a tool for operators.
- **Coverage:** every action with a keybinding is also a palette command. The key is the shortcut; the palette entry gives the full name and a searchable description.
- **Show the key on each row,** so the palette also teaches the shortcuts.
- **Rank commands for the current screen first,** then global ones. Show commands that can't run right now as dimmed with a reason, not hidden.
- **`Esc` closes the palette only.** It's one step down the quit ladder; it never also clears a filter or quits.

```
Wide (120×35)
 app-api › prod                          following ● 12,403 lines
┌──────────────────────────────────────────────────────────────┐
│ :tog                                                        │
│ ▸ Toggle follow mode            F        stream             │
│   Toggle line wrap              w        stream             │
│   Toggle timestamps             t        stream             │
│   Toggle level: DEBUG           —        filter             │
│   Theme: toggle light/dark      —        global             │
│                                              5/35           │
└──────────────────────────────────────────────────────────────┘
 ↑↓ select  enter run  esc close
```

```
Floor (60×24)
 app-api › prod               ● 12,403
┌──────────────────────────────────────────┐
│ :tog                                     │
│ ▸ Toggle follow mode               F     │
│   Toggle line wrap                 w     │
│   Toggle timestamps                t     │
│   Toggle level: DEBUG              —     │
│                                   5/35   │
└──────────────────────────────────────────┘
 enter run  esc close
```

At 60 columns the context column goes first, then descriptions truncate with `…`. The command name and its key always stay. The modal stays within 60–80% of the width (at least 30 columns), and its border, title and changed footer show that it's open even under `NO_COLOR`.

## The other layers still matter

The palette sits on top of the other discovery layers, not in place of them:

1. **Footer:** 3–5 hints that change with the screen, e.g. `/ search  F follow  : commands  ? help`. Make sure `:` is listed there, or nobody will find the palette.
2. **`?` help:** every binding, grouped by screen.
3. **Optional which-key** on a leader key, if you have clusters like "level filters" or "export as…".
4. **The palette.**

Define each key once in a keymap table and generate the footer, the help screen and the palette from it. Otherwise the three will drift apart.

## Questions to check against your app

- Is there free text entry anywhere, such as a query bar? While it has focus, `/` and `:` must be typed as characters.
- Do you already bind `:` to something like "go to line"? If so, add a `:42` command to the palette rather than giving up `:`.
- Do you want the palette to take arguments, like k9s's `:pods`? That's useful for "switch source", e.g. `:source prod-api`, and is a good reason to choose `:` over a plain fuzzy list.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show how to build the shared keymap and palette in it. Textual, for example, already ships a palette you'd configure rather than build.
