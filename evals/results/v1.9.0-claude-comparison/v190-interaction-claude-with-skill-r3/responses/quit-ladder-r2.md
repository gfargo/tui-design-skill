Rule of thumb: **Esc steps back and never quits. `q` steps back and quits only at the root. `Ctrl+C` cancels running work first, then quits from anywhere.** Each Esc press does the innermost step that applies, does it once, and stops.

## Esc: one step per press, never quits

| Order | When it applies | What Esc does |
|---|---|---|
| 1. Cancel | A request, load, or long action is running | Cancel it and keep the old data on screen |
| 2. Close | A modal, menu, palette, help screen or completion popup is open | Close the **top** one only |
| 3. Clear | A filter, search or multi-selection is active | Clear it. A cancelled search goes back to where the cursor was before |
| 4. Go back | A drill-down, detail view or focus trap is open | Go back **one** level |
| 5. Root | None of the above | **Nothing.** Esc never quits |

Those are probably your five jobs. Right now they likely have no defined order. With this table, any press has exactly one result. For example, in a detail view with a filter on and help open, Esc closes help, then clears the filter, then goes back.

## `q`: back out, quit only at the root

- In a nested view, `q` goes back one level. It should not quit from anywhere, which is your current problem. Quitting from deep inside the app is the worst case when there's unsaved work.
- At the root, `q` quits.
- While a text field has focus, `q` is just a letter.
- In a single-view app, `q` quits directly.

## `Ctrl+C`: the emergency exit

- If something is running, the first press cancels it.
- If nothing is running, it quits from anywhere. It doesn't step back through the levels.
- If quitting would lose something, the first press shows a status-line message (`Press Ctrl+C again to quit`). A second press within about 2 seconds quits.
- Don't take `Ctrl+C` for another action. If you have to, provide another obvious way to quit.

## Quit rules for all three keys

- **Confirm only when quitting loses something**: unsaved edits, or running work that can't resume. Example: `Quit? 2 jobs are still running [y/N]`, defaulting to No. If nothing would be lost, quit without asking.
- **Every way of quitting runs the same teardown**: the confirmed `q`, the second `Ctrl+C`, errors and panics. Each one must restore raw mode, the cursor, mouse capture and the screen buffer.
- **Esc can arrive late.** tmux holds a lone Esc for `escape-time` (500 ms before 3.5, 10 ms since) to tell it apart from an Alt sequence. Don't put anything time-critical on Esc, and test inside tmux.

## Implementation

Use one function that walks the steps from the top and returns after the first one that applies. Esc and `q` both call it. They differ only at the root: Esc does nothing there, and `q` quits (with a confirmation if something would be lost). Handle `Ctrl+C` in a separate branch above the steps: cancel if something is running, otherwise quit. Because the decision lives in your state logic, you can unit-test the order without a terminal: build a state with a popup open, a filter active and two levels of drill-down, send Esc several times, and check each step.

Update your footer and `?` help to match. At the root, show `q quit`. In a nested view, show `esc/q back`.

If you tell me the framework (Bubble Tea, Ratatui, Textual, Ink…), I can sketch the handler in its native style.
