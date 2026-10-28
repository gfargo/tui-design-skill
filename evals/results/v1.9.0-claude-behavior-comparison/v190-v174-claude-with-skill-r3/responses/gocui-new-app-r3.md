**No. Use Bubble Tea v2 with Lipgloss and Bubbles, and copy lazygit's interaction design rather than its library.**

## Why not gocui

- **lazygit no longer depends on gocui as a library.** In April 2026 it copied jesseduffield's fork into its own repo as `lazygit/pkg/gocui` and moved it to tcell v3. That fork is effectively retired as a standalone dependency. If you say "use gocui like lazygit does," you'd be using code that only lazygit maintains, for lazygit.
- **The maintained alternative is old.** `awesome-gocui/gocui` last released v1.1.0 in 2022, and it still runs on tcell v2.
- **It gives you very little structure.** You compute every view's coordinates by hand from `g.Size()`, write into views as `io.Writer` buffers, and register keybindings per view. lazygit works because of all the code it built on top of that.
- **Only pick gocui if** you're maintaining an existing gocui app, or you specifically want its "views as writable buffers" model.

## Why Bubble Tea fits a multi-panel app

- **State lives in one place.** One model with a `focused` field. Every key goes through `Update`, and `View()` builds the whole frame. Focus routing, panel tabs, and popups are just state changes you can unit-test without a terminal.
- **Background work stays off the UI thread.** Git, network, and other subprocess calls run as `tea.Cmd`s and return messages. This is how gitui stays responsive on huge repos, and it's what makes a lazy-style tool feel fast.
- **Popups and editor handoff are built in.** Lipgloss v2 layers can draw confirmation popups over panels and tell you which layer a click hit. `tea.ExecProcess` hands the terminal to `$EDITOR` and takes it back cleanly. In the callback, reload your data, because a repaint alone still shows the old state.
- **Components exist:** `list` (scrolls large data efficiently, has a filter), `viewport` for the diff pane, `key` and `help` for the footer, and `spinner` for background fetches.
- **The cost:** there's no flexbox. You calculate pane sizes from `tea.WindowSizeMsg` yourself, which is about the same work as gocui's manager function. In v2, a style's `Width` includes its border and padding, so don't carry over v1-style `w-2` math.

(If you'd rather have ready-made widgets and callbacks, tview is the other serious option; k9s uses it. For a lazygit-style app, Bubble Tea is the better fit.)

## What to copy from lazygit

- **Panels never move.** `1`–`5` jump to a panel, `Tab` cycles, and `[`/`]` switch sub-tabs inside a panel.
- **Letters mean different things per panel.** This only works because a **footer hint bar always shows what each key does in the focused panel.** If you skip the footer, don't use context-sensitive letters.
- A command log that shows the commands that actually ran.
- Destructive actions ask for confirmation (Enter confirms, Esc cancels), or support undo (`z`/`Z`).
- `?` opens help. `q` quits, except while the user is typing in a filter. Ctrl+C always works.

## Layout sketches

Wide (120×30):
```
 1 Status ─────────────────┐ Diff ─────────────────────────────────────────┐
 main ↑2 ↓0                │ @@ -12,6 +12,9 @@                             │
 2 Files ──────────────────┤ - old line                                    │
 M  src/app.go             │ + new line                                    │
▌A  src/panel.go           │                                               │
 3 Branches  Local│Remote ─┤                                               │
 * main                    │                                               │
 4 Commits ────────────────┤                                               │
 a1b2c3 fix resize         │                                               │
 5 Stash ──────────────────┤                                               │
                           │                                               │
 Command log ──────────────┴───────────────────────────────────────────────┘
 git add src/panel.go
 space stage · c commit · d discard · enter open · ? help · q quit
```

Floor (60×24, e.g. a tmux split): only one pane at a time, opened by drilling in.
```
 2 Files (1/5) ────────────────────────────────────────────┐
 M  src/app.go                                             │
▌A  src/panel.go                                           │
 ?? notes.md                                               │
                                                           │
 1-5 panel · enter diff · esc back · ? help                 
```

## What happens at smaller sizes

- **≥100 columns:** sidebar plus diff.
- **80×24:** narrower sidebar (about 32 columns). Panels that don't have focus collapse to their title line, and the focused panel gets the spare height. The command log hides; toggle it with a key.
- **60 columns:** one pane at a time, as sketched above. Enter opens the diff full-width, Esc goes back.
- **Below about 40×10:** show an honest "Terminal too small (need 40×10)" message instead of a broken layout.

## Clutter audit

- **Borders:** keep one border level. Panels share edges, so don't nest a box inside a box.
- **Focus:** show it with two signals, a bright border plus a `▌` marker on the cursor row. Not three or four.
- **File status:** a letter (`M`/`A`/`??`) plus color is enough. Drop any extra icon column that says the same thing.
- **Footer:** it lists keys for the focused panel only, never every binding in the app.

## Test plan

- **Unit tests:** send synthetic key presses into `Update` and check focus, selection, and resulting commands.
- **Golden frames:** snapshot rendered frames at 120×30, 80×24, 60 columns, and the minimum size, with the color profile pinned.
- **One end-to-end run in a real terminal:** quit, Ctrl+Z suspend/resume, and the `$EDITOR` handoff.

If you'd like, I can sketch the model struct and the focus/key-routing skeleton next.
