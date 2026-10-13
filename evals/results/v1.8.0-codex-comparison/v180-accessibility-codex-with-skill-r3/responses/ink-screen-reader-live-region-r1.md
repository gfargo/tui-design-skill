**The flag changes Ink’s rendering format; it doesn’t prevent repeated announcements.** In Ink 8, screen reader mode removes borders and color and honors accessibility labels, but **still erases and rewrites the entire live region whenever its output changes**. NVDA and the terminal can treat that rewritten text as new output.

If your conversation lives in the live region, each streamed token or spinner frame can cause the history to be announced again. Even a small animated child keeps that region updating.

Change the output architecture:

- **Move completed messages into `<Static>`**, with stable keys and speaker labels such as `User:` and `Assistant:`. Only append finalized messages; `<Static>` is unsuitable for text you still edit.
- **Stop animation at its source in screen reader mode.** Use `useIsScreenReaderEnabled()` to select a static `Working…` component instead of mounting the spinner. Disable elapsed-time ticks too. `aria-hidden` alone doesn’t stop animation updates.
- **Buffer streamed responses**, then append the completed response once. If incremental speech is necessary, emit completed chunks once rather than repeatedly rewriting the growing response.
- **Keep the live area small:** the current prompt and essential controls. Print meaningful status transitions once, including completion, cancellation, and actionable errors.
- **Offer a linear `--no-tui` mode** with ordinary scrollback, no alternate screen, labelled output, and numbered or typed choices. Preserve access to every chat action.

Adding more `aria-label`s, lowering `maxFps`, or enabling incremental rendering won’t fix the underlying announcement pattern.

Verify with **NVDA in the actual Windows terminal your users run**: send multiple messages, wait through a long response, cancel, and trigger an error. Completed history should be spoken once, with no spinner chatter. At 80×24 and 60 columns, the accessible layout should remain one linear flow without repeated headers, borders, or status boilerplate.

These recommendations follow the supplied [tui-design skill](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/amazing-meitner-d3ddd1/plugins/tui-design/skills/tui-design/SKILL.md) and its Ink and accessibility references.