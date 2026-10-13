The fix is to stop treating the background query as something startup has to wait for. Draw the first frame right away with a default palette, ask the terminal in the background, and repaint if an answer arrives. Ask again whenever the terminal reports a theme change.

## 1. Pick the palette in this order

1. **Explicit user choice:** `--theme light|dark`, a config key, or an env var. This always wins and skips the query entirely. It's also the fix for terminals that never answer.
2. **Terminal reply** to the background query (section 2).
3. **`$COLORFGBG`**, set by rxvt-style terminals. It's free and needs no network round trip.
4. **Default palette.** Make it a 16-color ANSI theme. Those colors follow the user's own terminal palette, so they're readable on either background, and switching to the detected palette later is a small refinement rather than a jarring flash.

Default to `auto` and use the override only when the user sets it.

## 2. The startup query

- **Send two queries in one write:** `OSC 11 ; ? ST` (background color), then DA1 `CSI c`, which every terminal answers. The Linux console, PuTTY, mosh, GNU Screen, and ConEmu never answer OSC 11. If the DA1 reply arrives first, no background reply is coming, so you can stop waiting right away. This is your "some terminals never answer" case.
- **Still cap the wait.** Real apps use anywhere from 100 ms (Neovim) to 500 ms (lazygit, chosen for slow SSH) to 2 s (Lip Gloss). Because the UI is already drawn, the cap only decides how long you keep listening, so a generous value like 500 ms to 1 s is fine.
- **Read the replies through your normal input parser.** Don't run a separate blocking `read()` before the event loop starts. A blocking read is the likely cause of your SSH stall, since every query costs a network round trip. It can also swallow keystrokes the user types during startup.
- **Parse defensively.** The reply looks like `rgb:rrrr/gggg/bbbb`, can end with either BEL or ST, and each channel can have 1 to 4 hex digits. Scale each channel, compute luminance, and treat anything below about 0.5 as dark.
- **tmux 3.4+** answers OSC 11 itself with the attached client's colors, so the query works inside tmux too.

## 3. Noticing OS theme changes

- **Use mode 2031 where it's supported.** First check support with DECRQM (`CSI ? 2031 $ p`), then enable it with `CSI ? 2031 h`. The terminal then sends `CSI ? 997 ; 1 n` when it switches to dark and `CSI ? 997 ; 2 n` when it switches to light. kitty 0.38.1+, Ghostty, foot 1.23+, and iTerm2 3.7+ support it, and tmux 3.8 passes the outer terminal's changes through. WezTerm doesn't support it.
- **When a change report arrives, send OSC 11 again** and use that answer instead of trusting the dark/light bit alone. lazygit and Neovim do the same.
- **Fallback for other terminals:** turn on focus reports (mode 1004) and send OSC 11 again whenever the window regains focus. That's my suggestion, not an established convention. It catches a theme switch made while the user was in another app, which is the usual case.
- **Turn 2031 off on every exit path** and before handing the terminal to a child process like `$EDITOR`. Turn it back on and query again when you resume.

## 4. Applying the result

Keep colors behind semantic tokens like `text.muted` and `status.error`. A theme change should only swap which palette the tokens point to, rebuild the styles, and force a full redraw. If the user has explicitly chosen a theme, ignore change reports.

## Framework notes

- **Bubble Tea v2:** don't call `lipgloss.HasDarkBackground` inside a running program, because its query competes with Bubble Tea for input. Instead, return `tea.RequestBackgroundColor` from `Init` and handle `tea.BackgroundColorMsg` with `lipgloss.LightDark(msg.IsDark())`. Bubble Tea passes 2031 reports through but doesn't enable the mode, so your app has to send `CSI ? 2031 h` itself.
- **Textual, Ink, and Ratatui** don't handle 2031 at all. You'd write the query and parse the reply yourself, and with Ratatui/crossterm you're responsible for restoring that mode.

Tell me which stack you're on and I can sketch the exact code.

## Tests

- **Parser unit tests:** BEL vs ST endings, 2-digit vs 4-digit channels, malformed and partial replies.
- **State-machine tests** with fake events: background reply first, DA1 first, timeout, a change report followed by a new background reply, and the user override suppressing all of it.
- **Frame snapshots** of both palettes and the 16-color default.
- **One manual run** over SSH and one inside GNU Screen or mosh, to confirm the first frame appears immediately.
