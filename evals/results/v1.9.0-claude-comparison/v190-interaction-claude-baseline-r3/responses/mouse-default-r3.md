**Short answer:** in the full-screen TUI, turn on **1000 + 1002 + 1006**, and add 1003 only if you need hover. In the inline picker, leave the mouse **off by default** and make it opt-in.

## Full-screen TUI (alternate screen)

| Mode | Enable? | Why |
|---|---|---|
| `?1000` (button press/release) | Yes | Basic clicks and wheel. |
| `?1002` (motion while a button is held) | Yes, if you support dragging | Needed for drag-select, resizing splits and scrollbars. It only sends events while a button is down, so it's cheap. |
| `?1003` (all motion) | Only if you need hover effects | It sends an event on every cell the pointer crosses. That's a lot of input to parse and re-render. |
| `?1006` (SGR encoding) | Always, alongside the others | Coordinates aren't capped at 223 columns, it's unambiguous, and it tells you which button was released (the legacy X10 encoding doesn't). |
| `?1005` / `?1015` (UTF-8 / urxvt encodings) | No | Obsolete and ambiguous. 1006 replaces both. |
| `?1004` (focus in/out) | Optional | Useful for pausing animations or dimming the cursor when the window loses focus. |

Enable on startup: `\e[?1000h\e[?1002h\e[?1006h`. Disable in reverse order on **every** exit path:
- normal quit
- panics and uncaught exceptions
- `SIGINT` / `SIGTERM`
- `SIGTSTP` (Ctrl-Z): disable before suspending and re-enable on `SIGCONT`
- before spawning `$EDITOR` or a pager

If any of these is missed, the user's shell is left printing escape codes whenever they move the mouse.

Other tips:
- **Tell users about the selection bypass.** Mouse reporting takes over native text selection. Most terminals let you select anyway with **Shift**-drag; in iTerm2 it's **Option**. Put this in your help screen.
- **If you only want the wheel to scroll,** you may not need mouse reporting at all. With `?1007` (alternate scroll mode), many terminals turn wheel events into Up/Down arrow keys while the alternate screen is active. Native selection keeps working and you add no parsing code.
- **Consider a `--no-mouse` flag or config option.** It helps people using tmux or screen setups, and people who prefer to copy text natively.

## Inline picker

My recommendation is **off by default, opt-in with a flag.** Reasons:

1. **Coordinates are screen-relative, not relative to your widget.** You don't know where your rows are unless you query the cursor position (`\e[6n`) at startup. That position goes stale if the content scrolls or the terminal is resized.
2. **It takes over things users expect inline.** Users expect wheel-scrolling through scrollback and click-drag copying of nearby output to keep working. A picker shown inline sits in the middle of their shell session, so this matters more than it does full-screen.
3. **Keyboard is the expected way to use it.** A picker is a short type-filter-Enter interaction. Mouse support adds little.
4. **Mistakes cost more.** If the picker crashes without disabling the modes, the user's normal shell is left broken. A full-screen app at least gets the alternate-screen teardown.

Some tools do this well (fzf enables the mouse by default even with `--height` and offers `--no-mouse`), so it's a defensible choice. If you add it:
- Use only `1000 + 1006`. Skip motion tracking.
- Query the cursor position before drawing, and handle the case where drawing makes the terminal scroll.
- Map clicks only inside your own rows and ignore everything else.
- Use the same cleanup on every exit path as the full-screen app.
