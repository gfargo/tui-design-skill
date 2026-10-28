Look in two places: **the status bar’s animation lifecycle** and **the table’s display-width calculations**. The workspace is empty, so I can’t name specific files.

For the spinner:

- Animate only while work is active; stop its timer when work finishes or the component unmounts.
- Use frames with equal terminal-cell widths so adjacent text doesn’t jump.
- Reserve space for the spinner and use the normal render loop; direct terminal writes can corrupt layout.
- Provide a static status when animation is disabled.

For emoji and CJK alignment:

- Measure **terminal cells**, not bytes, string length, or Unicode code points.
- CJK characters typically occupy two cells. Combining marks occupy zero additional cells; emoji sequences require grapheme-aware handling.
- Use your TUI framework’s width, padding, wrapping, and truncation helpers consistently. ANSI styling sequences must contribute zero width.
- Truncate at grapheme boundaries and account for the ellipsis’s width.
- Test emoji with variation selectors, skin tones, and joined sequences, plus mixed Latin/CJK text. Terminal emoji widths can vary, so allow an ASCII fallback where exact alignment matters.

Useful search terms in your repo: `spinner`, `tick`, `interval`, `status`, `column`, `padding`, `truncate`, `wcwidth`, `stringWidth`, and `display_width`.