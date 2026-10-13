Make the layout responsive and Unicode-aware before translation starts. English at 80 columns should be one layout case, not the sizing rule.

- **Budget terminal cells, not bytes or characters.** Japanese characters often occupy two cells; combining marks may occupy none. Use a terminal-aware width and truncation library compatible with your Bubble Tea/Lip Gloss stack that also handles ANSI styling. Avoid `len()` and rune-count padding.
- **Define a compact layout for 60 columns.** Give essential columns priority, let the task title take remaining space, and hide or move secondary fields to a detail view. Account for borders, padding, and column gaps. Below a useful table width, switch to a list or stacked rows.
- **Handle resizing dynamically.** Recalculate widths on `tea.WindowSizeMsg`, including when tmux panes resize. Size the footer and table independently.
- **Redesign the key-hint footer.** Show a few essential actions and a localized “Help” hint; put the full key map in an expandable help view. Allow hints to wrap or switch to a compact form without clipping key bindings.
- **Separate bindings from translated labels.** Keep actual keys supplied by the application and interpolate them into messages. Don’t translate shortcut letters accidentally. If you want locale-specific shortcuts, make that a deliberate feature with conflict checks.
- **Give translators context and flexible messages.** Use complete messages with named placeholders, locale-aware plural rules, and separate short labels where compact wording is necessary. Document where each string appears and whether it can wrap or truncate. Avoid concatenated sentence fragments and fixed character limits.

Before strings arrive, test with expanded pseudo-translations, Japanese wide characters, combining marks, and long unbroken task titles at **60 and 80 columns**, plus live resizing. Check that selection remains clear, essential actions stay discoverable, and no row or footer exceeds the available terminal width.

German and Finnish need room for longer words; Japanese needs correct cell measurement. Truncation helps individual fields, but layout changes are what make the 60-column experience usable.