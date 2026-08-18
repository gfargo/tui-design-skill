No: while the filter input is active, bare `j` and `k` must be query text—not navigation. Use `↑/↓` plus `Ctrl-J`/`Ctrl-K` (and optionally `Ctrl-N`/`Ctrl-P`) for selection movement. That matches fzf’s model.

fzf is **full-screen by default**, not inline. `--height` makes it a bounded picker below the cursor; user defaults can of course override this. [fzf README](https://github.com/junegunn/fzf/blob/master/README.md)

### Screen contract

- Default to a full-screen, alternate-screen picker if you are deliberately emulating fzf.
- Offer inline/bounded mode explicitly (`--height`-like) when keeping the shell context visible matters.
- Render interactive UI on `/dev/tty` (or stderr); write only the accepted item(s) to stdout.
- On accept: stdout contains the selected value(s), exit `0`.
- On cancel: no stdout, non-zero exit. Restore terminal state on every path.
- Layout: query line, `matched / total` count, result list with a clear active-row marker, optional preview. Update within 100 ms per keystroke.
- Preserve the highlighted item by identity across a re-filter when it still matches; otherwise select the first result.

```text
> src ut                         12 / 4,382
❯ src/utils/format.ts
  src/utils/date.ts
  src/app.ts
  …
↑↓ / C-j C-k move · Enter choose · Esc cancel
```

### Key contract

| Key | Action |
|---|---|
| Printable characters, including `j`/`k` | Insert into query |
| Backspace | Delete query character |
| `Ctrl-A` / `Ctrl-E` | Start / end of query |
| `Ctrl-W` | Delete previous query word |
| `↑` / `↓` | Previous / next result |
| `Ctrl-K` / `Ctrl-J` | Previous / next result |
| `Ctrl-P` / `Ctrl-N` | Optional previous / next aliases |
| `PageUp` / `PageDown` | Scroll a page |
| `Home` / `End` | First / last result |
| `Enter` | Accept active result |
| `Esc` | Clear query if nonempty; otherwise cancel |
| `Ctrl-C` | Cancel cleanly |
| `Tab` | Toggle mark, only in multi-select mode |

Do not add a normal-mode-style `j/k` binding unless you explicitly introduce a navigation mode with a strong visible mode indicator. For an immediate picker, text entry is the primary state.
