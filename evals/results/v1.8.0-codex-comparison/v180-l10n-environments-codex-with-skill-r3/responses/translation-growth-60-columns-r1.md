**Make the layout responsive and test expanded strings now.** German and Finnish labels can grow substantially; Japanese requires correct terminal-cell measurement even when strings contain fewer characters.

Using the [tui-design skill](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/amazing-meitner-d3ddd1/plugins/tui-design/skills/tui-design/SKILL.md), I’d change these before translation:

1. **Replace English-based width constants with a width budget.** Handle `tea.WindowSizeMsg`; subtract padding, separators, borders, and footer height before allocating columns. Measure rendered strings with `lipgloss.Width()`, never byte length or rune count. Use ANSI-aware, grapheme-safe truncation and reserve the measured width of the truncation marker.

2. **Define what survives narrowing.**

   | Size | Behavior |
   |---|---|
   | 80×24 | Four columns when their minimum widths fit; task title gets remaining space. Drop the lowest-priority column when expanded labels make that necessary. |
   | 60 columns | One primary task list, retaining title and essential status. Move other fields into an Enter-to-open detail view; Esc returns to the same selection. |
   | Below tested minimum | Show a compact “terminal too small” message with the actual required dimensions, while retaining quit behavior. |

   Keep table rows single-line. Truncate headers before sacrificing useful task data; expose full labels and values in help/details. Derive the minimum from usable content rather than declaring 80 columns mandatory.

3. **Make the footer prioritize complete hints.** At 60 columns, keep open, help, and quit discoverable; move secondary actions into `?` help. Measure whole `key + action` groups and omit lower-priority groups instead of cutting their descriptions midway. Generate hints from the same Bubbles `key.Binding` definitions used for dispatch. Translate action descriptions separately from key tokens.

4. **Give translators context and variants.** Extract complete messages with placeholders and plural handling. Provide translator notes describing each action, plus separate short and full labels where needed. Don’t impose English character limits or require translators to invent abbreviations to rescue the layout.

5. **Test before real strings arrive.** Add a marked pseudo-locale with roughly 50% expansion, plus stress cases at 2–3× English length for short headers and hints. Golden-test 80×24, 60 columns, and the proposed minimum. Include Japanese, combining marks, emoji, long task titles, and resizing while selected. Check Japanese terminal settings where ambiguous characters—borders, arrows, `·`, and `…`—render wide; provide ASCII alternatives.

**Also reclaim wasted cells.** Without a rendered frame, actual clutter counts remain unknown. Audit border depth, duplicate status signals, markers on every row, and chrome-to-data share. Remove any outer frame around an already-bordered table, decorative per-row markers, and redundant status badges; use modest whitespace between columns. Those cells are valuable translation space.