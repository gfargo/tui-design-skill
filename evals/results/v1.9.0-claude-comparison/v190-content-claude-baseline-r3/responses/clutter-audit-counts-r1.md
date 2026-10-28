The working directory is empty, so I can't see your code. Here's how I'd fix it based on your description. There are two problems: each row says the same thing more than once, and you have more borders than you need.

## 1. Show each piece of information once

`> [PASS] (ok) build 2.1s` has four markers before the name, and `[PASS]` and `(ok)` mean the same thing. Use one status glyph and let color do the rest:

```
› ✓ build        2.1s
  ✓ lint         0.8s
  ✗ test        14.3s
  ◌ deploy          –
```

- **Status:** a single glyph (`✓ ✗ ◌ ⊘`) in green, red, dim or yellow. Drop the brackets and the word. If the output has to work without color (piped output or `NO_COLOR`), the glyph shapes still tell the states apart.
- **Cursor:** keep `›` or `>` but give it a fixed 2-character gutter so rows don't shift. Or drop it and highlight the selected row with reverse video or a subtle background color, which is usually cleaner.
- **Duration:** right-align it in its own column and dim it. Aligned numbers are much easier to scan than ones that follow names of different lengths.
- **Name:** this is what people read, so give it the default foreground color and let everything else be quieter than it.

## 2. Use one border at most

Two nested boxes use 4 columns and 4 rows on box-drawing characters that tell the user nothing. Options, from cleanest to least clean:

- **No border.** Use a bold or dim header line (`Tests  3/4 passed`) and blank lines for spacing. Whitespace groups things well enough.
- **One border** around the list, with the title in the top edge: `╭─ Tests ──────╮`.
- If the outer box exists only to frame the whole app, remove it and keep the inner one. If you have several panels, a single rule (`│` or `─`) between them is enough.

## 3. Optional polish

- Put a summary in the header or footer (`3 passed · 1 failed · 17.2s`) so people don't have to count rows.
- Dim the passing rows a little and keep failures at full brightness so problems stand out.
- If the list gets long, sort failures to the top or offer a filter.

If you share the rendering code (Ink, Bubble Tea, Ratatui, Textual, etc.), I can show you the exact changes.
