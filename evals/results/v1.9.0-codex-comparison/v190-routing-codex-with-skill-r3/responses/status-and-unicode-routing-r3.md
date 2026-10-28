Look in [references/visual-patterns.md](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/eloquent-ritchie-f2f1c8/plugins/tui-design/skills/tui-design/references/visual-patterns.md). It owns both issues.

| Concern | Sections |
|---|---|
| Status-bar spinner | **Status bars, headers, footers**, **Progress indicators**, **States**, **Accessibility → Motion** |
| Misaligned emoji/CJK | **Tables and lists → Emoji and aligned columns**, **Localization → Ambiguous-width characters** |

The rules:

- **Spinner:** small background work can use a status-line spinner and message. Initial loading belongs in the content area; during refresh, keep existing rows visible. Delay animation ~100–200 ms; Braille frames at ~80 ms are the default. Stop on completion, showing `✓`, `✗`, or clearing it.
- **Motion and output:** suppress spinners on non-TTY output. In plain, screen-reader, or reduced-motion mode, print `Working...` once, then the final status.
- **Status messages:** success/info fade after 3–5 seconds. Errors/warnings stay until dismissed; retain messages in a reopenable log. Preserve meaning without color.
- **Width:** measure **terminal cells**, using grapheme-aware width handling—not bytes, code points, or string length. Use the same width policy for padding and truncation; test CJK, combining marks, and emoji.
- **Emoji:** prefer `✓ ✗ !` or words in status columns. Wide-base emoji such as `✅ ❌ ⭐` are safer than variation-selector/joiner sequences such as `⚠️`, `❤️`, or families, whose measured width can differ across terminals.
- **Ambiguous glyphs:** borders, blocks, `…`, and many arrows can become two cells. Test the terminal’s ambiguous-wide setting and offer ASCII fallbacks.
- **Tables:** left-align text/status, right-align numbers, and truncate cells rather than wrapping. Reserve the measured width of the truncation marker.

Verify at **80×24 and 60 columns**: hide low-priority columns, retain full values in a detail view, and keep essential status visible. For clutter, remove redundant status signals and markers repeated on every row.