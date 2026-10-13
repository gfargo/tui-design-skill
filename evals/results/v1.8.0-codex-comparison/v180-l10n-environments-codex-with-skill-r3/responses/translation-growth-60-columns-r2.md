**Make 60 columns a supported layout before strings arrive.** German and Finnish labels can expand substantially; Japanese exposes errors in character-width handling.

1. **Replace English width constants with cell budgets.** On `tea.WindowSizeMsg`, recompute available space after padding, borders, gaps, and the footer. Use `lipgloss.Width()` for measurement and ANSI-aware, grapheme-safe truncation consistent with your installed Charm stack. Bytes and rune counts cannot measure Japanese, combining marks, or emoji correctly.

2. **Give the four columns priorities and a fallback.**

   | Size | Recommended behavior |
   |---|---|
   | 80×24 | Show all four columns only when their minimum useful widths fit; give task titles the remaining space. |
   | 60 columns | Keep task title and essential status; move the other two fields into an Enter-to-open detail view. |
   | Below that | Use a single task list with full-screen details and a clear back action. |
   | Below tested minimum width/height | Show a localized “terminal too small” message naming the requirement; preserve quit and resize recovery. |

   Preserve selection across layout changes. Truncate table cells instead of wrapping rows; show full values in details. Shorten or truncate headers before sacrificing useful data width.

3. **Make the footer adaptive.** Generate hints from the same Bubbles `key.Binding` definitions used for input, with localized help descriptions. Show 3–5 contextual actions when they fit; at 60 columns prioritize opening details, the main task action, and `?` help. Drop whole lower-priority hints rather than clipping key/action pairs. Keep full help scrollable and budget its height separately.

4. **Prepare the translation contract.** Extract complete messages with named placeholders and plural support; avoid assembling sentences from translated fragments. Give translators context and optional short-label variants for headers and hints. Keep key tokens separate from descriptions and bindings stable unless deliberately redesigned. Use fixed-width ISO dates in the table and localized formats in details.

5. **Run a clutter audit.** The supplied description doesn’t establish current border or marker counts. Measure border depth, signals per state, markers repeated on every row, and the share of cells used by chrome. Remove nested table/panel borders, decorative row bullets, repeated field labels, and redundant status cues if present. Those cells matter at 60 columns.

6. **Test now with a pseudo-locale.** Expand every UI string by about 50% and surround it with markers to expose hardcoded text and clipping. Stress very short labels at 2–3× English length too. Add Japanese-width fixtures, combining characters, and emoji. Test ambiguous-width punctuation and borders with the terminal’s ambiguous-wide setting, and provide an ASCII chrome option.

Before handing off strings, require rendered-frame tests at **80×24, 60×24, and the declared minimum**, including help, details, errors, empty states, and resizing between layouts. Assert that every line fits, keys remain discoverable, and hidden or truncated values remain accessible.