**Main fix:** stop clearing and repainting the whole screen. Send only the cells that changed, write each frame in one `write`, and wrap each frame in synchronized output (mode 2026) when the terminal supports it.

## Why it's worse in tmux

When you clear the screen and repaint it, the terminal can show the half-drawn frame for a moment. Inside tmux there's an extra layer: tmux reads what your app writes into its own copy of the screen, then redraws that onto your real terminal. So the blank or half-drawn screen reaches your terminal and shows up as flicker. The tmux version matters too: synchronized output only passes through tmux 3.7 and later. On older versions you're relying entirely on writing less.

## What to change, most important first

1. **Remove the clear-and-redraw.** Look for `clear()`, `\x1b[2J`, `ClearScreen`, or "clear then print everything" on each update. Build the next frame in memory, compare it with the previous one, and write only the cells that differ. Clear the screen only when you have a real reason: the first draw, returning from `$EDITOR` or a suspend, or a resize.
2. **Send each frame in one write.** Collect all the output in a buffer and flush it once. Many small writes give tmux more chances to redraw partway through a frame.
3. **Wrap each frame in synchronized output** when the terminal reports it:
   ```
   CSI ? 2026 h    …frame bytes…    CSI ? 2026 l
   ```
   You can check for support with `CSI ? 2026 $ p`. kitty, WezTerm, foot, Alacritty, Ghostty, iTerm2, Windows Terminal 1.23+ and tmux 3.7+ support it. **Always send the end sequence, including on error paths.** Otherwise the screen stays frozen until the terminal's own timeout, which can be up to 2 seconds.
4. **Hide the cursor while drawing.** Show it again afterwards on the focused row or field, so screen-reader and keyboard users can still find it.
5. **Draw only when something changes:** input, new data, a resize, or a timer that actually changes what's visible. Don't redraw on a fixed loop. If updates come in bursts (log tailing, streaming tokens), cap them at about 30 fps or debounce them.

## If you use a framework, it probably does this already

The full-screen redraw usually means something is working against the framework's own diffing:

- **Ratatui:** `draw()` already sends only changed cells. Remove any `terminal.clear()` in your loop; keep it only for resume and resize. Ratatui doesn't turn on synchronized output, so wrap each `draw()` in crossterm's `BeginSynchronizedUpdate` / `EndSynchronizedUpdate` yourself. Also draw only after an event or a timer that changed visible state.
- **Bubble Tea v2:** it compares your `View()` output with the last frame and turns on synchronized output when the terminal supports it. Flicker usually comes from printing to stdout outside `View()` or from sending `ClearScreen` too often.
- **Ink:** use 6.7+ (which has synchronized updates), set `incrementalRendering: true` (Ink 8), lower `maxFps`, and put append-only logs in `<Static>`.
- **Textual:** it diffs and synchronizes already, so look for something writing to the terminal directly.
- **Hand-written ANSI:** steps 1–4 are your job. Keep a front buffer and a back buffer and compare them cell by cell.

## Checking it

- Run `tmux -V`. Below 3.7 there's no synchronized output, so steps 1–2 have to fix it alone. Upgrading tmux helps.
- Record how many bytes your app writes per update. After the fix, moving the selection one row should write a few dozen bytes, not a full screen's worth.
- Make sure nothing else writes to stdout while the UI is running, such as logs or `print` debugging. Send it to a file instead.

If you tell me the language or framework, or share the render loop, I can point to the exact line that's causing the full redraw.
