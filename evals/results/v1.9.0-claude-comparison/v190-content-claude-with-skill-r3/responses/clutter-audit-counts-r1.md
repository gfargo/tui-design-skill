**Remove the inner box and both the `>` and `(ok)` markers, and replace the brackets with a plain status column.** The busy feeling comes from three specific things, and each one can be counted.

## Clutter audit

| Measure | Now | Why it's noise |
|---|---|---|
| Border depth | **2** (box inside a box) | The inner border sits inside the outer one, so it separates nothing and shows no focus. The terminal edge already frames the app. |
| Signals per status | **3** (`[PASS]` + `(ok)` + green) | The limit is one color cue plus one non-color cue. `(ok)` repeats what `[PASS]` already says. |
| Always-on markers | `>` on **every** row | A glyph on 100% of rows doesn't mark anything. |
| Chrome vs. data | about **84%** of non-blank cells are borders, brackets and markers | That high share is what "busy" means here. |

## Before → after

```
+--------------------------------------+
| +----------------------------------+ |
| | > [PASS] (ok)  build        2.1s | |
| | > [PASS] (ok)  lint         0.8s | |
| | > [FAIL] (!!)  test         4.5s | |
| +----------------------------------+ |
+--------------------------------------+
```

```
 Task    Status  Time
 build   PASS    2.1s
 lint    PASS    0.8s
 test    FAIL    4.5s      ← FAIL in red; selected row in reverse video
```

The specific changes:

1. **Delete the inner border.** Keep one border only if the list shares the screen with other panes and needs a boundary or a focus cue. If the list fills the screen, delete the outer border too.
2. **Drop `(ok)` and `(!!)`.** Show status as the bare word `PASS` or `FAIL`. Leave passes in the default text color, or dim them, and color only `FAIL` in red. Failures then stand out because they're the only colored rows. The word still carries the meaning without color, so it works with `NO_COLOR` and for colorblind users.
3. **Drop the `>` prefix.** Mark the selected row with reverse video only.
4. **Add a dim header row** (`Task  Status  Time`) instead of brackets. Left-align the text columns and right-align the times so the decimal points line up.
5. **Use whitespace for grouping.** If you have phases, such as build steps and then tests, put a blank row between them rather than a box around each.

## At smaller sizes

- **80×24:** the table fits easily with room left over. This is a good point to add a detail pane (failure output for the selected test) to the right, with one border between the two panes.
- **60-column tmux split:** use a single pane. `Status` and `Time` keep fixed widths, and `Task` gets the rest of the width and cuts off long names with `…` instead of wrapping. Pressing Enter opens the failure output full-width, and Esc returns to the list.
- **Below about 30 columns:** show a clear "terminal too small, need 30 columns" message rather than garbled rows.

If you tell me which framework you're using (Bubble Tea/Lipgloss, Ratatui, Textual, Ink), I can show the exact table and style code.
