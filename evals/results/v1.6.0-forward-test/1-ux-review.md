I wouldn’t release without responsive behavior; wide monitors do not cover tmux splits, SSH sessions, embedded terminals, or font zoom.

Priority changes:

1. **Add explicit breakpoints.**

   - `>120 cols`: keep all three panes; give Resources the most width.
   - `80–120`: Resources wins. Move namespace into the header/picker and open YAML with `Enter`; `Esc` returns.
   - `60–79`: single-pane drill-down: Namespaces → Resources → YAML, with a breadcrumb.
   - Below a tested minimum such as `48×12`: show `terminal too small — need 48×12`.

   Drop low-priority columns before truncating names; never wrap table rows.

2. **Remove the outer double frame.** The content currently has border depth 2: terminal edge → outer frame → pane border. Use single-line pane borders or shared separators, with an accent-colored border and bold title only on the focused pane.

3. **Simplify resource rows.** Readiness is encoded three times—green, `[READY]`, and `✓`—while the bullet appears on every row and therefore marks nothing. Remove the bullets and render one aligned status column: `Ready`, optionally green. Reserve symbols for exceptions or selection.

4. **Replace the two-row, 18-shortcut footer.** Show only 3–5 actions relevant to the focused pane plus `? Help`. Put all 18 bindings in a categorized help view. One contextual footer row should be enough.

5. **Make focus unmistakable.** Use reverse video for the selected row, accent border/title for the focused pane, `Tab`/`Shift+Tab` for focus, `Enter` to drill in, and `Esc` to return.

Before release, snapshot-test `140`, `120`, `80×24`, `60` columns, and the hard minimum. Also verify resize handling, loading/empty/error/disconnected states, `NO_COLOR`, ASCII fallbacks, wide-character truncation, terminal restoration on every exit path, and a plain `--no-tui` mode.
