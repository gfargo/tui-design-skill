Look in [references/visual-patterns.md](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/eloquent-ritchie-f2f1c8/plugins/tui-design/skills/tui-design/references/visual-patterns.md), which owns all these rules:

| Concern | Section |
|---|---|
| Spinner behavior | **Progress indicators → Spinners** |
| Status messages | **Status bars, headers, footers** |
| Emoji alignment | **Tables and lists → Emoji and aligned columns** |
| CJK and ambiguous widths | **Localization** |
| Disabling animation | **Accessibility → Motion** |

The rules to apply:

- **Measure terminal cells**, not bytes, code points, or string length. Use a grapheme-aware width library for measuring, padding, and truncating; test CJK, combining marks, and emoji.
- **Emoji widths vary.** Wide-base emoji such as `✅ ❌ ⭐` occupy two cells. Narrow-base sequences such as `⚠️`, `✔️`, `❤️`, and ZWJ families can disagree between terminals and libraries. Prefer `✓ ✗ !` or words for status columns.
- **Check ambiguous-width settings.** Borders, arrows, dots, and ellipses can become double-width. Test with ambiguous-wide enabled and provide an ASCII override.
- **Truncate table cells; don’t wrap.** Budget the truncation marker’s actual width. Left-align text and statuses; right-align numbers.
- **Delay spinners 100–200 ms.** Braille frames at roughly 80 ms are the default. On completion, replace with success/failure or remove. Suppress animation on non-TTY; in plain, screen-reader, or reduced-motion mode, print `Working...` once, then the final status.
- **Keep status feedback readable.** Success/info may clear after 3–5 seconds; warnings/errors stay until dismissed. Preserve messages in a reopenable log, and express meaning with words or symbols alongside color.

For verification, render the troublesome strings at **80×24 and 60 columns**, hide low-priority columns as needed, and expose full values through row details. Also remove redundant status markers—for example, `Error:` already supplies the label without another icon.