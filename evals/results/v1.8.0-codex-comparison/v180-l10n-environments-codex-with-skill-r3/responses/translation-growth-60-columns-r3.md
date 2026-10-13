Change the layout contract before handing strings to translators: **60 columns must be a supported layout, and translated labels must never determine whether the app remains usable.**

1. **Replace fixed English column widths with a width budget.** Measure rendered terminal cells with `lipgloss.Width()`, not bytes or rune counts. Subtract padding, separators, borders, and sort indicators first; give the task title the remaining space. Cap header widths so long German or Finnish labels cannot squeeze out task data. Truncate labels before sacrificing useful data, with full labels available in help.

2. **Define a responsive fallback now.**

   | Size | Behavior |
   |---|---|
   | Wide | All four columns when their useful minimum widths fit |
   | 80×24 | Four columns only if they fit; otherwise drop the lowest-priority column |
   | 60 columns | One primary task list, keeping title and essential status; secondary fields available through Enter |
   | Below a tested minimum | A clear “terminal too small” message naming the required dimensions |

   Rank your actual four columns by importance. Keep selection, filtering, and sorting intact through resize. Handle `tea.WindowSizeMsg` and recompute both table geometry and footer height.

3. **Make key hints responsive as complete units.** Keep a small contextual set of essential actions plus a visible `?` help hint. Drop lower-priority hints or deliberately use another line; never clip a key away from its description. Generate hints from the same Bubbles `key.Binding` definitions used for input, using `ShortHelp()` and `FullHelp()`. Translate descriptions separately from physical key bindings.

4. **Fix Unicode width and truncation.** Use ANSI-aware, grapheme-safe truncation and measure the truncation marker too. Japanese characters commonly occupy two cells; combining marks and emoji need cluster-aware handling. Test ambiguous-width settings: arrows, box drawing, `…`, and `·` can change width. Provide ASCII borders and markers, and avoid assuming that a Japanese locale means the terminal renders ambiguous characters wide.

5. **Prepare the translation catalog for context.** Externalize headers, hints, errors, empty states, and help. Give translators complete messages, named placeholders, plural handling, and notes explaining each action. Offer separate compact and full labels where useful—don’t require translators to fit English character limits. Keep table dates compact and predictable, such as ISO dates; localize richer dates and numbers in details.

6. **Test before translations arrive.** Add a marked pseudo-locale with roughly 50% expansion, plus harsher expansion for short headers and hints. Golden-test frames at 80×24, 60 columns, the declared minimum, and just below it. Include Japanese text, decomposed accents, emoji, long task names, and live resizing in tmux. Assert that every rendered line fits and every hidden field remains reachable.

Also reclaim wasted cells: remove any redundant outer frame or nested table border, avoid markers repeated on every row, and count padding/separator cells against the width budget. Without a screenshot, the current clutter count is unknown; those are concrete things to audit before allocating space to translations.