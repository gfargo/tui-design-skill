Yes—35 actions across several screens is enough to justify a command palette, especially for less frequent actions and commands whose shortcuts users may forget. Keep common actions visible; the palette supplements them.

Make **`/` search the logs in the current view**. That’s a familiar convention in terminal tools and fits the main task of a log viewer.

A clear split:

| Key | Behavior |
|---|---|
| `/` | Search log content in the current view |
| `n` / `N` | Jump to the next / previous match |
| `Ctrl+K` | Open the command palette |
| `Esc` | Close the active input or overlay |

Keep **search and filtering distinct**: search highlights matches while preserving surrounding context; filtering hides nonmatching entries. Offer “Filter logs…” through a visible control and the palette.

For the palette:

- Include all available actions, grouped or ranked by relevance to the current screen.
- Show each action’s keyboard shortcut.
- Use concrete names such as “Pause live updates” and “Copy selected log line.”
- Explain disabled actions when their absence would be confusing.
- Ignore global shortcuts while the user is typing in an input.

If you already use `Ctrl+K` for something important, choose another palette shortcut. The key decision is to give `/` one predictable meaning: **find text in the logs you’re looking at**.