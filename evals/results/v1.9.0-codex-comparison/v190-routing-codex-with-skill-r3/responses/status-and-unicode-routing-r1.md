Look in the skill’s [references/visual-patterns.md](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/eloquent-ritchie-f2f1c8/plugins/tui-design/skills/tui-design/references/visual-patterns.md). It owns all these rules:

| Section | Rules |
|---|---|
| **Status bars, headers, footers** | Success/info fades after **3–5 seconds**. Errors/warnings stay until dismissed. Keep messages in a reopenable log. Use a label or symbol so meaning survives `NO_COLOR`. |
| **Progress indicators → Spinners** | Prefer Braille frames, roughly **80 ms/frame**. Delay display **100–200 ms** to avoid flashing. Stop on completion with a final result or remove it. Suppress on non-TTY; use a static `Working...` line and final status in plain, screen-reader, or reduced-motion modes. |
| **Tables and lists → Emoji and aligned columns** | Measure **terminal cells**, never bytes, code points, or string length. Use grapheme-aware width measurement for padding and truncation. Prefer `✓ ✗ !` or words for status columns. |
| **Localization → Ambiguous-width characters** | Terminal settings and width libraries can disagree. Test ambiguous-wide mode; offer ASCII fallbacks for borders, bars, and markers. |

For your misalignment specifically:

- **CJK characters commonly occupy two cells.** Combining marks and emoji sequences make character counts unsuitable for alignment.
- **Emoji width varies:** narrow-base sequences such as `⚠️`, `❤️`, and ZWJ families may occupy one or two cells depending on the terminal/library. Wide-base emoji such as `✅ ❌ ⭐` are safer, but still test supported terminals.
- **Truncate by display width without splitting grapheme clusters.** Dense table cells should not wrap; expose full values in a detail view.
- Test CJK, combining marks, and emoji at **80×24 and 60 columns**. Drop low-priority columns as space shrinks and keep essential status visible.

For clutter, keep one clear status label and at most one reinforcing color cue; remove redundant emoji, labels, and markers that appear on every row.