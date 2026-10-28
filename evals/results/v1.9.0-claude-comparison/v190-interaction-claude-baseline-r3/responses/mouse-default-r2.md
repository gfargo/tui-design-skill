## Full-screen TUI (alternate screen)

Enable these, together, after switching to the alternate screen (`?1049h`):

| Mode | Sequence | Why |
|---|---|---|
| **1000** – button press/release | `\e[?1000h` | Clicks and wheel (wheel arrives as buttons 64/65) |
| **1002** – button-event tracking | `\e[?1002h` | Motion only while a button is held, which is what you need for drag (splitters, selection, scrollbar thumbs) |
| **1006** – SGR extended encoding | `\e[?1006h` | **Required in practice.** The legacy encoding breaks past column/row 223, can't say *which* button was released, and produces bytes that aren't valid UTF-8. SGR gives `\e[<b;x;yM` / `...m`. |

Optional:
- **1003** (any-motion) instead of 1002, but only if you actually render hover effects. It sends an event for every cell the pointer crosses, so you'll have to coalesce events.
- **1004** (focus in/out) and **2004** (bracketed paste) aren't mouse modes, but full-screen apps usually want them too.

Skip **1005** (UTF-8 encoding) and **1015** (urxvt). Both are superseded by 1006 and ambiguous to parse. Keep a fallback parser for legacy X10 `\e[M` sequences anyway, for terminals that ignore 1006.

**Cleanup is the part people get wrong.** Disable everything in reverse order (`?1006l ?1002l ?1000l`, then `?1049l`) on:
- normal exit
- `SIGTSTP` (Ctrl-Z), then re-enable on `SIGCONT`
- panics, uncaught exceptions, and `SIGINT`/`SIGTERM`

If you miss one, the user's shell fills with garbage like `[<0;12;5M` every time they click.

Also tell users about the escape hatch: in most terminals, Shift+drag (Option+drag in some macOS terminals) bypasses mouse reporting so they can still select text natively.

## Inline picker (main screen, no alt-screen)

**My recommendation: keyboard-only by default, with mouse support as an opt-in flag.**

Reasons against capturing the mouse inline:
- **It takes over the scroll wheel.** The user expects the wheel to scroll terminal scrollback. Once you enable reporting, the wheel goes to your app.
- **It breaks native selection.** The user can't copy text from earlier output, including the content right above your picker, without the Shift modifier.
- **The coordinates are absolute screen positions.** You have to query the cursor position (`\e[6n`) to find where your region starts, and that changes if the terminal scrolls when you draw or resizes.
- **Leftover modes are worse here.** If cleanup fails, the user drops straight back into their shell prompt with reporting still on.

There's precedent the other way: fzf enables the mouse by default even in `--height` inline mode and offers `--no-mouse`. It works, but it's the most common complaint about fzf in inline mode.

If you do add mouse support inline:
- Use **only 1000 + 1006**. No motion tracking, because an inline picker has nothing to drag.
- Use wheel events to scroll the list and clicks to select a row.
- Map clicks to rows relative to the origin you got from `\e[6n`, and re-query after any resize.
- Turn reporting off *before* you print the final selection and return to the shell.
