The row has the same information in it three times, and the double border boxes it in again. Most of the fix is removing repetition.

## 1. Show each piece of status once

`[PASS]`, `(ok)` and (most likely) the color all say the same thing. Pick one glyph and let color support it:

```
› ✓ build        2.1s
  ✓ lint         0.4s
  ✗ unit-tests   5.8s
  ● e2e          …
  ○ deploy
```

- **One status glyph**: `✓` pass, `✗` fail, `●`/spinner running, `○` pending, `–` skipped. Color it green/red/yellow/dim. The glyph alone is still readable without color, so you don't need both a word and a symbol.
- **Drop `(ok)`.** If it's meant to show something different from PASS, like a cached result, show it only when it applies, e.g. a dim `cached` after the duration.

## 2. Make the cursor quieter

`>` takes up a column and pulls the eye on every row. Two options:
- Keep a narrow `›` and also apply **reverse video or a subtle background** to the selected row, or
- Remove the marker and use only the highlight.

Either way, the unselected rows get blank space where the marker would be, so all the names stay lined up.

## 3. Align the columns

Pad names to a fixed width and right-align durations. Aligned columns make the list easy to scan without any borders. Dim the durations so the names stand out.

## 4. Remove one border, maybe both

You rarely need two boxes. Options, from lightest to heaviest:
- **No inner box.** Put a header line above the list, e.g. `Tests  4/5 passed` in bold, plus a blank line or a dim `─` rule.
- Keep **one** outer border for the whole app frame and separate regions with space.
- If you're using a panel framework (Ink `<Box borderStyle>`, Ratatui `Block`, Textual, Bubble Tea/lipgloss), remove the border from the inner component and put its title in the outer box's title slot.

## 5. Put the summary in one place

Rather than marking every row as passing, show a single summary (`✓ 4 passed  ✗ 1 failed  12.3s`) in the header or footer. Then the rows mostly matter when they've failed. You could even dim passing rows and leave failures at full brightness.

## Before and after

```
┌──────────────────────────┐        Tests  ✓ 4  ✗ 1   12.3s
│ ┌──────────────────────┐ │
│ │> [PASS] (ok) build 2.1s│ │  →   › ✓ build        2.1s
│ │  [PASS] (ok) lint 0.4s │ │        ✓ lint         0.4s
│ │  [FAIL] (err) unit 5.8s│ │        ✗ unit-tests   5.8s
│ └──────────────────────┘ │
└──────────────────────────┘
```

If you tell me which library you're using (Ink, Ratatui, Bubble Tea, Textual, etc.), or share the file, I can make these changes in your code. I didn't find any source files in the current directory.
