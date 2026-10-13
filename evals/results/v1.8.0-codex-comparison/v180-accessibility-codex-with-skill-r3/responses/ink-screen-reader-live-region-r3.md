**Change the output model, not just the flag.** Ink 8’s screen-reader mode removes borders and color and honors accessibility labels, but it still erases and rewrites the **whole live region whenever it changes**. NVDA’s terminal diffing—and Windows Terminal’s reporting of written text—can treat that output as new text. A spinner tick or streamed token can therefore trigger another reading of the conversation.

`INK_SCREEN_READER=true` enables this renderer; it doesn’t detect NVDA or make output append-only.

What to change:

- **Move completed messages into `<Static>`.** Append each finalized message once, with stable identity and a speaker label such as `Assistant:`. Don’t put a message there until it is finished; Static items aren’t updated afterward.
- **Stop animation at its source.** In screen-reader mode, don’t mount the spinner or run its timer. Use `Working…` once, then a completion, cancellation, or error message. Hiding the spinner with `aria-hidden` alone doesn’t eliminate render churn.
- **Buffer streamed responses.** Announce a completed answer once, or append meaningful sentence-sized chunks once. Rewriting a growing answer on every token recreates the problem.
- **Keep the live region small.** Limit it to the current input and essential state. `useIsScreenReaderEnabled()` lets components choose this behavior.
- **Offer a linear `--no-tui` mode.** Keep output in scrollback, avoid the alternate screen and cursor-driven repainting, and use ordinary prompts or numbered choices. Preserve every chat action in this mode.

Use `aria-label` for useful descriptions and `aria-hidden` for decoration, but neither supplies browser-style live-region announcement control. Lower `maxFps`, memoization, and incremental rendering may improve visual performance; they don’t fix whole-region rewriting in screen-reader mode.

For the accessibility layout, remove borders, repeated headers, row glyphs, and duplicate status indicators; retain speaker labels and one textual status. At **80×24 and 60 columns**, use a single wrapping transcript and prompt with no sidebar.

Verify the **actual terminal writes**, not just rendered-frame snapshots: completed messages should appear once, waiting should produce no spinner ticks, and responses should not replay history. Then test with NVDA in the users’ terminal, including typing, streaming, cancellation, and errors.