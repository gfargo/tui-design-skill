**Change the output architecture, not just the flag.** `INK_SCREEN_READER=true` enables Ink’s accessibility renderer, but **it still erases and rewrites the entire live region on every change**. NVDA can interpret those writes as new text. If conversation history sits in that region, spinner ticks, streamed tokens, and input updates can trigger repeated announcements.

Ink’s renderer removes borders and color and supports `aria-label`/`aria-hidden`; it doesn’t provide browser-style announcement isolation. `useIsScreenReaderEnabled()` reports the opt-in flag—it doesn’t detect NVDA.

What to change:

- **Move completed messages into `<Static>`.** Append each message once with a stable ID. Keep streaming drafts out of `<Static>` because already-rendered items won’t update.
- **Unmount animated spinners in screen-reader mode.** Replace them with a one-time “Assistant: Working…” line and a completion/error message. Stop their timers too; hiding or labelling a ticking spinner doesn’t eliminate rendering churn.
- **Avoid repainting an expanding streamed answer.** Buffer until completion, or append immutable sentence-sized chunks. Lower FPS and debounce can reduce noise, but don’t fix repeated history.
- **Keep the live area small:** the current input and essential controls. Use speaker prefixes, concise instructions, and a real terminal cursor on the input.
- **Provide a linear `--no-tui` mode:** normal scrollback, no alternate screen, append-only output, numbered choices, and access to every chat action. Results belong on stdout; prompts/progress on stderr. Make the preference persistent.

For the accessibility layout, remove borders, spinner glyphs, repeated headings, and redundant status markers. At **80×24 and 60 columns**, use one wrapping column without side panels or width truncation that loses message content.

Validate with **NVDA in the Windows terminal your users use**: idle waiting should produce no repeated announcements; typing should not replay history; each completed answer should appear once. Frame snapshots alone can’t verify speech behavior.

These recommendations follow the skill’s [Ink guidance](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/amazing-meitner-d3ddd1/plugins/tui-design/skills/tui-design/references/ecosystem-typescript.md) and [accessibility guidance](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/amazing-meitner-d3ddd1/plugins/tui-design/skills/tui-design/references/visual-patterns.md:671).